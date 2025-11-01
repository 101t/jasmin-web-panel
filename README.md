# Jasmin Web Panel

<div align="center">

[![Build Status](https://travis-ci.org/101t/jasmin-web-panel.svg?branch=master)](https://travis-ci.org/101t/jasmin-web-panel)
[![Docker Hub](https://img.shields.io/badge/docker-hub-blue.svg)](https://hub.docker.com/u/tarekaec)
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
- **Python**: 3.11 or higher
- **Database**: PostgreSQL 12+ (recommended) or MySQL 8.0+
- **Redis**: 6.0+ (for caching and Celery)
- **RabbitMQ**: 3.10+ (for message queuing)

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
# Edit .env with your settings

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
DEBUG=False  # Always False in production
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

#### 3. Initialize Database

```bash
# Run migrations
python manage.py migrate

# Load sample data (optional)
python manage.py samples

# Collect static files
python manage.py collectstatic --no-input

# Create superuser (optional)
python manage.py createsuperuser
```

#### 4. Run Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

Access the application at `http://localhost:8000`

---

## 🐳 Docker Deployment

### Using Pre-built Image

```bash
# Pull the latest image
docker pull tarekaec/jasmin_web_panel:1.4

# Configure environment
cp sample.env .env
# Edit .env with your settings

# Run container
docker run -d \
  --name jasmin-web \
  -p 8999:8000 \
  --env-file .env \
  -v ./public:/app/public \
  tarekaec/jasmin_web_panel:1.4
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
- `rabbit-mq`: RabbitMQ message broker
- `jasmin`: Jasmin SMS Gateway (ports 2775, 8990, 1401)
- `sms_logger`: SMS submit log collector

#### ARM64/AArch64 Support

For ARM-based systems:

1. Comment out line 38 in `config/docker/slim/Dockerfile`:
   ```dockerfile
   # ENV LD_PRELOAD /usr/lib/x86_64-linux-gnu/libjemalloc.so.2
   ```

2. Start services:
   ```bash
   docker compose up -d
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
| `SUBMIT_LOG` | Enable submit log tracking | `False` | ❌ |

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

#### 2. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable jasmin-web.service
sudo systemctl start jasmin-web.service
sudo systemctl status jasmin-web.service
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

### Cannot connect to Jasmin Gateway

**Solutions**:
- Verify Jasmin is running: `systemctl status jasmin`
- Check telnet connectivity: `telnet localhost 8990`
- Confirm `TELNET_*` settings match Jasmin configuration
- Ensure firewall allows port 8990

### Submit logs not appearing

**Solutions**:
- Verify `SUBMIT_LOG=True` in `.env`
- Check SMS Logger service: `docker compose ps sms_logger`
- Confirm `publish_submit_sm_resp = True` in `jasmin.cfg`
- Check logs: `docker compose logs sms_logger`

### Static files not loading

**Solutions**:
```bash
python manage.py collectstatic --no-input --clear
sudo chown -R www-data:www-data /opt/jasmin-web-panel/public/
sudo nginx -t && sudo systemctl reload nginx
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

We welcome contributions! To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ for the Jasmin SMS Gateway community**

[⬆ Back to Top](#jasmin-web-panel)

</div>
