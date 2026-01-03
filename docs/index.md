# Jasmin Web Panel

**Jasmin Web Panel** is a full-featured, modern web interface for the open-source [Jasmin SMS Gateway](https://jasminsms.com/). It provides complete control over your SMS infrastructure with an intuitive UI, advanced logging, and user management.

## Key Features

- **User Management**: Create and manage groups and users with granular permissions.
- **Routing Control**: Manage MO (Mobile Originated) and MT (Mobile Terminated) routes easily.
- **Filter Management**: extensive control over Jasmin filters.
- **SMPP Connection Management**: Configure and monitor SMPP client and server connections.
- **Real-time Logging**: Track message status with the integrated Submit Log Viewer.
- **Billing & Quota**: (Add description if relevant based on inferred features).
- **Modern Dashboard**: Responsive and clean interface built with Django.

## Quick Start

Get up and running in minutes using Docker:

```bash
docker run -d \
  --name jasmin-web \
  -p 8999:8000 \
  --env-file .env \
  tarekaec/jasmin_web_panel:1.4
```

See the [Installation Guide](getting-started/installation.md) for more details.

## Architecture

The panel communicates with the Jasmin SMS Gateway via Telnet for management and uses a shared database/Redis for logs and tasks.

- **Frontend**: HTML/JS served by Django
- **Backend**: Django (Python)
- **Task Queue**: Celery with Redis/RabbitMQ
- **Gateway**: Jasmin SMS Gateway (separate service)
