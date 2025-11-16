# Business Valuation Django Application

A comprehensive Django-based business valuation application with Celery integration for asynchronous processing.

## Features

- **File Upload**: Upload Excel or CSV files with historical financial data
- **Data Processing**: Automatic parsing and normalization of financial metrics
- **Valuation Assumptions**: Interactive form for setting WACC, growth rates, and multiples
- **DCF Analysis**: Discounted Cash Flow valuation with forecasting
- **CCA Analysis**: Comparable Company Analysis using EBITDA multiples
- **Excel Reports**: Generate detailed Excel reports with formulas
- **Asynchronous Processing**: Celery-based background tasks for long-running calculations

## Project Structure

```
valuation_app/
├── core/                      # Main application
│   ├── engines/              # Valuation engines
│   │   ├── data_ingestion.py    # File parsing
│   │   ├── dcf_engine.py        # DCF calculations
│   │   ├── cca_engine.py        # CCA calculations
│   │   └── excel_exporter.py    # Report generation
│   ├── migrations/           # Database migrations
│   ├── templates/            # HTML templates
│   ├── templatetags/         # Custom template filters
│   ├── admin.py             # Admin interface
│   ├── forms.py             # Django forms
│   ├── models.py            # Database models
│   ├── tasks.py             # Celery tasks
│   ├── urls.py              # URL routing
│   └── views.py             # View functions
├── valuation_app/            # Project settings
│   ├── settings.py          # Django settings
│   ├── celery.py            # Celery configuration
│   ├── urls.py              # Main URL configuration
│   └── wsgi.py              # WSGI application
├── media/                    # User uploads and reports
├── manage.py                 # Django management script
└── requirements.txt          # Python dependencies
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd valuation_app
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file (optional):

```bash
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost/dbname  # Optional, defaults to SQLite
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Start Redis (for Celery)

```bash
# On Linux/Mac
redis-server

# On Windows (use WSL or Docker)
docker run -d -p 6379:6379 redis
```

### 6. Start Celery Worker

In a separate terminal:

```bash
celery -A valuation_app worker --loglevel=info
```

### 7. Run Development Server

```bash
python manage.py runserver
```

Visit http://localhost:8000 to access the application.

## Workflow

### Step 1: Upload Financial Data

1. Click "New Project" on the dashboard
2. Fill in project details (name, client, etc.)
3. Upload an Excel or CSV file with financial data
4. The system will automatically process the file in the background

**File Format**: 
- First column: Metric names (Revenue, COGS, EBITDA, etc.)
- Subsequent columns: Years (2020, 2021, 2022, etc.)
- Each row represents one financial metric

### Step 2: Set Assumptions

1. Once file processing is complete, click "Set Assumptions"
2. Input WACC components (risk-free rate, beta, etc.)
3. Set DCF parameters (terminal growth rate, forecast years)
4. Enter CCA multiples from comparable companies
5. Click "Save & Calculate Valuation"

### Step 3: View Results

1. The system calculates DCF and CCA valuations
2. View the results dashboard with:
   - DCF equity value
   - CCA equity value range (min/median/max)
   - Concluded equity value
3. Download detailed Excel report

## Database Models

### Project
- Main project/engagement entity
- Stores status, file references, and metadata

### FinancialData
- Stores standardized financial metrics
- One row per metric per year

### ValuationAssumptions
- User-defined inputs for valuation
- WACC components, growth rates, multiples

### ValuationResult
- Final valuation outputs
- DCF and CCA results

## Celery Tasks

### process_financial_file
- Reads and parses uploaded files
- Saves data to FinancialData model
- Updates project status

### run_valuation_calculation
- Executes DCF and CCA engines
- Saves results to ValuationResult model
- Marks project as complete

### generate_excel_report_task
- Generates comprehensive Excel report
- Includes all assumptions, calculations, and results

## Admin Interface

Access the Django admin at http://localhost:8000/admin

- Manage projects, financial data, assumptions, and results
- View and edit all entities
- Monitor background task progress

## Production Deployment

### Database
- Use PostgreSQL instead of SQLite
- Set `DATABASE_URL` environment variable

### Web Server
- Use Gunicorn: `gunicorn valuation_app.wsgi:application`
- Configure Nginx as reverse proxy

### Celery
- Use supervisor or systemd to manage Celery workers
- Consider using Flower for monitoring

### Static Files
- Run `python manage.py collectstatic`
- Serve with Nginx or WhiteNoise

## Testing

Run tests (if implemented):

```bash
pytest
```

## Troubleshooting

### Celery Tasks Not Running
- Ensure Redis is running
- Check Celery worker is started
- Review Celery logs for errors

### File Upload Issues
- Check `MEDIA_ROOT` directory exists and is writable
- Verify file format matches expected structure

### Database Errors
- Run migrations: `python manage.py migrate`
- Check database connection settings

## License

Proprietary - Internal Use Only

## Support

For questions or issues, contact the development team.
