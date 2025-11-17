# Valuation Workbench - Deployment Guide

This guide covers deploying the Valuation Workbench (VWB) to Google Cloud Platform.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Infrastructure Setup](#infrastructure-setup)
- [Environment Configuration](#environment-configuration)
- [Deployment](#deployment)
- [Post-Deployment](#post-deployment)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

1. **Google Cloud SDK**
   ```bash
   # Install gcloud CLI
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   gcloud init
   ```

2. **Terraform** (>= 1.5)
   ```bash
   # macOS
   brew install terraform
   
   # Linux
   wget https://releases.hashicorp.com/terraform/1.5.0/terraform_1.5.0_linux_amd64.zip
   unzip terraform_1.5.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

3. **Docker**
   ```bash
   # macOS
   brew install docker
   
   # Linux
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```

### GCP Project Setup

1. **Create GCP Project**
   ```bash
   export PROJECT_ID="your-project-id"
   export REGION="us-central1"
   
   gcloud projects create $PROJECT_ID
   gcloud config set project $PROJECT_ID
   ```

2. **Enable Billing**
   - Go to [GCP Console](https://console.cloud.google.com/)
   - Link a billing account to your project

3. **Set Up Authentication**
   ```bash
   gcloud auth application-default login
   ```

## Infrastructure Setup

### 1. Create Terraform State Bucket

```bash
export PROJECT_ID="your-project-id"
export TF_STATE_BUCKET="${PROJECT_ID}-terraform-state"

# Create bucket for Terraform state
gsutil mb -p $PROJECT_ID -l $REGION gs://$TF_STATE_BUCKET

# Enable versioning
gsutil versioning set on gs://$TF_STATE_BUCKET
```

### 2. Configure Terraform Variables

Create `infra/terraform.tfvars`:

```hcl
project_id    = "your-project-id"
region        = "us-central1"
environment   = "dev"  # or "staging" / "prod"
github_repo   = "your-org/your-repo"
alert_email   = "alerts@yourcompany.com"

# Optional customizations
db_tier                  = "db-f1-micro"  # or "db-n1-standard-2" for prod
backend_max_instances    = 10
frontend_max_instances   = 5
uploads_retention_days   = 2555  # 7 years
artifacts_retention_days = 365
```

### 3. Deploy Infrastructure

```bash
cd infra

# Initialize Terraform
terraform init -backend-config="bucket=${TF_STATE_BUCKET}"

# Review changes
terraform plan -var-file="terraform.tfvars"

# Apply changes
terraform apply -var-file="terraform.tfvars"
```

This will create:
- Cloud Run services (backend + frontend)
- Cloud SQL PostgreSQL database
- Cloud Storage buckets (uploads, artifacts)
- BigQuery datasets (raw, curated, valuation)
- Pub/Sub topics for async processing
- Cloud Tasks queues
- VPC and networking
- IAM service accounts and permissions
- Artifact Registry
- Monitoring and alerting

**Note:** First deployment will fail for Cloud Run services because no images exist yet. This is expected.

### 4. Get Infrastructure Outputs

```bash
terraform output

# Save important values
export BACKEND_URL=$(terraform output -raw backend_url)
export FRONTEND_URL=$(terraform output -raw frontend_url)
export DB_CONNECTION=$(terraform output -raw db_connection_name)
```

## Environment Configuration

### 1. Set Up Document AI Processor

```bash
# Create Document AI processor
gcloud alpha documentai processors create \
  --display-name="VWB Financial Extractor" \
  --type=FORM_PARSER_PROCESSOR \
  --location=us

# Get processor ID
PROCESSOR_ID=$(gcloud alpha documentai processors list \
  --location=us \
  --format="value(name)" | head -1)

echo "Document AI Processor ID: $PROCESSOR_ID"
```

### 2. Configure Secrets

Terraform creates empty secrets. Populate them:

```bash
# JWT Secret (already populated by Terraform)

# Database Password (already populated by Terraform)

# Optional: Market data provider API keys
gcloud secrets versions add dev-vwb-pitchbook-key \
  --data-file=- <<< "your-pitchbook-api-key"

gcloud secrets versions add dev-vwb-capiq-key \
  --data-file=- <<< "your-capiq-api-key"
```

## Deployment

### Option 1: GitHub Actions (Recommended)

1. **Configure GitHub Secrets**

   Go to your repository settings → Secrets and add:

   ```
   GCP_PROJECT_ID:          your-project-id
   GCP_PROJECT_ID_PROD:     your-prod-project-id (if different)
   WIF_PROVIDER:            (from Terraform output)
   WIF_SERVICE_ACCOUNT:     (from Terraform output)
   WIF_PROVIDER_PROD:       (from Terraform output for prod)
   WIF_SERVICE_ACCOUNT_PROD:(from Terraform output for prod)
   STAGING_DATABASE_URL:    postgresql://...
   PROD_DATABASE_URL:       postgresql://...
   STAGING_API_URL:         https://...
   PROD_API_URL:            https://...
   SLACK_WEBHOOK:           https://hooks.slack.com/... (optional)
   ```

2. **Deploy to Staging**

   ```bash
   # Push to main branch
   git push origin main
   ```

   GitHub Actions will:
   - Run tests
   - Build Docker images
   - Push to Artifact Registry
   - Deploy to Cloud Run
   - Run smoke tests

3. **Deploy to Production**

   ```bash
   # Create release
   git tag v1.0.0
   git push origin v1.0.0
   ```

   Or use GitHub UI to create a release.

### Option 2: Cloud Build

```bash
# Submit build
gcloud builds submit \
  --config=infra/cloudbuild.yaml \
  --substitutions=_ENVIRONMENT=dev,_REGION=us-central1
```

### Option 3: Manual Deployment

```bash
# Build and push images
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/dev-vwb-docker"

# Backend
docker build -t ${REGISTRY}/backend:latest app/backend
docker push ${REGISTRY}/backend:latest

# Frontend
docker build -t ${REGISTRY}/frontend:latest \
  --build-arg NEXT_PUBLIC_API_URL=${BACKEND_URL} \
  app/frontend
docker push ${REGISTRY}/frontend:latest

# Deploy to Cloud Run
gcloud run deploy dev-vwb-backend \
  --image=${REGISTRY}/backend:latest \
  --region=${REGION} \
  --platform=managed

gcloud run deploy dev-vwb-frontend \
  --image=${REGISTRY}/frontend:latest \
  --region=${REGION} \
  --platform=managed
```

## Post-Deployment

### 1. Run Database Migrations

```bash
# Connect via Cloud SQL Proxy
cloud_sql_proxy -instances=${DB_CONNECTION}=tcp:5432 &

# Run migrations
cd app/backend
export DATABASE_URL="postgresql://vwb_app:PASSWORD@localhost:5432/vwb"
alembic upgrade head
```

### 2. Create Admin User

```bash
# SSH into Cloud Run instance or run locally
python -c "
from app.models import User
from app.database import SessionLocal
from passlib.hash import bcrypt

db = SessionLocal()
admin = User(
    email='admin@yourcompany.com',
    hashed_password=bcrypt.hash('your-secure-password'),
    is_admin=True
)
db.add(admin)
db.commit()
"
```

### 3. Verify Deployment

```bash
# Health checks
curl ${BACKEND_URL}/health
curl ${BACKEND_URL}/ready

# API docs
open ${BACKEND_URL}/docs

# Frontend
open ${FRONTEND_URL}
```

### 4. Set Up Monitoring

- **Cloud Logging**: Logs are automatically sent to Cloud Logging
- **Cloud Monitoring**: Dashboards are automatically created
- **Alerts**: Email alerts configured via Terraform

View in GCP Console:
- [Cloud Run](https://console.cloud.google.com/run)
- [Cloud Logging](https://console.cloud.google.com/logs)
- [Cloud Monitoring](https://console.cloud.google.com/monitoring)

## Scaling Configuration

### Auto-scaling (Cloud Run)

Already configured via Terraform:
- **Dev**: 0-10 instances
- **Staging**: 0-20 instances  
- **Prod**: 1-100 instances (always warm)

### Database Scaling

```bash
# Upgrade database tier
gcloud sql instances patch ${INSTANCE_NAME} \
  --tier=db-n1-standard-4

# Add read replicas (prod only)
gcloud sql instances create ${INSTANCE_NAME}-replica \
  --master-instance-name=${INSTANCE_NAME} \
  --region=${REGION}
```

## Backup & Disaster Recovery

### Database Backups

Automated backups configured via Terraform:
- **Daily backups** at 3 AM
- **7-day** transaction log retention
- **30-day** backup retention

Manual backup:
```bash
gcloud sql backups create \
  --instance=${INSTANCE_NAME} \
  --description="Manual backup $(date +%Y%m%d)"
```

### Restore from Backup

```bash
# List backups
gcloud sql backups list --instance=${INSTANCE_NAME}

# Restore
gcloud sql backups restore BACKUP_ID \
  --backup-instance=${INSTANCE_NAME}
```

## Troubleshooting

### Cloud Run Service Won't Start

```bash
# Check logs
gcloud run services logs read ${SERVICE_NAME} --region=${REGION}

# Check environment variables
gcloud run services describe ${SERVICE_NAME} --region=${REGION}

# Check IAM permissions
gcloud run services get-iam-policy ${SERVICE_NAME} --region=${REGION}
```

### Database Connection Issues

```bash
# Test connection via Cloud SQL Proxy
cloud_sql_proxy -instances=${DB_CONNECTION}=tcp:5432

# Check Cloud SQL logs
gcloud sql operations list --instance=${INSTANCE_NAME}

# Verify VPC connector
gcloud compute networks vpc-access connectors describe \
  ${VPC_CONNECTOR} --region=${REGION}
```

### Document AI Processing Failures

```bash
# Check processor status
gcloud alpha documentai processors list --location=us

# Test processor
gcloud alpha documentai processors process \
  --processor=${PROCESSOR_ID} \
  --location=us \
  --input-document=gs://your-bucket/test.pdf
```

### Performance Issues

```bash
# Check Cloud Run metrics
gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --format="value(status.traffic)"

# Increase resources
gcloud run services update ${SERVICE_NAME} \
  --memory=4Gi \
  --cpu=4 \
  --region=${REGION}

# Check database performance
gcloud sql instances describe ${INSTANCE_NAME}
```

## Security Best Practices

1. **Secrets Management**
   - Never commit secrets to git
   - Use Secret Manager for all sensitive data
   - Rotate secrets regularly

2. **IAM**
   - Use service accounts with minimal permissions
   - Enable Workload Identity for GitHub Actions
   - Review IAM bindings regularly

3. **Network Security**
   - Cloud Run services use HTTPS only
   - Database is private (no public IP)
   - VPC connector for backend-to-database communication

4. **Data Protection**
   - Enable encryption at rest (default)
   - Enable encryption in transit (default)
   - Configure retention policies

5. **Monitoring**
   - Set up alerts for errors and anomalies
   - Monitor costs via billing alerts
   - Review audit logs regularly

## Cost Optimization

### Estimated Monthly Costs (Dev Environment)

- Cloud Run: $5-20 (pay per use)
- Cloud SQL (db-f1-micro): $10-15
- Cloud Storage: $1-5
- BigQuery: $0-10 (mostly free tier)
- Document AI: $1.50 per 1000 pages
- Vertex AI: Pay per use
- **Total: ~$20-60/month**

### Production Environment

- Cloud Run: $50-200
- Cloud SQL (db-n1-standard-2): $120-180
- Other services: $50-100
- **Total: ~$220-480/month**

### Cost Reduction Tips

1. Scale down dev environments outside business hours
2. Use committed use discounts for prod
3. Set budget alerts
4. Clean up old data regularly
5. Use Cloud SQL proxy connection pooling

## Support

- **Documentation**: Check `ARCHITECTURE.md` and `README.md`
- **Issues**: GitHub Issues
- **GCP Support**: [Support Console](https://console.cloud.google.com/support)

## Next Steps

1. ✅ Infrastructure deployed
2. ✅ Application deployed
3. ⬜ Create sample engagements
4. ⬜ Train team on platform
5. ⬜ Set up CI/CD monitoring
6. ⬜ Configure custom domain
7. ⬜ Set up staging environment
8. ⬜ Production readiness review
