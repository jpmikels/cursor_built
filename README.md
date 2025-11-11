# Valuation Workbench (VWB)

GCP-native web application for financial statement consolidation, validation, and business valuation.

## Overview

VWB ingests financial statements (PDF + XLSX), consolidates them into formula-rich Excel workbooks, validates data integrity, and generates comprehensive valuation outputs using DCF, Guideline Public Company, and Guideline Transaction methodologies.

## Architecture

### Tech Stack
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Backend**: Python 3.11 FastAPI on Cloud Run
- **Data**: BigQuery (analytics), Cloud SQL Postgres (metadata), Cloud Storage (artifacts)
- **AI/ML**: Document AI (parsing), Vertex AI Gemini 1.5 (mapping & validation)
- **Orchestration**: Pub/Sub, Cloud Tasks, Workflows
- **IaC**: Terraform
- **CI/CD**: GitHub → Cloud Build → Cloud Run

### Key Features
- Multi-tenant architecture with row-level security
- Automated document parsing and chart-of-accounts mapping
- Financial statement normalization and reconciliation
- Rule-based + AI-powered validation
- Formula-rich Excel workbook generation
- Multiple valuation methodologies with pluggable market data providers
- Complete audit trail and compliance logging

## Repository Structure

```
/vwb
  /infra                 # Terraform IaC
  /app
    /frontend            # Next.js application
    /backend             # FastAPI services
      /api               # API routes
      /services          # Business logic
      /parsers           # Document extraction
      /normalization     # COA mapping & normalization
      /validation        # Rule engine & AI validation
      /valuation         # DCF, GPCM, GTM engines
      /workbook          # Excel generation
      /providers         # Market data integrations
      /auth              # Authentication & authorization
      /schemas           # Pydantic models & COA definitions
      /jobs              # Background job handlers
    /common              # Shared utilities
  /samples               # Sample financial statements
  /tests                 # Unit & E2E tests
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Terraform 1.5+
- GCP Account with billing enabled
- GitHub repository (for CI/CD)

### Local Development

#### Backend
```bash
cd app/backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### Frontend
```bash
cd app/frontend
npm install
npm run dev
```

#### Database Migrations
```bash
cd app/backend
alembic upgrade head
```

### GCP Deployment

#### 1. Set Up Environment Variables
```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
export ENVIRONMENT="dev"  # dev, staging, prod
export GITHUB_REPO="your-org/vwb"
```

#### 2. Enable Required APIs
```bash
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
  artifactregistry.googleapis.com
```

#### 3. Deploy Infrastructure
```bash
cd infra
terraform init
terraform plan -var="project_id=$GCP_PROJECT_ID" -var="environment=$ENVIRONMENT"
terraform apply -var="project_id=$GCP_PROJECT_ID" -var="environment=$ENVIRONMENT"
```

#### 4. Configure Secrets
```bash
# Database password
echo -n "your-db-password" | gcloud secrets create vwb-db-password --data-file=-

# JWT secret
echo -n "$(openssl rand -hex 32)" | gcloud secrets create vwb-jwt-secret --data-file=-

# Optional: Market data provider API keys
echo -n "your-api-key" | gcloud secrets create vwb-pitchbook-key --data-file=-
```

#### 5. Set Up GitHub Actions (Workload Identity Federation)
The Terraform configuration automatically sets up Workload Identity Federation for GitHub Actions.

Add these secrets to your GitHub repository:
- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_WIF_PROVIDER`: Output from Terraform
- `GCP_WIF_SERVICE_ACCOUNT`: Output from Terraform

#### 6. Push to GitHub to Trigger CI/CD
```bash
git push origin main
```

## Configuration

### Environment Variables

**Backend** (`app/backend/.env`):
```env
PROJECT_ID=your-project-id
ENVIRONMENT=dev
DATABASE_URL=postgresql://user:pass@host/db
JWT_SECRET_KEY=your-secret-key
VERTEX_AI_LOCATION=us-central1
DOCUMENT_AI_PROCESSOR_ID=your-processor-id
UPLOADS_BUCKET=your-project-dev-vwb-uploads
ARTIFACTS_BUCKET=your-project-dev-vwb-artifacts
```

**Frontend** (`app/frontend/.env.local`):
```env
NEXT_PUBLIC_API_URL=https://your-backend-url.run.app
NEXT_PUBLIC_ENVIRONMENT=dev
```

### Terraform Variables

See `infra/variables.tf` for full list. Key variables:
- `project_id`: GCP project ID
- `environment`: Deployment environment
- `region`: Primary GCP region
- `db_tier`: Cloud SQL instance tier
- `github_repo`: GitHub repository for CI/CD

## API Documentation

Once deployed, access interactive API docs at:
- Swagger UI: `https://your-backend-url.run.app/docs`
- ReDoc: `https://your-backend-url.run.app/redoc`

