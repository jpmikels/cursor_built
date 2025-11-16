# Project Structure

## Complete Django Business Valuation Application

This document provides an overview of the complete project structure.

## Directory Tree

```
valuation_app/
├── core/                           # Main Django application
│   ├── engines/                    # Valuation calculation engines
│   │   ├── __init__.py
│   │   ├── cca_engine.py          # Comparable Company Analysis engine
│   │   ├── data_ingestion.py      # File parsing and data extraction
│   │   ├── dcf_engine.py          # Discounted Cash Flow engine
│   │   └── excel_exporter.py      # Excel report generator
│   ├── migrations/                 # Database migrations
│   │   └── __init__.py
│   ├── templates/                  # HTML templates
│   │   └── core/
│   │       ├── base.html          # Base template
│   │       ├── dashboard.html     # Main dashboard
│   │       ├── create_project.html # Project creation form
│   │       ├── project_detail.html # Project details view
│   │       ├── assumptions_input.html # Assumptions form
│   │       ├── results_dashboard.html # Results display
│   │       ├── financial_data.html # Data table view
│   │       ├── login.html         # Login page
│   │       └── delete_project.html # Confirmation page
│   ├── templatetags/              # Custom template tags
│   │   ├── __init__.py
│   │   └── core_extras.py         # Custom filters
│   ├── __init__.py
│   ├── admin.py                   # Django admin configuration
│   ├── apps.py                    # App configuration
│   ├── forms.py                   # Django forms
│   ├── models.py                  # Database models
│   ├── tasks.py                   # Celery background tasks
│   ├── urls.py                    # URL routing
│   └── views.py                   # View functions
├── media/                         # User-uploaded files
│   ├── uploads/                   # Financial data files
│   └── reports/                   # Generated Excel reports
├── sample_data/                   # Sample data for testing
│   └── financial_data_sample.csv  # Example financial data
├── static/                        # Static files (CSS, JS, images)
│   └── .gitkeep
├── valuation_app/                 # Django project configuration
│   ├── __init__.py
│   ├── celery.py                 # Celery configuration
│   ├── settings.py               # Django settings
│   ├── urls.py                   # Main URL configuration
│   └── wsgi.py                   # WSGI application
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
├── DEPLOYMENT.md                  # Production deployment guide
├── manage.py                      # Django management script
├── PROJECT_STRUCTURE.md           # This file
├── QUICKSTART.md                  # Quick start guide
├── README.md                      # Main documentation
├── requirements.txt               # Python dependencies
└── setup.sh                       # Automated setup script
```

## Key Components

### 1. Database Models (`core/models.py`)

- **Project**: Main project/engagement entity
- **FinancialData**: Stores standardized financial metrics
- **ValuationAssumptions**: User-defined valuation inputs
- **ValuationResult**: Final valuation calculations

### 2. Valuation Engines (`core/engines/`)

#### Data Ingestion Engine (`data_ingestion.py`)
- Parses Excel and CSV files
- Extracts financial metrics by year
- Normalizes metric names

#### DCF Engine (`dcf_engine.py`)
- Forecasts free cash flows
- Calculates present values
- Computes terminal value
- Derives enterprise and equity values

#### CCA Engine (`cca_engine.py`)
- Applies EBITDA multiples
- Calculates enterprise value range
- Derives equity value range

#### Excel Exporter (`excel_exporter.py`)
- Generates comprehensive Excel reports
- Includes all assumptions and calculations
- Creates formatted workbooks with multiple sheets

### 3. Celery Tasks (`core/tasks.py`)

- **process_financial_file**: Background file processing
- **run_valuation_calculation**: DCF and CCA calculations
- **generate_excel_report_task**: Report generation

### 4. Views (`core/views.py`)

- **dashboard_view**: Main dashboard
- **create_project_view**: Upload workflow
- **project_detail_view**: Project status
- **assumptions_input_view**: Assumptions form
- **results_dashboard_view**: Results display
- **download_excel_view**: Report download
- **financial_data_view**: Data table view
- **delete_project_view**: Project deletion

### 5. Forms (`core/forms.py`)

- **ProjectUploadForm**: Project creation and file upload
- **ValuationAssumptionsForm**: Valuation inputs

