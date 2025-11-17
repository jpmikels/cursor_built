# Valuation Workbench - Complete Setup Guide

This guide walks you through setting up the complete Valuation Workbench from scratch.

## 🎯 What You're Building

An AI-powered business valuation platform that reduces valuation time from 20-40 hours to 2-4 hours (80%+ time savings).

### Key Capabilities
- Intelligent PDF/Excel extraction (Document AI + Gemini)
- Auto-mapping to chart of accounts (AI-powered)
- Formula-rich Excel workbook generation (20+ tabs)
- Multi-method valuation (DCF, GPCM, GTM)
- Conversational AI interface
- Professional audit-grade PDF reports
- Real-time collaboration

## 📋 Customization Questions

Before starting, answer these questions:

1. **GCP Project ID**: `_____________`
2. **GitHub Repository**: `owner/repo-name`
3. **GCP Region**: `us-central1` (recommended) or: `_______`
4. **Industry Focus** (select 1-3):
   - [ ] Manufacturing
   - [ ] SaaS/Technology
   - [ ] Professional Services
   - [ ] Healthcare
   - [ ] Retail
   - [ ] Other: `_______`
5. **Data Providers** (check what you have):
   - [ ] None (use free sources only)
   - [ ] Bloomberg
   - [ ] S&P Capital IQ
   - [ ] PitchBook
   - [ ] DealStats
6. **Budget**: `$______/month` for GCP + data
7. **Alert Email**: `_____________`

## 🚀 Step-by-Step Setup

### Phase 1: Prerequisites (15 minutes)

#### 1.1. Install Required Tools

**macOS:**
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install tools
brew install google-cloud-sdk terraform docker node python@3.11
```

**Linux:**
```bash
# Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Terraform
wget https://releases.hashicorp.com/terraform/1.5.0/terraform_1.5.0_linux_amd64.zip
unzip terraform_1.5.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Python
sudo apt-get install python3.11 python3.11-venv
```

**Windows (WSL2 recommended):**
```powershell
# Install WSL2
wsl --install

# Then follow Linux instructions in WSL2
```

#### 1.2. Verify Installations

```bash
gcloud version
terraform version
docker version
node --version
python3 --version
```

### Phase 2: GCP Project Setup (10 minutes)

#### 2.1. Create GCP Project

```bash
export PROJECT_ID="your-project-id"  # Use your answer from above
export REGION="us-central1"
export ALERT_EMAIL="your-email@example.com"

# Create project
gcloud projects create $PROJECT_ID --name="Valuation Workbench"

# Set as default
gcloud config set project $PROJECT_ID

# Enable billing (must be done via console)
echo "⚠️  Enable billing at: https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
read -p "Press enter once billing is enabled..."
```

#### 2.2. Authenticate

```bash
# Login
gcloud auth login

# Application default credentials
gcloud auth application-default login
```

### Phase 3: Infrastructure Deployment (30 minutes)

#### 3.1. Create Terraform State Bucket

```bash
export TF_STATE_BUCKET="${PROJECT_ID}-terraform-state"

gsutil mb -p $PROJECT_ID -l $REGION gs://$TF_STATE_BUCKET
gsutil versioning set on gs://$TF_STATE_BUCKET
```

#### 3.2. Configure Terraform Variables

Create `infra/terraform.tfvars`:

```bash
cat > infra/terraform.tfvars <<EOF
project_id    = "$PROJECT_ID"
region        = "$REGION"
environment   = "dev"
github_repo   = "your-org/vwb"  # Update this
alert_email   = "$ALERT_EMAIL"

# Adjust based on your budget
db_tier                  = "db-f1-micro"
backend_max_instances    = 10
frontend_max_instances   = 5
uploads_retention_days   = 2555
artifacts_retention_days = 365
EOF
```

#### 3.3. Deploy Infrastructure

```bash
cd infra

# Initialize
terraform init -backend-config="bucket=${TF_STATE_BUCKET}"

# Plan (review changes)
terraform plan -var-file="terraform.tfvars"

# Apply
terraform apply -var-file="terraform.tfvars" -auto-approve

# Save outputs
terraform output > ../infra-outputs.txt
```

**Expected outcome:** 
- ✅ Cloud Run services created (will show errors - expected)
- ✅ Database provisioned
- ✅ Storage buckets created
- ✅ BigQuery datasets created
- ✅ Networking configured
- ✅ IAM roles assigned

### Phase 4: Document AI Setup (10 minutes)

#### 4.1. Create Document AI Processor

```bash
# Enable Document AI API (if not done by Terraform)
gcloud services enable documentai.googleapis.com

# Create processor
gcloud alpha documentai processors create \
  --display-name="VWB Financial Extractor" \
  --type=FORM_PARSER_PROCESSOR \
  --location=us \
  --project=$PROJECT_ID

