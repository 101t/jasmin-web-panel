# Systemd & Nginx Deployment

For traditional Linux server deployments (Ubuntu/Debian), we recommend running the application with Gunicorn managed by Systemd, and using Nginx as a reverse proxy.

## Prerequisites

- Python 3.11 (install via `apt` or `pyenv`)
- PostgreSQL 14+
- Redis 6+
- Nginx

### Install Python 3.11

=== "Ubuntu"

    ```bash
    sudo apt update
    sudo apt install -y software-properties-common
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3.11-dev
    ```

=== "Debian"

    The `deadsnakes` PPA is not available on Debian. Use `pyenv` to install Python 3.11:

    ```bash
    # Install pyenv dependencies
    sudo apt update
    sudo apt install -y build-essential libssl-dev zlib1g-dev \
        libbz2-dev libreadline-dev libsqlite3-dev curl git \
        libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

    # Install pyenv
    curl https://pyenv.run | bash

    # Add to shell profile (~/.bashrc or ~/.profile)
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc
    source ~/.bashrc

    # Install and set Python 3.11
    pyenv install 3.11
    pyenv global 3.11
    ```

## 1. Application Setup

```bash
# Clone the project
sudo mkdir -p /opt/jasmin-web-panel
cd /opt/jasmin-web-panel
git clone https://github.com/101t/jasmin-web-panel.git .

# Create a virtual environment with Python 3.11
python3.11 -m venv env
source env/bin/activate

pip install --upgrade pip wheel uv
uv pip install -r pyproject.toml --extra=prod
```

### Configure Environment

```bash
cp sample.env .env
# Edit .env and set SECRET_KEY, PRODB_URL, REDIS_HOST, TELNET_HOST, etc.
nano .env
```

### PostgreSQL Database Setup

```sql
-- Run as the postgres superuser
sudo -u postgres psql

CREATE USER jasmin_user WITH PASSWORD 'strong_password_here';
CREATE DATABASE jasmin_db OWNER jasmin_user;
\c jasmin_db
GRANT USAGE, CREATE ON SCHEMA public TO jasmin_user;
\q
```

Set `PRODB_URL` in your `.env`:

```dotenv
PRODB_URL=postgres://jasmin_user:strong_password_here@localhost:5432/jasmin_db
```

### Database Migrations

```bash
source env/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.pro

python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

!!! tip "Migration troubleshooting"
    If you see `permission denied for schema public`, connect to PostgreSQL and run:
    ```sql
    GRANT ALL ON SCHEMA public TO jasmin_user;
    ALTER SCHEMA public OWNER TO jasmin_user;
    ```

### Set Permissions

```bash
sudo chown -R www-data:www-data /opt/jasmin-web-panel
sudo chmod -R 750 /opt/jasmin-web-panel
sudo mkdir -p /opt/jasmin-web-panel/logs
sudo chown www-data:www-data /opt/jasmin-web-panel/logs
```

## 2. Systemd Services

### Web Application Service

Create **/etc/systemd/system/jasmin-web.service**:

```ini
[Unit]
Description=Jasmin Web Panel
Requires=postgresql.service
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/jasmin-web-panel
Environment="DJANGO_SETTINGS_MODULE=config.settings.pro"
ExecStart=/opt/jasmin-web-panel/env/bin/gunicorn \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --timeout 120 \
    --log-level info \
    --access-logfile /opt/jasmin-web-panel/logs/gunicorn.log \
    --error-logfile /opt/jasmin-web-panel/logs/gunicorn_error.log \
    config.wsgi:application
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Celery Worker Service

Create **/etc/systemd/system/jasmin-celery.service**:

```ini
[Unit]
Description=Jasmin Web Panel Celery Worker
Requires=redis-server.service
After=network.target redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/jasmin-web-panel
Environment="DJANGO_SETTINGS_MODULE=config.settings.pro"
ExecStart=/opt/jasmin-web-panel/env/bin/celery \
    -A config worker \
    --max-tasks-per-child 1 \
    -l info \
    --logfile /opt/jasmin-web-panel/logs/celery.log
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start both services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable jasmin-web jasmin-celery
sudo systemctl start jasmin-web jasmin-celery
sudo systemctl status jasmin-web jasmin-celery
```

## 3. Nginx Configuration

Configure Nginx to proxy requests to Gunicorn and serve static files.

Create **/etc/nginx/sites-available/jasmin_web**:

```nginx
# Map $http_upgrade to correctly handle WebSocket and regular HTTP connections
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

upstream jasmin_web {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name sms.yourdomain.com;

    client_max_body_size 20M;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Static files
    location /static/ {
        alias /opt/jasmin-web-panel/public/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Media files (if applicable)
    location /media/ {
        alias /opt/jasmin-web-panel/public/media/;
        expires 7d;
        access_log off;
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://jasmin_web;
        proxy_http_version 1.1;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;

        # WebSocket support (if needed)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }
}
```

Enable the site and reload Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/jasmin_web /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 4. SSL with Certbot

Secure your panel with HTTPS (free certificate from Let's Encrypt):

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d sms.yourdomain.com
# Auto-renewal is configured automatically by certbot
sudo systemctl status certbot.timer
```

After obtaining a certificate, Certbot updates your Nginx config to redirect HTTP → HTTPS automatically.

## 5. Verify the Deployment

```bash
# Check service status
sudo systemctl status jasmin-web
sudo systemctl status jasmin-celery

# Tail application logs
sudo tail -f /opt/jasmin-web-panel/logs/gunicorn.log
sudo tail -f /opt/jasmin-web-panel/logs/gunicorn_error.log

# Test Nginx config
sudo nginx -t
```

Access the panel at `http://sms.yourdomain.com` (or `https://` after SSL setup).
