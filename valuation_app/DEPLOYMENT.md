# Deployment Guide

## Production Deployment Checklist

### 1. Environment Configuration

Create a production `.env` file:

```bash
# Security
DJANGO_SECRET_KEY=generate-a-strong-random-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/valuation_prod

# Redis/Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.yourprovider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### 2. Database Setup

Install PostgreSQL and create database:

```bash
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres psql
```

```sql
CREATE DATABASE valuation_prod;
CREATE USER valuation_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE valuation_prod TO valuation_user;
\q
```

### 3. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-pip python3-dev libpq-dev redis-server nginx
```

### 4. Application Setup

```bash
# Clone repository
git clone <your-repo-url> /opt/valuation_app
cd /opt/valuation_app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser
```

### 5. Gunicorn Configuration

Create `/etc/systemd/system/valuation.service`:

```ini
[Unit]
Description=Valuation App Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/valuation_app
Environment="PATH=/opt/valuation_app/venv/bin"
EnvironmentFile=/opt/valuation_app/.env
ExecStart=/opt/valuation_app/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/opt/valuation_app/valuation.sock \
    valuation_app.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable valuation
sudo systemctl start valuation
sudo systemctl status valuation
```

### 6. Celery Configuration

Create `/etc/systemd/system/celery.service`:

```ini
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/opt/valuation_app
Environment="PATH=/opt/valuation_app/venv/bin"
EnvironmentFile=/opt/valuation_app/.env
ExecStart=/opt/valuation_app/venv/bin/celery -A valuation_app worker \
    --loglevel=info \
    --pidfile=/var/run/celery/%n.pid \
    --logfile=/var/log/celery/%n.log

[Install]
WantedBy=multi-user.target
```

Create necessary directories:

```bash
sudo mkdir -p /var/run/celery /var/log/celery
sudo chown www-data:www-data /var/run/celery /var/log/celery
```

Enable and start:

```bash
sudo systemctl enable celery
sudo systemctl start celery
sudo systemctl status celery
```

### 7. Nginx Configuration

Create `/etc/nginx/sites-available/valuation`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 50M;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /opt/valuation_app/staticfiles/;
    }

    location /media/ {
        alias /opt/valuation_app/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/opt/valuation_app/valuation.sock;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/valuation /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 8. SSL Certificate (Let's Encrypt)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 9. Firewall Configuration

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow 22
sudo ufw enable
```

### 10. Monitoring and Logging

#### Application Logs

```bash
# Django logs
tail -f /opt/valuation_app/logs/django.log

# Gunicorn logs
sudo journalctl -u valuation -f

# Celery logs
sudo journalctl -u celery -f
tail -f /var/log/celery/worker.log
```

#### System Monitoring

Consider installing:
- **Supervisor**: Process monitoring
- **Flower**: Celery monitoring
- **Sentry**: Error tracking
- **New Relic / DataDog**: Application performance monitoring

### 11. Backup Strategy

#### Database Backup

Create a backup script `/opt/valuation_app/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/valuation"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
pg_dump valuation_prod > $BACKUP_DIR/db_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /opt/valuation_app/media/

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

Add to crontab:

```bash
sudo crontab -e
# Add: 0 2 * * * /opt/valuation_app/backup.sh
```

### 12. Security Hardening

1. **Change Secret Key**: Generate a new strong secret key
2. **Set DEBUG=False**: Never run with DEBUG in production
3. **Configure ALLOWED_HOSTS**: Restrict to your domain only
4. **Use HTTPS**: Always use SSL/TLS
5. **Secure Cookies**: Set CSRF_COOKIE_SECURE and SESSION_COOKIE_SECURE
6. **Rate Limiting**: Consider django-ratelimit
7. **Database Security**: Use strong passwords, restrict access
8. **File Permissions**: Restrict access to sensitive files

### 13. Performance Optimization

1. **Database Indexing**: Ensure proper indexes on models
2. **Caching**: Consider Redis caching for Django
3. **CDN**: Use CDN for static files
4. **Database Connection Pooling**: Use pgbouncer
5. **Gunicorn Workers**: Adjust based on CPU cores (2-4 x num_cores + 1)

### 14. Health Checks

Create a health check endpoint in `core/views.py`:

```python
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'healthy'})
```

Add to `core/urls.py`:

```python
path('health/', views.health_check, name='health_check'),
```

### 15. Maintenance Mode

Create a simple maintenance page and update Nginx config when needed.

## Deployment Commands

### Update Application

```bash
cd /opt/valuation_app
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart valuation
sudo systemctl restart celery
```

### Rollback

```bash
cd /opt/valuation_app
git checkout <previous-commit-hash>
# ... run update commands above
```

## Monitoring Checklist

- [ ] Application is accessible
- [ ] SSL certificate is valid
- [ ] Celery workers are running
- [ ] Background tasks are executing
- [ ] Logs are being written
- [ ] Backups are running
- [ ] Email notifications work
- [ ] File uploads work
- [ ] Database connections are healthy

## Support

For production issues, check:
1. Application logs
2. Nginx error logs: `/var/log/nginx/error.log`
3. System logs: `sudo journalctl -xe`
4. Celery logs
5. Database logs