# Get processor ID
export PROCESSOR_ID=$(gcloud alpha documentai processors list \
  --location=us \
  --project=$PROJECT_ID \
  --format="value(name)" | head -1 | cut -d'/' -f6)

echo "Document AI Processor ID: $PROCESSOR_ID"
echo "Save this: $PROCESSOR_ID"
```

#### 4.2. Update Backend Configuration

Add to your backend `.env`:
```
DOCUMENT_AI_PROCESSOR_ID=$PROCESSOR_ID
```

### Phase 5: Local Development Setup (20 minutes)

#### 5.1. Clone and Setup Repository

```bash
cd ~
git clone https://github.com/your-org/vwb.git
cd vwb
```

#### 5.2. Create Local Environment Files

**Backend `.env`:**
```bash
cat > app/backend/.env <<EOF
# Application
APP_NAME=Valuation Workbench
ENVIRONMENT=dev
DEBUG=true
LOG_LEVEL=INFO

# GCP
PROJECT_ID=$PROJECT_ID
REGION=$REGION

# Database (will use docker-compose postgres)
DATABASE_URL=postgresql://vwb:vwb_dev_password@localhost:5432/vwb_dev
DB_ECHO=false

# JWT
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Storage (from Terraform outputs)
UPLOADS_BUCKET=$(grep uploads_bucket ../infra-outputs.txt | cut -d'=' -f2 | tr -d ' "')
ARTIFACTS_BUCKET=$(grep artifacts_bucket ../infra-outputs.txt | cut -d'=' -f2 | tr -d ' "')

# BigQuery
BQ_DATASET_RAW=vwb_raw_dev
BQ_DATASET_CURATED=vwb_curated_dev
BQ_DATASET_VALUATION=vwb_valuation_dev

# Document AI
DOCUMENT_AI_PROCESSOR_ID=$PROCESSOR_ID
DOCUMENT_AI_LOCATION=us

# Vertex AI
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-1.5-flash

# Pub/Sub & Tasks
PUBSUB_TOPIC_INGESTION=vwb-ingestion-dev
PUBSUB_TOPIC_VALIDATION=vwb-validation-dev
CLOUD_TASKS_QUEUE=vwb-tasks-dev
CLOUD_TASKS_LOCATION=us-central1

# CORS
CORS_ORIGINS=http://localhost:3000
EOF
```

**Frontend `.env.local`:**
```bash
cat > app/frontend/.env.local <<EOF
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_ENVIRONMENT=dev
EOF
```

#### 5.3. Start Services with Docker Compose

```bash
# Create secrets directory
mkdir -p secrets

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### 5.4. Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create admin user
docker-compose exec backend python -c "
from models import User
from database import SessionLocal
from passlib.hash import bcrypt

db = SessionLocal()
try:
    admin = User(
        email='admin@example.com',
        hashed_password=bcrypt.hash('admin123'),
        is_admin=True,
        full_name='Admin User'
    )
    db.add(admin)
    db.commit()
    print('✅ Admin user created: admin@example.com / admin123')
except Exception as e:
    print(f'⚠️  User might already exist: {e}')
finally:
    db.close()
"
```

### Phase 6: Verify Local Installation (5 minutes)

#### 6.1. Test Backend

```bash
# Health check
curl http://localhost:8080/health

# API docs
open http://localhost:8080/docs  # or visit in browser
```

#### 6.2. Test Frontend

```bash
# Open frontend
open http://localhost:3000

# Login with: admin@example.com / admin123
```

#### 6.3. Test Database

```bash
# Access PgAdmin
open http://localhost:5050

# Login: admin@vwb.local / admin
# Add server:
#   Host: postgres
#   Port: 5432
#   Username: vwb
#   Password: vwb_dev_password
```

### Phase 7: Deploy to GCP (20 minutes)

#### 7.1. Build and Push Images

```bash
export REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/dev-vwb-docker"

# Authenticate Docker
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build and push backend
docker build -t ${REGISTRY}/backend:latest app/backend
docker push ${REGISTRY}/backend:latest

# Build and push frontend
docker build -t ${REGISTRY}/frontend:latest \
  --build-arg NEXT_PUBLIC_API_URL=https://dev-vwb-backend-${REGION}.run.app \
  app/frontend
docker push ${REGISTRY}/frontend:latest
```

#### 7.2. Deploy to Cloud Run

```bash
# Get database connection
DB_CONNECTION=$(terraform output -raw -state=infra/terraform.tfstate db_connection_name)

# Deploy backend
gcloud run deploy dev-vwb-backend \
  --image=${REGISTRY}/backend:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --add-cloudsql-instances=$DB_CONNECTION \
  --set-env-vars="ENVIRONMENT=dev,PROJECT_ID=$PROJECT_ID" \
  --min-instances=0 \
  --max-instances=10 \
  --memory=2Gi \
  --cpu=2

# Get backend URL
BACKEND_URL=$(gcloud run services describe dev-vwb-backend \
  --region=$REGION \
  --format="value(status.url)")

