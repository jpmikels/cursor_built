# Valuation Workbench - Architecture Documentation

## System Overview

VWB is a cloud-native, production-grade financial statement consolidation and business valuation platform built entirely on Google Cloud Platform.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ HTTPS
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              Cloud Load Balancer (HTTPS)                         │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├──────────────┬─────────────────┐
             │              │                 │
             ▼              ▼                 ▼
      ┌───────────┐  ┌──────────┐    ┌─────────────┐
      │ Frontend  │  │ Backend  │    │   Cloud     │
      │  Cloud    │  │  Cloud   │    │   Storage   │
      │   Run     │  │   Run    │    │  (Uploads)  │
      └───────────┘  └─────┬────┘    └─────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Cloud    │    │ BigQuery │    │  Cloud   │
    │ SQL      │    │ Analytics│    │  Pub/Sub │
    │Postgres  │    │          │    │  Events  │
    └──────────┘    └──────────┘    └─────┬────┘
                                           │
          ┌────────────────────────────────┤
          │                                │
          ▼                                ▼
    ┌──────────┐                    ┌──────────┐
    │Document  │                    │ Vertex   │
    │   AI     │                    │   AI     │
    │ Parsing  │                    │ Gemini   │
    └──────────┘                    └──────────┘
```

## Technology Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State**: Zustand + React Hook Form
- **HTTP**: Axios
- **Deployment**: Cloud Run (containerized)

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.11
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic v2
- **Async**: asyncio + httpx
- **Deployment**: Cloud Run (containerized)

### Data Layer
- **Relational DB**: Cloud SQL PostgreSQL 15
- **Analytics DB**: BigQuery
- **Object Storage**: Cloud Storage
- **Cache**: In-memory (scalable to Memorystore)

### AI/ML
- **Document Parsing**: Document AI (Form Parser)
- **COA Mapping**: Vertex AI (Gemini 1.5 Flash)
- **Validation**: Vertex AI + rule engine

### Infrastructure
- **IaC**: Terraform
- **CI/CD**: Cloud Build + GitHub Actions
- **Container Registry**: Artifact Registry
- **Orchestration**: Cloud Workflows
- **Queue**: Cloud Pub/Sub + Cloud Tasks
- **Secrets**: Secret Manager
- **Monitoring**: Cloud Monitoring + Logging

## Data Flow

### 1. Document Upload Flow

```
User Upload
    ↓
Frontend generates signed URL request
    ↓
Backend creates Document record + generates GCS signed URL
    ↓
Frontend uploads directly to GCS (no backend proxy)
    ↓
Document metadata stored in Cloud SQL
    ↓
User triggers ingestion
    ↓
Backend publishes message to Pub/Sub
```

### 2. Ingestion & Parsing Flow

```
Pub/Sub message received
    ↓
Cloud Run worker picks up message
    ↓
├─ PDF: Document AI parses → extract tables & key-values
└─ Excel: pandas/openpyxl reads → detect structure
    ↓
Raw extraction stored in BigQuery (raw dataset)
    ↓
Vertex AI maps line items to canonical COA
    ↓
Mappings stored in BigQuery with confidence scores
    ↓
Job status updated in Cloud SQL
    ↓
Publish to validation topic
```

### 3. Normalization & Validation Flow

```
Validation message received
    ↓
Normalize financial data:
  - Group by canonical COA codes
  - Calculate subtotals with formulas
  - Build period-over-period tables
    ↓
Store normalized data in BigQuery (curated dataset)
    ↓
Run validation rules:
  - BS equation (Assets = Liab + Equity)
  - IS calculations (Revenue - COGS = GP)
  - CF reconciliation
  - Negative checks, range checks
    ↓
Vertex AI analyzes for missing fields & anomalies
    ↓
Validation issues stored in Cloud SQL
    ↓
User reviews issues in UI
    ↓
User accepts/overrides suggestions
    ↓
Re-run normalization if needed
```

### 4. Workbook Generation Flow

```
User requests consolidated workbook
    ↓
Backend fetches normalized data from BigQuery
    ↓
