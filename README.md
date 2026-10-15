# Jasmin Web Panel

<div align="center">

[![CI](https://github.com/101t/jasmin-web-panel/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/101t/jasmin-web-panel/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-online-blue.svg)](https://about.supernovasoft.com/jasmin-web-panel/)
[![Docker Image](https://img.shields.io/docker/v/tarekaec/jasmin_web_panel?sort=semver&label=docker)](https://hub.docker.com/r/tarekaec/jasmin_web_panel)
[![Docker Pulls](https://img.shields.io/docker/pulls/tarekaec/jasmin_web_panel)](https://hub.docker.com/r/tarekaec/jasmin_web_panel)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**A modern, feature-rich web interface for managing [Jasmin SMS Gateway](https://github.com/jookies/jasmin)**

[Features](#-features) • [Quick Start](#-quick-start) • [Installation](#-installation) • [Docker](#-docker-deployment) • [Support](#-support)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
  - [Manual Installation](#manual-installation)
  - [Docker Deployment](#-docker-deployment)
  - [Docker Compose](#docker-compose-deployment)
- [Configuration](#-configuration)
- [Production Deployment](#-production-deployment)
- [Submit Log Integration](#-submit-log-integration)
- [Default Credentials](#-default-credentials)
- [Troubleshooting](#-troubleshooting)
- [Support](#-support)

---

## 🎯 Overview

Jasmin Web Panel is a comprehensive web-based management interface for [Jasmin SMS Gateway](https://github.com/jookies/jasmin). Built with Django and modern web technologies, it provides an intuitive dashboard to configure, monitor, and manage your SMS operations efficiently.

### How it works

```mermaid
flowchart LR
    user(["You<br/>browser or API client"])
    panel["<b>Jasmin Web Panel</b><br/>pages + REST API"]
    jcli["<b>Jasmin gateway</b><br/>jcli console :8990"]
    smsc(["SMSC providers<br/>and your apps"])
    mq{{"RabbitMQ"}}
    db[("Panel database")]

    user -- "(1) use the panel" --> panel
    panel -- "(2) jcli commands over telnet<br/>(add user, create route, ...)" --> jcli
    jcli -- "(3) answer: OK or error message" --> panel
    jcli -. "SMS traffic never passes<br/>through the panel" .- smsc
    jcli -- "delivery results" --> mq
    mq -- "sms_logger" --> db
    panel -- "Submit Log page reads" --> db
```

**How the panel and the gateway talk:**

1. You use the panel in the browser (or call its REST API).
2. For every action (add a user, create a route, start a connector) the panel opens a telnet session to Jasmin's
   **jcli** console on port `8990` and types the same commands an administrator would, then runs `persist` so the
   change survives a restart.
3. Jasmin answers; the panel shows the result, or Jasmin's own error message if the command was refused.

The panel only *manages* the gateway. Your SMS traffic flows through Jasmin's SMPP server and HTTP API and never
passes through the panel. For the Submit Log, Jasmin publishes delivery results to RabbitMQ and the `sms_logger`
service stores them in the panel's database, which the **[Submit Log](#-submit-log-integration)** page reads.

---

## ✨ Features

### Core Functionality
- 🚀 **Dashboard**: Real-time statistics and system health monitoring
- 👥 **User Management**: Create and manage users with role-based access control
- 📡 **SMPP Connectors**: Configure and monitor SMPP client/server connections
- 🌐 **HTTP API**: Manage HTTP connectors for sending SMS via REST API
- 🔀 **Message Routing**: Define routing rules and filters for message delivery
- 📨 **MO/MT Routers**: Configure Mobile Originated and Mobile Terminated message routing

### Monitoring & Analytics
- 📊 **Submit Logs**: Comprehensive message tracking with advanced search and filtering
  - Search by Message ID, Source/Destination address, UID, and content
  - Filter by status: Success (`ESME_ROK`, `ESME_RINVNUMDESTS`), Failed (`ESME_RDELIVERYFAILURE`), Unknown
  - Real-time statistics with color-coded status badges
- 🔍 **Service Monitoring**: Monitor Jasmin gateway service health
- 📈 **Real-time Status**: Live SMPP connector status monitoring

### Advanced Features
- 🔧 **RESTful API**: Programmatic access to all management functions
- ⚡ **Rate Limiting**: Configure throughput limits per user/connector
- 🔒 **Multi-tenancy**: Manage multiple clients/users
- 📝 **Audit Logging**: Track all administrative actions
- 🌍 **Internationalization**: Multi-language support ready
- 📱 **Responsive Design**: Mobile-friendly interface

---

## 📦 Prerequisites

### Required Components
- **[Jasmin SMS Gateway](http://docs.jasminsms.com/en/latest/installation/index.html)**: v0.9+ installed and running
- **Python**: 3.11 or 3.12 (both tested in CI; the Docker image uses 3.12)
- **telnet client**: the panel drives Jasmin's jcli through the `telnet` command (`apt install telnet`; already in the Docker image)
- **Database**: PostgreSQL 12+ (recommended) or MySQL 8.0+
- **Redis**: 6.0+ (for caching and Celery)
- **RabbitMQ**: 3.10+ (used by Jasmin and the submit-log consumer)

### System Requirements
- **OS**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- **RAM**: Minimum 2GB (4GB+ recommended for production)
- **Disk**: 10GB+ free space
- **Network**: Connectivity to Jasmin telnet interface (default: port 8990)

---

## 🚀 Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/101t/jasmin-web-panel.git
cd jasmin-web-panel

# Copy and configure environment file
cp sample.env .env
# Edit .env: at least set SECRET_KEY, and change the default passwords for production

# Start all services
docker compose up -d

# Access the web interface
open http://localhost:8999
```

**Default credentials**: `admin` / `secret` ⚠️ **Change immediately after first login!**

---

## 💻 Installation

### Manual Installation

#### 1. Clone and Setup Environment

```bash
# Clone repository
git clone https://github.com/101t/jasmin-web-panel.git
cd jasmin-web-panel

# Create virtual environment (recommended)
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Upgrade pip and install build tools
pip install --upgrade pip wheel uv

# Install dependencies
uv pip install -r pyproject.toml --extra=prod
```

#### 2. Configure Application

```bash
# Copy sample environment file
cp sample.env .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Essential configuration**:

```ini
# Django Settings
DEBUG=False  # Always False in production; set True for local development
SECRET_KEY=your-very-long-random-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
PRODB_URL=postgres://username:password@localhost:5432/jasmin_web_db

# Jasmin Gateway Connection
TELNET_HOST=127.0.0.1
TELNET_PORT=8990
TELNET_USERNAME=jcliadmin
TELNET_PW=jclipwd
TELNET_TIMEOUT=10

# Redis for Cache & Celery
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=<Optional>

# Submit Log Feature
SUBMIT_LOG=True
```

#### 3. Create PostgreSQL Database

> **Note**: If you are using PostgreSQL 15 or newer, the `CREATE` privilege on the `public` schema is **no longer granted to all users by default**. Run the following commands as a PostgreSQL superuser to create the application database and grant the required permissions.

```sql
-- Connect as a PostgreSQL superuser (e.g. psql -U postgres)
-- Replace the values below with those you set in PRODB_URL in your .env file
CREATE USER your_db_user WITH PASSWORD 'your_db_password';
CREATE DATABASE your_db_name OWNER your_db_user;
\c your_db_name
GRANT USAGE, CREATE ON SCHEMA public TO your_db_user;
```

#### 4. Initialize Database

```bash
# Run migrations
python manage.py migrate

# Load sample data (optional)
python manage.py samples

# Collect static files
python manage.py collectstatic --no-input

# Create your own admin account (optional, "samples" already creates admin / secret)
python manage.py createsuperuser
```

#### 5. Run Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

Access the application at `http://localhost:8000`

---

## 🐳 Docker Deployment

### Using Pre-built Image

```bash
# Pull the latest image
docker pull tarekaec/jasmin_web_panel:3.1.0

# Configure environment
cp sample.env .env
# Edit .env with your settings

# Run container
docker run -d \
  --name jasmin-web \
  -p 8999:8000 \
  --env-file .env \
  -v ./public:/app/public \
  tarekaec/jasmin_web_panel:3.1.0
```

### Building Custom Image

```bash
# Build from Dockerfile
docker build -f config/docker/slim/Dockerfile -t jasmin_web_panel:custom .

# Run your custom image
docker run -d \
  --name jasmin-web \
  -p 8999:8000 \
  --env-file .env \
  jasmin_web_panel:custom
```

### Docker Compose Deployment

Full stack deployment with all dependencies:

```bash
# Ensure .env is configured
cp sample.env .env

# Start all services
docker compose up -d

# View logs
docker compose logs -f jasmin-web

# Check service status
docker compose ps

# Stop all services
docker compose down
```

**Services included**:
- `jasmin-web`: Web application (port 8999)
- `jasmin-celery`: Background task processor
- `db`: PostgreSQL database
- `redis`: Redis cache
- `rabbitmq`: RabbitMQ message broker
- `jasmin`: Jasmin SMS Gateway (ports 2775, 8990, 1401)
- `sms_logger`: SMS submit log collector

#### ARM64/AArch64 Support

The Dockerfile builds on both amd64 and arm64 without changes:

```bash
docker build -f config/docker/slim/Dockerfile -t jasmin_web_panel:custom .
```

---

## ⚙️ Configuration

### Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEBUG` | Enable debug mode | `False` | ✅ |
| `SECRET_KEY` | Django secret key | - | ✅ |
| `ALLOWED_HOSTS` | Allowed hosts | `*` | ✅ |
| `PRODB_URL` | PostgreSQL URL | - | ✅ |
| `REDIS_HOST` | Redis host | `redis` | ✅ |
| `REDIS_PORT` | Redis port | `6379` | ✅ |
| `REDIS_DB` | Redis database | `0` | ✅ |
| `TELNET_HOST` | Jasmin telnet host | `127.0.0.1` | ✅ |
| `TELNET_PORT` | Jasmin telnet port | `8990` | ✅ |
| `TELNET_USERNAME` | Jasmin admin username | `jcliadmin` | ✅ |
| `TELNET_PW` | Jasmin admin password | `jclipwd` | ✅ |
| `TELNET_TIMEOUT` | Seconds to wait for a jcli answer | `10` | ❌ |
| `HTTPS_ONLY` | Secure cookies and HTTPS redirect (set when served over HTTPS) | `False` | ❌ |
| `CSRF_TRUSTED_ORIGINS` | Origins allowed to post forms, e.g. `https://sms.example.com` | - | ❌ |
| `SUBMIT_LOG` | Enable submit log tracking | `False` | ❌ |
| `API_THROTTLE_ANON` | API rate limit for anonymous requests | `20/minute` | ❌ |
| `API_THROTTLE_USER` | API rate limit for authenticated requests | `120/minute` | ❌ |

The [configuration guide](https://about.supernovasoft.com/jasmin-web-panel/getting-started/configuration/) lists every variable, including the Send SMS (`HTTP_*`, `SMPP_*`) settings.

### Jasmin Gateway Configuration

Ensure Jasmin is configured properly:

1. Enable `submit_sm_resp` publishing in `jasmin.cfg`:
   ```ini
   [sm-listener]
   publish_submit_sm_resp = True
   ```

2. Restart Jasmin:
   ```bash
   systemctl restart jasmin
   ```

---

## 🚀 Production Deployment

### Nginx & Systemd Setup

#### 1. Create Systemd Service

Create `/etc/systemd/system/jasmin-web.service`:

```ini
[Unit]
Description=Jasmin Web Panel
Requires=postgresql.service
After=network.target postgresql.service

[Service]
Type=simple
SyslogIdentifier=jasminwebpanel
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

### Create Celery Worker Service

The web panel requires a Celery worker to process background tasks like report exports from Submit Logs Page.

Create `/etc/systemd/system/jasmin-web-panel-celery.service`:

```ini
[Unit]
Description=Jasmin Web Panel Celery Worker
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
SyslogIdentifier=jasmin-web-panel-celery
User=www-data
Group=www-data
WorkingDirectory=/opt/jasmin-web-panel
Environment="DJANGO_SETTINGS_MODULE=config.settings.pro"
Environment="CELERY_LOG_LEVEL=info"
ExecStart=/opt/jasmin-web-panel/env/bin/celery --app config worker --max-tasks-per-child 1 -l info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable jasmin-web.service
sudo systemctl start jasmin-web.service
sudo systemctl status jasmin-web.service
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable jasmin-web-panel-celery.service
sudo systemctl start jasmin-web-panel-celery.service
sudo systemctl status jasmin-web-panel-celery.service
```


#### 3. Configure Nginx

Create `/etc/nginx/sites-available/jasmin_web`:

```nginx
upstream jasmin_web {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name sms.yourdomain.com;  # Replace with your domain
    charset utf-8;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Logging
    access_log /var/log/nginx/jasmin_web_access.log combined;
    error_log /var/log/nginx/jasmin_web_error.log;
    
    # Static files
    location /static/ {
        alias /opt/jasmin-web-panel/public/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /opt/jasmin-web-panel/public/media/;
    }
    
    # Proxy to Django
    location / {
        proxy_pass http://jasmin_web;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        client_max_body_size 20M;
    }
}
```

#### 4. Enable Nginx Configuration

```bash
sudo ln -s /etc/nginx/sites-available/jasmin_web /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 5. Setup SSL (Recommended)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d sms.yourdomain.com
```

---

## 📊 Submit Log Integration

Track all SMS messages submitted through Jasmin Gateway with detailed status information.

### Setup Instructions

1. **Enable in configuration**:
   ```ini
   SUBMIT_LOG=True
   ```

2. **Configure SMS Logger**:
   ```ini
   DB_HOST=db
   DB_DATABASE=jasmin
   DB_USER=jasmin
   DB_PASS=jasmin
   DB_TABLE=submit_log
   ```

### Features

- ✅ **Real-time Tracking**: Monitor message submission and delivery status
- 🔍 **Advanced Search**: Search by Message ID, addresses, UID, or content
- 🎯 **Status Filtering**: 
  - Success: `ESME_ROK`, `ESME_RINVNUMDESTS`
  - Failed: `ESME_RDELIVERYFAILURE`
  - Unknown: All other status codes
- 📈 **Statistics Dashboard**: View total, success, failed, and unknown counts
- 🎨 **Color-coded Badges**: Visual status identification
- 📄 **Pagination**: Handle large volumes efficiently

---

## 🔐 Default Credentials

⚠️ **SECURITY WARNING**: Change default credentials immediately after first login!

```
Username: admin
Password: secret
```

### Change Password

**Via Web Interface**:
1. Log in with default credentials
2. Navigate to **Profile** → **Change Password**
3. Enter new secure password

**Via Command Line**:
```bash
python manage.py changepassword admin
```

---

## 🔧 Troubleshooting

### `permission denied for schema public` during migrations

This error occurs on **PostgreSQL 15+** where the `CREATE` privilege on the `public` schema is no longer granted to all users by default.

**Solution** — connect to PostgreSQL as a superuser and run:

```sql
\c your_db_name     -- connect to your application database (matches DB name in PRODB_URL)
GRANT USAGE, CREATE ON SCHEMA public TO your_db_user;  -- matches DB user in PRODB_URL
```

If you created the database without setting the owner correctly, you can also fix it with:

```sql
ALTER DATABASE your_db_name OWNER TO your_db_user;
```

For new Docker deployments this is handled automatically by `config/docker/postgres/init.sql` when the Postgres data volume is first initialized. If you already have an existing `postgres_data` volume, you must either run the GRANT statements above manually or recreate the Postgres volume so the init script can run.

### Cannot connect to Jasmin Gateway

The pages show the reason in the table, for example *"Could not connect to Jasmin jcli at 127.0.0.1:8990"*
or *"Jasmin jcli login failed, check TELNET_USERNAME and TELNET_PW"*.

**Solutions**:
- Verify Jasmin is running: `systemctl status jasmin`
- Check telnet connectivity: `telnet localhost 8990`
- Confirm `TELNET_*` settings match Jasmin configuration
- Ensure firewall allows port 8990
- For manual installs, make sure the `telnet` client is installed (`apt install telnet`)

### Submit logs not appearing

**Solutions**:
- Verify `SUBMIT_LOG=True` in `.env`
- Check SMS Logger service: `docker compose ps sms_logger`
- Confirm `publish_submit_sm_resp = True` in `jasmin.cfg`
- Check logs: `docker compose logs sms_logger`

### Static files not loading

The panel serves its static files itself (WhiteNoise) once they are collected; the Docker image does this on start.

**Solutions**:
```bash
python manage.py collectstatic --no-input --clear
sudo chown -R www-data:www-data /opt/jasmin-web-panel/public/
sudo nginx -t && sudo systemctl reload nginx
```

### Cannot sign in with an account made by `createsuperuser`

Accounts created before this fix were saved with an unverified email, which the sign-in page refuses. Mark them verified:

```bash
python manage.py shell -c "from main.users.models import User; User.objects.filter(is_superuser=True).update(is_email=True, is_verified=True)"
```

### View Application Logs

```bash
# Docker Compose
docker compose logs -f jasmin-web

# Systemd
sudo journalctl -u jasmin-web.service -f
```

---

## 💬 Support

### Community Support

- **Telegram**: Join our community → [https://t.me/jasminwebpanel](https://t.me/jasminwebpanel)
- **GitHub Issues**: [Report bugs or request features](https://github.com/101t/jasmin-web-panel/issues)
- **Email**: [tarek.it.eng@gmail.com](mailto:tarek.it.eng@gmail.com)

### Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) before submitting a pull request.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Follow the [coding standards](CONTRIBUTING.md#coding-standards)
4. Write tests for your changes
5. Open a Pull Request using our [PR template](.github/PULL_REQUEST_TEMPLATE.md)

Please also review our [Code of Conduct](CODE_OF_CONDUCT.md) and [Security Policy](SECURITY.md).

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ for the Jasmin SMS Gateway community**

[⬆ Back to Top](#jasmin-web-panel)

</div>
