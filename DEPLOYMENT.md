# Valuation Workbench - Deployment Guide

## Overview

This guide walks through deploying the complete Valuation Workbench (VWB) application to Google Cloud Platform.

## Prerequisites

1. **GCP Account**: Active billing account with sufficient quota
2. **CLI Tools**:
   ```bash
   # Google Cloud SDK
   gcloud components update
   
   # Terraform
   brew install terraform  # macOS
   # or download from terraform.io
   
   # Node.js & npm
   node --version  # Should be 18+
   npm --version
   
   # Python
   python --version  # Should be 3.11+
   ```

3. **Permissions**: Owner or Editor role on GCP project

## Step 1: GCP Project Setup

```bash
# Set variables
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export ENVIRONMENT="dev"

# Set active project
gcloud config set project $PROJECT_ID

# Enable required APIs (this may take a few minutes)
gcloud services enable \
  cloudresourcemanager.googleapis.com \
  serviceusage.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  bigquery.googleapis.com \
  storage.googleapis.com \
  pubsub.googleapis.com \
  secretmanager.googleapis.com \
  documentai.googleapis.com \
  aiplatform.googleapis.com \
  workflows.googleapis.com \
  cloudtasks.googleapis.com \
  artifactregistry.googleapis.com \
  vpcaccess.googleapis.com \
  compute.googleapis.com
```

## Step 2: Create Terraform State Bucket

```bash
# Create GCS bucket for Terraform state
gsutil mb -p $PROJECT_ID -l $REGION gs://${PROJECT_ID}-terraform-state

# Enable versioning
gsutil versioning set on gs://${PROJECT_ID}-terraform-state
```

## Step 3: Configure Document AI

```bash
# Create Document AI processor
gcloud alpha documentai processors create \
  --location=us \
  --display-name="VWB Form Parser" \
  --type=FORM_PARSER_PROCESSOR

# Note the processor ID for terraform variables
```

## Step 4: Deploy Infrastructure with Terraform

```bash
cd infra

# Copy and edit terraform variables
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values:
# - project_id
# - github_repo
# - alert_email
# - document_ai_processor_id (from step 3)

# Initialize Terraform
terraform init -backend-config="bucket=${PROJECT_ID}-terraform-state"

# Review plan
terraform plan -var="project_id=$PROJECT_ID"

# Apply infrastructure
terraform apply -var="project_id=$PROJECT_ID"

# Save outputs
terraform output > ../terraform-outputs.txt
```

This will provision:
- Cloud Storage buckets
- BigQuery datasets
- Cloud SQL PostgreSQL instance
- Cloud Run services (placeholders)
- Pub/Sub topics
- Cloud Tasks queues
- Secret Manager secrets
- VPC & connector
- Artifact Registry
- IAM service accounts
- Monitoring & alerting
- Workload Identity Federation for GitHub

## Step 5: Configure Secrets

```bash
# Get the Cloud SQL password from Terraform
DB_PASSWORD=$(terraform output -raw db_password 2>/dev/null || echo "CHANGE_ME")

# JWT secret is auto-generated, but you can rotate it
JWT_SECRET=$(openssl rand -hex 32)
echo -n "$JWT_SECRET" | gcloud secrets versions add vwb-jwt-secret --data-file=-

# Add market data provider API keys (optional)
# echo -n "YOUR_PITCHBOOK_KEY" | gcloud secrets create vwb-pitchbook-key --data-file=-
# echo -n "YOUR_CAPIQ_KEY" | gcloud secrets create vwb-capiq-key --data-file=-
```

## Step 6: Set Up GitHub CI/CD

### 6.1 Get Workload Identity Federation info

```bash
# From Terraform outputs
WIF_PROVIDER=$(terraform output -raw workload_identity_provider)
WIF_SA=$(terraform output -raw cloudbuild_service_account)

echo "Add these to GitHub repository secrets:"
echo "GCP_PROJECT_ID: $PROJECT_ID"
echo "GCP_WIF_PROVIDER: $WIF_PROVIDER"
echo "GCP_WIF_SERVICE_ACCOUNT: $WIF_SA"
```

### 6.2 Add secrets to GitHub

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Add the three secrets above

## Step 7: Initial Build & Deploy

### Option A: Deploy via GitHub (Recommended)

```bash
# Push code to GitHub
git init
git add .
git commit -m "Initial VWB deployment"
git remote add origin https://github.com/YOUR_ORG/vwb.git
git push -u origin main

# Cloud Build trigger will automatically build and deploy
```

### Option B: Manual Deploy (for testing)

```bash
# Build backend
cd app/backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/vwb-backend

# Deploy backend
BACKEND_SERVICE=$(terraform output -raw backend_service_name)
gcloud run deploy $BACKEND_SERVICE \
  --image gcr.io/$PROJECT_ID/vwb-backend \
  --region $REGION \
  --platform managed

# Build frontend
cd ../frontend
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format='value(status.url)')
gcloud builds submit --tag gcr.io/$PROJECT_ID/vwb-frontend \
  --build-arg NEXT_PUBLIC_API_URL=$BACKEND_URL

# Deploy frontend
FRONTEND_SERVICE=$(terraform output -raw frontend_service_name)
gcloud run deploy $FRONTEND_SERVICE \
  --image gcr.io/$PROJECT_ID/vwb-frontend \
  --region $REGION \
  --platform managed
```