xlsxwriter generates Excel with:
  - Cover & Assumptions
  - Normalized financial statements
  - Formulas linking cells
  - Named ranges for key inputs
  - Adjustments schedule
  - Forecast model
  - Valuation calculations
  - Audit log
    ↓
Workbook uploaded to GCS (artifacts bucket)
    ↓
Frontend gets signed download URL
    ↓
User downloads workbook
```

### 5. Valuation Flow

```
User configures valuation parameters:
  - WACC inputs (rf, ERP, beta, etc.)
  - DCF: terminal growth or exit multiple
  - GPCM: comparable tickers, multiples
  - GTM: transaction filters, multiples
    ↓
Backend creates ValuationRun record
    ↓
Enqueues task to Cloud Tasks
    ↓
Worker executes valuation:
  ├─ WACC calculation
  ├─ DCF: forecast FCF → PV → terminal value → EV
  ├─ GPCM: fetch comps → calc multiples → apply to subject
  └─ GTM: filter transactions → calc multiples → apply
    ↓
Fetch market data from providers:
  - yfinance for public comps
  - Static Damodaran data for betas/ERPs
  - PitchBook/CapIQ for transactions (if configured)
    ↓
Calculate weighted average conclusion
    ↓
Store results in BigQuery (valuation dataset)
    ↓
Generate valuation summary PDF with WeasyPrint
    ↓
Upload PDF to GCS
    ↓
Update ValuationRun status
    ↓