# Deploy frontend
gcloud run deploy dev-vwb-frontend \
  --image=${REGISTRY}/frontend:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars="NEXT_PUBLIC_API_URL=$BACKEND_URL" \
  --min-instances=0 \
  --max-instances=5 \
  --memory=512Mi \
  --cpu=1

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe dev-vwb-frontend \
  --region=$REGION \
  --format="value(status.url)")

echo "✅ Deployment complete!"
echo "Backend:  $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"
```

### Phase 8: Setup CI/CD (15 minutes)

#### 8.1. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and add:

```bash
# Get Workload Identity values from Terraform
cd infra
WIF_PROVIDER=$(terraform output -raw workload_identity_provider)
WIF_SA=$(terraform output -raw workload_identity_sa)

echo "Add these to GitHub Secrets:"
echo "GCP_PROJECT_ID: $PROJECT_ID"
echo "WIF_PROVIDER: $WIF_PROVIDER"
echo "WIF_SERVICE_ACCOUNT: $WIF_SA"
```

In GitHub:
1. Go to repository Settings
2. Secrets and variables → Actions
3. Add new repository secrets:
   - `GCP_PROJECT_ID`
   - `WIF_PROVIDER`
   - `WIF_SERVICE_ACCOUNT`
   - `STAGING_DATABASE_URL` (from terraform outputs)
   - `STAGING_API_URL` ($BACKEND_URL)

#### 8.2. Test CI/CD

```bash
# Create test branch
git checkout -b test-ci

# Make small change
echo "# Test" >> README.md

# Commit and push
git add README.md
git commit -m "Test CI/CD"
git push origin test-ci

# Create PR and watch GitHub Actions run
```

### Phase 9: Post-Deployment Configuration (10 minutes)

#### 9.1. Run Production Migrations

```bash
# Install Cloud SQL Proxy
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy

# Start proxy
./cloud_sql_proxy -instances=$DB_CONNECTION=tcp:5432 &

# Run migrations
cd app/backend
export DATABASE_URL="postgresql://vwb_app:PASSWORD@localhost:5432/vwb"
alembic upgrade head

# Stop proxy
killall cloud_sql_proxy
```

#### 9.2. Create Production Admin User

```bash
# Use Cloud Run console or Cloud Shell
gcloud run services proxy dev-vwb-backend --region=$REGION &

# Then connect and create user (similar to local)
```

#### 9.3. Configure Monitoring

```bash
# View logs
gcloud run services logs read dev-vwb-backend --region=$REGION

# View metrics in console
echo "Metrics: https://console.cloud.google.com/run/detail/$REGION/dev-vwb-backend/metrics?project=$PROJECT_ID"
```

## ✅ Verification Checklist

- [ ] Local backend running (http://localhost:8080/health)
- [ ] Local frontend running (http://localhost:3000)
- [ ] Can login with admin@example.com
- [ ] Can create engagement
- [ ] Cloud Run backend deployed
- [ ] Cloud Run frontend deployed
- [ ] GitHub Actions CI passing
- [ ] Database migrations completed
- [ ] Document AI processor created
- [ ] Monitoring alerts configured

## 🎓 Next Steps

1. **Create Sample Engagement**
   - Upload sample financial statements
   - Test document extraction
   - Review AI mappings
   - Generate workbook

2. **Customize for Your Industry**
   - Update canonical COA in `app/backend/schemas/coa_canonical.csv`
   - Add industry-specific validation rules
   - Configure market data providers

3. **Train Your Team**
   - Share user guide
   - Run demo sessions
   - Create example engagements

4. **Production Readiness**
   - Set up production environment
   - Configure custom domain
   - Enable additional security features
   - Set up backup/DR procedures

## 🆘 Troubleshooting

### Common Issues

**Docker containers won't start:**
```bash
docker-compose down -v
docker-compose up -d --build
```

**GCP authentication issues:**
```bash
gcloud auth application-default revoke
gcloud auth application-default login
```

**Terraform state issues:**
```bash
terraform state pull > backup.tfstate
terraform force-unlock LOCK_ID
```

**Database connection issues:**
```bash
# Check if postgres is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres
```

## 💰 Cost Estimates

### Development Environment
- Cloud Run: $5-20/month (mostly free tier)
- Cloud SQL: $10-15/month (db-f1-micro)
- Storage + BigQuery: $1-5/month
- Document AI: $1.50 per 1000 pages
- **Total: ~$20-50/month**

### Production Environment
- Cloud Run: $50-200/month
- Cloud SQL: $120-180/month (db-n1-standard-2)
- Other services: $50-100/month
- **Total: ~$220-480/month**

## 📞 Support

- Documentation: Check `ARCHITECTURE.md`, `DEPLOYMENT.md`
- Issues: GitHub Issues
- Email: support@yourcompany.com

---

**Congratulations! 🎉 Your Valuation Workbench is now set up and ready to use.**