### Key Endpoints

**Engagements**
- `POST /api/v1/engagements` - Create new engagement
- `GET /api/v1/engagements/{id}` - Get engagement details
- `POST /api/v1/engagements/{id}/upload` - Get signed upload URL
- `POST /api/v1/engagements/{id}/ingest` - Start ingestion workflow

**Validation**
- `GET /api/v1/engagements/{id}/validation` - List validation issues
- `POST /api/v1/engagements/{id}/validation/accept` - Accept AI suggestions
- `POST /api/v1/engagements/{id}/validation/override` - Override with manual fix

**Valuation**
- `POST /api/v1/engagements/{id}/valuation/run` - Execute valuation
- `GET /api/v1/engagements/{id}/valuation/result` - Get valuation results

**Artifacts**
- `GET /api/v1/engagements/{id}/artifacts/workbook.xlsx` - Download consolidated workbook
- `GET /api/v1/engagements/{id}/artifacts/summary.pdf` - Download valuation summary

## Adding a Market Data Provider

1. Create new provider in `app/backend/providers/market/`:

```python
from .base import MarketDataProvider

class MyProvider(MarketDataProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_comparable_companies(self, criteria: dict) -> list:
        # Implementation
        pass
```

2. Register in `app/backend/providers/market/__init__.py`
3. Add credentials to Secret Manager
4. Update configuration in database

## Chart of Accounts (COA)

The canonical COA is defined in `app/backend/schemas/coa_canonical.csv` with ~150 standard line items covering:
- Income Statement (Revenue → Net Income)
- Balance Sheet (Assets = Liabilities + Equity)
- Cash Flow Statement (Operating, Investing, Financing)

AI mapping uses this canonical set plus aliases for flexible source document handling.

## Data Flow

1. **Upload** → Raw files to GCS, job record in Cloud SQL
2. **Parse** → Document AI/Excel extraction → BigQuery staging
3. **Map** → Vertex AI maps source labels to canonical COA
4. **Normalize** → Build standardized periodic tables
5. **Validate** → Rule engine + AI suggestions → User review
6. **Consolidate** → Generate formula-rich Excel workbook
7. **Valuate** → Run DCF/GPCM/GTM → Store results → Generate PDF
8. **Download** → Signed URLs for artifacts

## Security

- **Authentication**: JWT with bcrypt password hashing
- **Authorization**: RBAC (Admin, Analyst, Viewer roles)
- **Multi-tenancy**: Row-level security across all data stores
- **Secrets**: All credentials in Secret Manager, never in code
- **Network**: VPC egress controls, private Cloud SQL
- **Audit**: Complete trail of all actions and data changes
- **Compliance**: Ready for SOC 2 / ISO 27001 controls

## Testing

```bash
# Backend unit tests
cd app/backend
pytest tests/ -v --cov=. --cov-report=html

# Frontend tests
cd app/frontend
npm test

# E2E tests
cd tests/e2e
npm install
npx playwright test
```

## Monitoring & Observability

- **Logging**: Structured JSON logs with trace IDs
- **Metrics**: Cloud Monitoring dashboards (automatically provisioned)
- **Alerting**: Error rate, latency, and availability policies
- **Tracing**: OpenTelemetry distributed traces
- **Health Checks**: `/health` and `/ready` endpoints

## Cost Optimization

- Cloud Run scales to zero when idle
- BigQuery clustering and partitioning by tenant + date
- GCS lifecycle policies for old artifacts
- Cloud SQL automated backups with retention policies
- Budget alerts configured in Terraform

## Troubleshooting

### Common Issues

**Build fails with "permission denied"**
- Ensure service accounts have required IAM roles
- Check Cloud Build service account permissions

**Document AI parsing errors**
- Verify processor ID is correct for your region
- Check document size limits (50MB for PDFs)

**Database connection fails**
- Confirm Cloud SQL proxy is running for local dev
- Verify VPC connector for Cloud Run

**Validation suggestions not appearing**
- Check Vertex AI API is enabled
- Verify service account has `aiplatform.user` role

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and add tests
3. Run linters: `black .`, `isort .`, `flake8 .`
4. Commit: `git commit -am 'Add feature'`
5. Push: `git push origin feature/my-feature`
6. Create Pull Request

## License

Proprietary - All Rights Reserved

## Support

For issues and questions:
- Create GitHub issue
- Contact: support@valuationworkbench.example.com