User views/downloads results
```

## Security Architecture

### Authentication & Authorization
- **User Auth**: JWT tokens (HS256)
- **Token Storage**: localStorage (frontend), httpOnly cookies (production)
- **Password**: bcrypt hashing
- **RBAC**: Admin, Analyst, Viewer roles
- **Multi-tenancy**: Row-level security on all tables

### Network Security
- **Frontend-Backend**: HTTPS only
- **Backend-GCS**: Signed URLs with expiration
- **Backend-DB**: Private IP via VPC connector
- **API Keys**: Secret Manager, never in code/env files
- **Egress**: VPC egress controls for Cloud Run

### Data Security
- **At Rest**: All GCP storage encrypted by default (AES-256)
- **In Transit**: TLS 1.3
- **Secrets**: Secret Manager with IAM-controlled access
- **PII**: No PII expected; redaction if found
- **Audit**: All actions logged to BigQuery

## Scalability

### Compute
- **Cloud Run**: Auto-scales 0 → N instances
- **Backend**: Stateless design, horizontal scaling
- **Frontend**: SSR/SSG where possible, CDN-ready

### Data
- **BigQuery**: Clustered by tenant_id + date, partitioned tables
- **Cloud SQL**: Vertical scaling (CPU/RAM), read replicas for prod
- **GCS**: Unlimited storage, lifecycle policies

### Bottlenecks & Solutions
- **Document AI**: 15 req/min limit → queue with backoff
- **Vertex AI**: Rate limits → caching + batching
- **Database**: Connection pooling (10-20 connections)
- **Cold Starts**: Min instances = 1 for prod backend

## High Availability

### Uptime Targets
- **Frontend**: 99.5% (Cloud Run SLA)
- **Backend**: 99.5% (Cloud Run SLA)
- **Database**: 99.95% (Cloud SQL regional)

### Redundancy
- **Cloud Run**: Multi-zone deployment (automatic)
- **Cloud SQL**: Regional instance with automatic failover
- **GCS**: Multi-regional replication
- **BigQuery**: Multi-regional datasets

### Disaster Recovery
- **Database**: Automated daily backups, 30-day retention, PITR enabled
- **GCS**: Versioning enabled, 365-day retention for uploads
- **Code**: GitHub source of truth
- **Infrastructure**: Terraform state in GCS with versioning

## Performance

### Latency Targets
- **Frontend Load**: < 2s (FCP)
- **API Response**: < 500ms (p95)
- **Document Parse**: < 30s per document
- **Workbook Generation**: < 60s
- **Valuation Calc**: < 120s

### Optimization Strategies
- **Frontend**: Code splitting, lazy loading, image optimization
- **Backend**: Query optimization, connection pooling, caching
- **BigQuery**: Clustered/partitioned tables, materialized views
- **AI Calls**: Batching, streaming responses, result caching

## Cost Model

### Estimated Monthly Costs (Dev)
- **Cloud Run**: $0-50 (mostly free tier)
- **Cloud SQL**: $30-80 (db-f1-micro)
- **BigQuery**: $0-20 (1 GB storage, 10 GB queries)
- **GCS**: $1-10 (< 100 GB)
- **Document AI**: $0-50 (100 docs/month)
- **Vertex AI**: $0-20 (1000 requests/month)
- **Total**: ~$50-200/month

### Estimated Monthly Costs (Production, 100 users)
- **Cloud Run**: $100-300
- **Cloud SQL**: $300-500 (db-custom-4-16384)
- **BigQuery**: $50-200
- **GCS**: $20-50
- **Document AI**: $200-500 (1000 docs/month)
- **Vertex AI**: $100-300
- **Total**: ~$800-2000/month

### Cost Optimization
- Scale down dev environments when not in use
- Use committed use discounts (1 or 3 year)
- Set BigQuery query cost limits
- Implement GCS lifecycle policies
- Cache AI responses aggressively

## Monitoring & Observability

### Metrics Collected
- **Cloud Run**: Request count, latency, error rate, instance count
- **Cloud SQL**: CPU, memory, connections, query latency
- **BigQuery**: Query bytes scanned, slot usage
- **GCS**: Storage size, request count
- **Custom**: Documents processed, validations run, valuations completed

### Logging
- **Format**: Structured JSON with trace IDs
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Retention**: 30 days (default), 90 days for ERROR+
- **Analysis**: Log Explorer, BigQuery export

### Alerting
- **Error Rate**: > 5% over 5 minutes
- **Latency**: p95 > 3s
- **Availability**: < 99% over 1 hour
- **Budget**: 80% of monthly budget consumed

### Tracing
- **OpenTelemetry**: Distributed traces across services
- **Cloud Trace**: End-to-end request visualization
- **Correlation**: Trace ID in all logs and errors

## Compliance & Governance

### Standards
- **SOC 2 Type II**: Ready (audit controls in place)
- **ISO 27001**: Partially compliant (documentation needed)
- **GDPR**: No PII expected; data residency configurable

### Audit Trail
- **User Actions**: All captured in audit_logs table
- **Data Changes**: Tracked with before/after states
- **Access**: IAM policy changes logged
- **Retention**: 7 years in BigQuery

### Data Residency
- **Current**: US (us-central1)
- **Configurable**: EU, Asia via Terraform variables
- **Restrictions**: Document AI limited to US/EU

## Development Workflow

### Local Development
1. Backend: `uvicorn main:app --reload`
2. Frontend: `npm run dev`
3. Database: Cloud SQL Proxy or local Postgres
4. Mocks: Use stubs for AI services

### CI/CD Pipeline
1. **Commit**: Push to GitHub
2. **Lint**: Black, isort, flake8, ESLint
3. **Test**: pytest, Jest
4. **Build**: Docker images
5. **Scan**: Vulnerability scanning
6. **Deploy**: Cloud Run
7. **Migrate**: Alembic upgrade
8. **Smoke Test**: Health checks

### Branching Strategy
- **main**: Production
- **develop**: Staging
- **feature/***: Feature branches
- **hotfix/***: Emergency fixes

## Future Enhancements

### Phase 2 (Q2 2025)
- Real-time collaboration (WebSockets)
- Advanced forecasting (ML models)
- Custom report builder
- SSO (SAML 2.0, OIDC)
- Mobile app (React Native)

### Phase 3 (Q3 2025)
- Multi-currency support
- International accounting standards (IFRS)
- Advanced workflow automation
- Marketplace for data providers
- White-label offering

### Phase 4 (Q4 2025)
- AI-powered financial analysis
- Predictive analytics
- Blockchain-based audit trail
- API marketplace
- Enterprise SLA tiers

