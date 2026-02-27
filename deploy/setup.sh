#!/bin/bash
# =============================================================================
# AWS EC2 Single-Server Deployment Script for the eLearning Platform
# =============================================================================
#
# This script sets up the complete eLearning Django application on a single
# Ubuntu EC2 instance with all services running locally:
#   - PostgreSQL (database)
#   - Redis (channel layer for WebSocket chat + Celery broker)
#   - Nginx (reverse proxy for static files, HTTP, and WebSocket)
#   - Gunicorn (WSGI HTTP server)
#   - Daphne (ASGI WebSocket server)
#   - Celery (background task worker)
#
# Prerequisites:
#   - Ubuntu 22.04+ EC2 instance (t2.micro or t3.micro for free tier)
#   - Security group allowing inbound ports 22 (SSH), 80 (HTTP)
#   - SSH access to the instance
#
# Usage:
#   1. SSH into your EC2 instance
#   2. Upload or clone the project to /home/ubuntu/elearning
#   3. chmod +x deploy/setup.sh
#   4. sudo ./deploy/setup.sh
#
# After running this script, follow the printed instructions to complete setup.
# =============================================================================

set -e  # Exit on any error

APP_DIR="/home/ubuntu/elearning"

echo "=== eLearning Platform - EC2 Setup Script ==="
echo ""

# ---------------------------------------------------------------------------
# 1. System packages
# ---------------------------------------------------------------------------
echo "[1/8] Installing system packages..."
apt-get update
apt-get install -y \
    python3 python3-pip python3-venv python3-dev \
    nginx \
    postgresql postgresql-contrib libpq-dev \
    redis-server \
    gcc \
    git \
    certbot python3-certbot-nginx

# ---------------------------------------------------------------------------
# 2. Start and enable PostgreSQL
# ---------------------------------------------------------------------------
echo "[2/8] Configuring PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

# Create database and user for the application
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='elearning_user'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER elearning_user WITH PASSWORD 'elearning_pass';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='elearning_db'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE elearning_db OWNER elearning_user;"

sudo -u postgres psql -c "ALTER USER elearning_user CREATEDB;"  # Needed for running tests

# ---------------------------------------------------------------------------
# 3. Start and enable Redis
# ---------------------------------------------------------------------------
echo "[3/8] Configuring Redis..."
systemctl start redis-server
systemctl enable redis-server

# Verify Redis is running
redis-cli ping | grep -q "PONG" && echo "  Redis is running." || echo "  WARNING: Redis is not responding."

# ---------------------------------------------------------------------------
# 4. Python virtual environment and dependencies
# ---------------------------------------------------------------------------
echo "[4/8] Setting up Python virtual environment..."
cd "$APP_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ---------------------------------------------------------------------------
# 5. Create log directories
# ---------------------------------------------------------------------------
echo "[5/8] Creating log directories..."
mkdir -p /var/log/gunicorn
mkdir -p /var/log/celery
chown -R ubuntu:www-data /var/log/gunicorn
chown -R ubuntu:www-data /var/log/celery

# ---------------------------------------------------------------------------
# 6. Configure Nginx
# ---------------------------------------------------------------------------
echo "[6/8] Configuring Nginx..."
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/elearning
ln -sf /etc/nginx/sites-available/elearning /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t  # Validate config before restarting
systemctl restart nginx

# ---------------------------------------------------------------------------
# 7. Configure systemd services (Gunicorn, Daphne, Celery)
# ---------------------------------------------------------------------------
echo "[7/8] Setting up systemd services..."
cp "$APP_DIR/deploy/gunicorn.service" /etc/systemd/system/
cp "$APP_DIR/deploy/daphne.service" /etc/systemd/system/
cp "$APP_DIR/deploy/celery.service" /etc/systemd/system/
systemctl daemon-reload

# Enable services to start automatically on boot
systemctl enable gunicorn
systemctl enable daphne
systemctl enable celery

# ---------------------------------------------------------------------------
# 8. Create .env file with default local values
# ---------------------------------------------------------------------------
echo "[8/8] Creating production .env file..."
if [ ! -f "$APP_DIR/.env" ]; then
    cat > "$APP_DIR/.env" << 'ENVEOF'
# Production Environment Variables
# Generated by setup.sh - update values as needed.

DJANGO_SETTINGS_MODULE=elearning.settings.prod
DJANGO_SECRET_KEY=change-me-to-a-random-50-character-string

# PostgreSQL (installed locally on this EC2 instance)
DB_NAME=elearning_db
DB_USER=elearning_user
DB_PASSWORD=elearning_pass
DB_HOST=localhost
DB_PORT=5432

# Redis (installed locally on this EC2 instance)
REDIS_HOST=127.0.0.1

# Django
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
ENVEOF
    echo "  Created .env at $APP_DIR/.env"
else
    echo "  .env already exists, skipping."
fi

# Set ownership of application directory
chown -R ubuntu:ubuntu "$APP_DIR"

echo ""
echo "=========================================="
echo "  Setup complete!"
echo "=========================================="
echo ""
echo "Next steps (run as ubuntu user):"
echo ""
echo "  1. Update the .env file with a real secret key and your EC2 public IP:"
echo "     nano $APP_DIR/.env"
echo ""
echo "  2. Activate the virtual environment:"
echo "     cd $APP_DIR && source venv/bin/activate"
echo ""
echo "  3. Run database migrations:"
echo "     python manage.py migrate"
echo ""
echo "  4. Collect static files:"
echo "     python manage.py collectstatic --noinput"
echo ""
echo "  5. Create an admin account:"
echo "     python manage.py createsuperuser"
echo ""
echo "  6. (Optional) Load demo data:"
echo "     python manage.py seed_data"
echo ""
echo "  7. Start all services:"
echo "     sudo systemctl start gunicorn daphne celery"
echo ""
echo "  8. Visit http://<your-ec2-public-ip>/ to verify"
echo ""
