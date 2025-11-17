# Valuation Workbench (VWB)

**AI-Powered Business Valuation Platform**

Reduce valuation time from 20-40 hours to 2-4 hours (80%+ time savings) with intelligent document processing, auto-mapping, and formula-rich Excel workbook generation.

[![CI](https://github.com/your-org/vwb/workflows/CI/badge.svg)](https://github.com/your-org/vwb/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🚀 Key Features

- **Intelligent PDF/Excel Extraction**: Document AI + Gemini for accurate data extraction
- **Auto-Mapping**: AI-powered mapping to canonical chart of accounts
- **Formula-Rich Workbooks**: Generate 20+ tab Excel workbooks with formulas
- **Multi-Method Valuation**: DCF, GPCM, GTM with WACC calculations
- **Conversational AI**: Chat interface for assumptions and scenarios
- **Audit-Grade Reports**: Professional PDF reports
- **Real-Time Collaboration**: Multi-user support with Firestore

## 📋 Table of Contents

- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Local Development](#local-development)
- [Deployment](#deployment)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Next.js   │─────▶│   FastAPI    │─────▶│  Cloud SQL  │
│  Frontend   │      │   Backend    │      │ PostgreSQL  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                     ┌──────┴────────┐
                     │               │
               ┌─────▼────┐    ┌────▼─────┐
               │ Vertex AI │    │ Document │
               │  Gemini   │    │   AI     │
               └───────────┘    └──────────┘
                     │               │
               ┌─────▼───────────────▼────┐
               │    Cloud Storage          │
               │    BigQuery              │
               │    Pub/Sub               │
               └──────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## 🚀 Quick Start

### Prerequisites

- **Google Cloud Project** with billing enabled
- **Docker** and **Docker Compose**
- **Node.js 20+** and **Python 3.11+**
- **Terraform 1.5+** (for infrastructure)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/vwb.git
cd vwb
```

### 2. Set Up GCP Credentials

```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Set your project
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID
```

### 3. Run Locally with Docker Compose

```bash
# Create secrets directory
mkdir -p secrets

# Download GCP service account key (or use ADC)
# gcloud iam service-accounts keys create secrets/gcp-key.json \
#   --iam-account=YOUR_SA@$PROJECT_ID.iam.gserviceaccount.com

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs
- **PgAdmin**: http://localhost:5050 (admin@vwb.local / admin)

### 4. Create Admin User

```bash
docker-compose exec backend python -c "
from models import User
from database import SessionLocal
from passlib.hash import bcrypt

db = SessionLocal()
admin = User(
    email='admin@example.com',
    hashed_password=bcrypt.hash('admin123'),
    is_admin=True
)
db.add(admin)
db.commit()
print('Admin user created!')
"
```

### 5. Access Application

1. Open http://localhost:3000
2. Login with `admin@example.com` / `admin123`
3. Create your first engagement

## 💻 Local Development

### Backend (FastAPI)

```bash
cd app/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload --port 8080
```

### Frontend (Next.js)

```bash
cd app/frontend

# Install dependencies
npm install

# Set environment variables
cp .env.local.example .env.local
# Edit .env.local with your API URL

# Start development server
npm run dev
```

### Database Migrations

```bash
cd app/backend

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Running Tests

```bash
# Backend tests
cd app/backend
pytest tests/ -v --cov

# Frontend tests
cd app/frontend
npm test

# Run all tests
docker-compose run backend pytest
docker-compose run frontend npm test
```

## 🚢 Deployment

### Deploy to GCP

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment instructions.

**Quick Deploy:**

```bash
# 1. Deploy infrastructure with Terraform
cd infra
terraform init
terraform apply -var-file=terraform.tfvars

# 2. Deploy via GitHub Actions
git push origin main  # Deploys to staging

# 3. Or deploy manually via Cloud Build
gcloud builds submit --config=infra/cloudbuild.yaml
```

### Environments

- **Development**: Auto-deploy on push to `develop` branch
- **Staging**: Auto-deploy on push to `main` branch
- **Production**: Auto-deploy on GitHub release

## 🛠️ Tech Stack

### Frontend
- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **shadcn/ui** components
- **React Query** + **Zustand**

### Backend
- **Python 3.11**
- **FastAPI**
- **SQLAlchemy** + **Alembic**
- **Pydantic** validation
- **Uvicorn** ASGI server

### AI & ML
- **Document AI** (PDF extraction)
- **Vision AI** (image processing)
- **Vertex AI Gemini 1.5** (intelligent mapping, chat)
- **LangChain** (conversational agent)

### Data & Storage
- **Cloud SQL PostgreSQL** (transactional data)
- **BigQuery** (analytics, normalized data)
- **Cloud Storage** (file uploads)
- **Firestore** (real-time collaboration)
- **Memorystore Redis** (caching)

### Infrastructure
- **Google Cloud Run** (containerized apps)
- **Terraform** (infrastructure as code)
- **GitHub Actions** (CI/CD)
- **Cloud Build** (image building)
- **Pub/Sub** (event-driven processing)
- **Cloud Tasks** (background jobs)

## 📁 Project Structure

```
vwb/
├── .github/workflows/      # GitHub Actions CI/CD
├── app/
│   ├── backend/            # FastAPI backend
│   │   ├── ai/            # AI services (Gemini, Document AI)
│   │   ├── api/v1/        # API endpoints
│   │   ├── models.py      # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── valuation/     # Valuation engines (DCF, GPCM, GTM)
│   │   ├── workbook/      # Excel workbook generator
│   │   └── main.py        # FastAPI app
│   └── frontend/          # Next.js frontend
│       ├── app/           # App router pages
│       ├── components/    # React components
│       └── lib/           # Utilities
├── infra/                 # Terraform infrastructure
│   ├── main.tf            # Main infrastructure
│   ├── variables.tf       # Variables
│   ├── outputs.tf         # Outputs
│   └── cloudbuild.yaml    # Cloud Build config
├── tests/                 # Tests
├── docker-compose.yml     # Local development
├── ARCHITECTURE.md        # Architecture docs
├── DEPLOYMENT.md          # Deployment guide
└── README.md             # This file
```

## 📚 API Documentation

### Interactive API Docs

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

### Key Endpoints

```
POST   /api/v1/auth/login                    # Authentication
GET    /api/v1/engagements                   # List engagements
POST   /api/v1/engagements                   # Create engagement
POST   /api/v1/{id}/files/upload-url         # Get signed upload URLs
POST   /api/v1/{id}/files                    # Process uploaded files
POST   /api/v1/{id}/mappings/suggest         # AI mapping suggestions
POST   /api/v1/{id}/validation               # Validate financials
POST   /api/v1/{id}/valuation/dcf            # Run DCF valuation
POST   /api/v1/{id}/workbook/generate        # Generate Excel workbook
POST   /api/v1/{id}/chat                     # Chat with AI assistant
```

## 🧪 Sample Data

Sample financial statements are provided in `samples/statements/`:

```bash
# Upload sample PDFs
curl -X POST http://localhost:8080/api/v1/engagements/123/files \
  -F "file=@samples/statements/pdf/income_statement.pdf"

# Test with sample Excel
curl -X POST http://localhost:8080/api/v1/engagements/123/files \
  -F "file=@samples/statements/excel/financials.xlsx"
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest` and `npm test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check `/docs` folder
- **Issues**: [GitHub Issues](https://github.com/your-org/vwb/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/vwb/discussions)
- **Email**: support@yourcompany.com

## 🙏 Acknowledgments

- Google Cloud Platform for infrastructure
- OpenAI/Anthropic for AI model inspiration
- Open-source community for amazing tools

## 📊 Project Status

- ✅ Core infrastructure deployed
- ✅ Document processing pipeline
- ✅ AI-powered mapping
- ✅ DCF valuation engine
- ✅ Workbook generation
- ✅ Chat interface
- ⬜ GPCM valuation (in progress)
- ⬜ GTM valuation (in progress)
- ⬜ PDF report generation (planned)
- ⬜ Real-time collaboration (planned)

---

**Built with ❤️ by the VWB Team**
