# Quick Start Guide

## Prerequisites

- Python 3.8 or higher
- Redis server (for Celery)
- pip and virtualenv

## Installation (Automated)

Run the setup script:

```bash
cd valuation_app
./setup.sh
```

This will:
- Create a virtual environment
- Install all dependencies
- Run database migrations
- Create necessary directories
- Prompt you to create a superuser

## Manual Installation

### 1. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create superuser

```bash
python manage.py createsuperuser
```

## Running the Application

You need **three** terminal windows:

### Terminal 1: Redis Server

```bash
redis-server
```

### Terminal 2: Celery Worker

```bash
cd valuation_app
source venv/bin/activate
celery -A valuation_app worker --loglevel=info
```

### Terminal 3: Django Development Server

```bash
cd valuation_app
source venv/bin/activate
python manage.py runserver
```

## Access the Application

1. **Web Interface**: http://localhost:8000
2. **Admin Interface**: http://localhost:8000/admin

## First Steps

### 1. Login

Use the superuser credentials you created.

### 2. Create a Project

1. Click "New Project" on the dashboard
2. Fill in project details
3. Upload the sample CSV file from `sample_data/financial_data_sample.csv`
4. Click "Create Project"

### 3. Wait for Processing

The file will be processed in the background by Celery. Check the project status on the dashboard.

### 4. Set Assumptions

Once the status is "Ready for Assumptions":

1. Click on the project
2. Click "Set Assumptions & Calculate"
3. Review or modify the default assumptions
4. Click "Save & Calculate Valuation"

### 5. View Results

Once the calculation is complete:

1. Click "View Results"
2. Review DCF and CCA valuation results
3. Download the Excel report

## Sample Data Format

Your financial data file should look like:

```
Metric,2020,2021,2022,2023
Revenue,5000000,5500000,6200000,7000000
COGS,3000000,3200000,3500000,3900000
EBITDA,1000000,1200000,1500000,1800000
...
```

## Troubleshooting

### "Connection refused" error

Make sure Redis is running:
```bash
redis-server
```

### Celery tasks not executing

1. Check Celery worker is running
2. Check Redis connection
3. Look for errors in Celery terminal

### File upload errors

1. Ensure `media/uploads` directory exists
2. Check file format (must be .xlsx, .xls, or .csv)
3. Verify file structure matches expected format

## Development Tips

### View Database

```bash
python manage.py dbshell
```

### Create Test Data

```bash
python manage.py shell
```

Then:
```python
from django.contrib.auth.models import User
from core.models import Project

# Create a test user
user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')

# Create a test project
project = Project.objects.create(
    name="Test Valuation",
    client_name="ABC Corp",
    created_by=user
)
```

### Clear All Data

```bash
python manage.py flush
```

## Next Steps

- Read the full README.md for detailed documentation
- Explore the admin interface at /admin
- Customize assumptions defaults in models.py
- Add custom validation rules
- Integrate with external data sources

## Support

For questions or issues, refer to the main README.md or contact the development team.