### 6. Templates (`core/templates/core/`)

All HTML templates with Bootstrap 5 styling:
- Base template with navigation
- Dashboard with project list
- Project creation form
- Project detail view
- Assumptions input form
- Results dashboard
- Financial data table
- Login page
- Delete confirmation

### 7. Configuration

- **settings.py**: Django configuration (database, media, Celery)
- **celery.py**: Celery app configuration
- **urls.py**: URL routing
- **requirements.txt**: Python dependencies

## Workflow

```
1. Upload File → process_financial_file task
   ↓
2. File processed → Status: READY
   ↓
3. Set Assumptions → run_valuation_calculation task
   ↓
4. Calculation complete → Status: COMPLETE
   ↓
5. View Results & Download Report
```

## Technology Stack

- **Framework**: Django 4.2
- **Task Queue**: Celery 5.3
- **Broker**: Redis
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: Bootstrap 5
- **Data Processing**: Pandas, NumPy
- **Excel**: openpyxl, XlsxWriter

## API Endpoints

- `/` - Dashboard
- `/project/create/` - Create project
- `/project/<id>/` - Project detail
- `/project/<id>/assumptions/` - Set assumptions
- `/project/<id>/results/` - View results
- `/project/<id>/financial-data/` - View data
- `/project/<id>/download/` - Download report
- `/project/<id>/delete/` - Delete project
- `/login/` - Login page
- `/logout/` - Logout
- `/admin/` - Django admin

## Database Schema

### Project Table
- id, name, client_name, description
- status (NEW, PROCESSING, READY, CALCULATING, COMPLETE, ERROR)
- uploaded_file, original_filename
- fiscal_year_end, currency, industry_code
- created_by (FK to User)
- created_at, updated_at
- error_message
- excel_report_path

### FinancialData Table
- id, project (FK)
- metric_name, year, value
- source_sheet, source_row
- is_derived
- created_at, updated_at

### ValuationAssumptions Table
- id, project (FK, OneToOne)
- risk_free_rate, equity_risk_premium, beta
- size_premium, company_specific_premium
- cost_of_debt, tax_rate
- debt_weight, equity_weight
- terminal_growth_rate, forecast_years
- mid_year_convention, revenue_growth_rate
- ebitda_multiple_min, ebitda_multiple_median, ebitda_multiple_max
- created_at, updated_at

### ValuationResult Table
- id, project (FK, OneToOne)
- dcf_enterprise_value, dcf_equity_value
- dcf_pv_forecast_fcf, dcf_pv_terminal_value
- cca_equity_value_min, cca_equity_value_median, cca_equity_value_max
- concluded_equity_value
- wacc_used, calculation_notes
- calculated_at, updated_at

## Features Implemented

✅ User authentication and authorization
✅ File upload and parsing (Excel, CSV)
✅ Background task processing with Celery
✅ DCF valuation with forecasting
✅ CCA valuation with multiples
✅ WACC calculation
✅ Interactive assumptions form
✅ Results dashboard
✅ Excel report generation
✅ Project management (CRUD)
✅ Financial data display
✅ Status tracking
✅ Error handling
✅ Admin interface
✅ Bootstrap UI
✅ Responsive design

## Future Enhancements

- [ ] Sensitivity analysis visualizations
- [ ] Historical data visualization (charts)
- [ ] Multiple valuation scenarios
- [ ] Market data integration (yfinance, etc.)
- [ ] PDF report generation
- [ ] Audit trail
- [ ] Collaborative features
- [ ] Advanced forecasting models
- [ ] Machine learning for metric normalization
- [ ] REST API
- [ ] Export to other formats
- [ ] Notification system

## Maintenance

- Run migrations after model changes: `python manage.py makemigrations && python manage.py migrate`
- Collect static files: `python manage.py collectstatic`
- Check for linter issues: `flake8 .`
- Run tests: `pytest`

## Documentation Files

- **README.md**: Main project documentation
- **QUICKSTART.md**: Quick start guide for developers
- **DEPLOYMENT.md**: Production deployment instructions
- **PROJECT_STRUCTURE.md**: This file - project structure overview

## License

Proprietary - Internal Use Only