## Step 8: Run Database Migrations

```bash
cd app/backend

# Install Cloud SQL Proxy
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy

# Get connection name
CONNECTION_NAME=$(terraform output -raw db_connection_name)

# Start proxy in background
./cloud_sql_proxy -instances=$CONNECTION_NAME=tcp:5432 &
PROXY_PID=$!

# Set database URL
export DATABASE_URL="postgresql://vwb_app:$DB_PASSWORD@localhost:5432/vwb"

# Run migrations
alembic upgrade head

# Stop proxy
kill $PROXY_PID
```

## Step 9: Verify Deployment

```bash
# Get service URLs
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format='value(status.url)')
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE --region $REGION --format='value(status.url)')

echo "Backend: $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"

# Test backend health
curl $BACKEND_URL/health

# Test frontend
curl $FRONTEND_URL

# Access application
open $FRONTEND_URL
```

## Step 10: Post-Deployment Configuration

### Create First User

1. Navigate to frontend URL
2. Click "Get Started" or "Register"
3. Fill in:
   - Email
   - Password
   - Full Name
   - Organization Name
4. Sign in

### Set Up Document AI Custom Processor (Optional)

For better parsing accuracy, train a custom Document AI processor:

1. Go to Document AI Console
2. Create Custom Extractor
3. Upload sample financial statements
4. Label entities (Revenue, COGS, etc.)
5. Train model
6. Update processor ID in environment

### Configure Market Data Providers (Optional)

1. Obtain API credentials from:
   - PitchBook
   - Capital IQ
   - DealStats
   
2. Add to Secret Manager:
   ```bash
   echo -n "YOUR_KEY" | gcloud secrets create vwb-provider-key --data-file=-
   ```

3. Update provider configuration in database

## Monitoring & Operations

### View Logs

```bash
# Backend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$BACKEND_SERVICE" --limit 50

# Frontend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$FRONTEND_SERVICE" --limit 50

# Error logs only
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit 50
```

### Monitor Application

```bash
# Open Cloud Console
open "https://console.cloud.google.com/monitoring/dashboards?project=$PROJECT_ID"

# View Cloud Run metrics
open "https://console.cloud.google.com/run?project=$PROJECT_ID"
```

### Scale Services

```bash
# Increase max instances
gcloud run services update $BACKEND_SERVICE \
  --region $REGION \
  --max-instances 20

# Set minimum instances (reduce cold starts)
gcloud run services update $BACKEND_SERVICE \
  --region $REGION \
  --min-instances 1
```

## Cost Optimization

### Development Environment

```bash
# Use smaller database tier
terraform apply -var="db_tier=db-f1-micro"

# Reduce min instances to 0
gcloud run services update $BACKEND_SERVICE --min-instances 0
```

### Production Environment

- Enable BigQuery partitioning and clustering
- Set GCS lifecycle policies
- Use committed use discounts for Cloud SQL
- Configure budget alerts

## Troubleshooting

### Build Failures

```bash
# Check Cloud Build logs
gcloud builds list --limit=5

# View specific build
BUILD_ID=$(gcloud builds list --limit=1 --format='value(id)')
gcloud builds log $BUILD_ID
```

### Database Connection Issues

```bash
# Verify VPC connector
gcloud compute networks vpc-access connectors describe vwb-vpc-cx \
  --region $REGION

# Test database connectivity
gcloud sql connect vwb-db --user=vwb_app
```

### Authentication Errors

```bash
# Verify service account permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*vwb*"
```

### Document AI Errors

```bash
# Check processor status
gcloud alpha documentai processors list --location=us

# Verify API is enabled
gcloud services list --enabled | grep documentai
```

## Security Hardening (Production)

1. **Enable Cloud Armor**: DDoS protection
2. **Set up Cloud IAP**: Identity-Aware Proxy for admin access
3. **Configure VPC Service Controls**: Perimeter security
4. **Enable Binary Authorization**: Ensure only verified images deploy
5. **Set up SOC 2 compliance**: Audit logging, access controls
6. **Regular vulnerability scanning**: Container Analysis

## Backup & Disaster Recovery

### Database Backups

```bash
# Backups are automatic, but you can create manual backup
gcloud sql backups create --instance=vwb-db

# List backups
gcloud sql backups list --instance=vwb-db
```

### GCS Bucket Versioning

Versioning is enabled by Terraform. To restore a file:

```bash
gsutil ls -a gs://YOUR_BUCKET/path/to/file
gsutil cp gs://YOUR_BUCKET/path/to/file#GENERATION ./restored_file
```

## Cleanup

To destroy all resources:

```bash
cd infra
terraform destroy -var="project_id=$PROJECT_ID"

# Delete state bucket
gsutil rm -r gs://${PROJECT_ID}-terraform-state
```

## Support

- Documentation: `/README.md`
- API Docs: `https://YOUR_BACKEND_URL/docs`
- Issues: GitHub Issues
- Email: support@valuationworkbench.example.com

