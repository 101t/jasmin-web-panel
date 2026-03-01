# Jasmin Web Panel

**Jasmin Web Panel** is a full-featured, modern web interface for the open-source [Jasmin SMS Gateway](https://jasminsms.com/). It provides complete control over your SMS infrastructure with an intuitive UI, advanced logging, and user management.

## Video Overview

Watch the quick-start walkthrough to see Jasmin Web Panel in action:

<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%;">
  <iframe
    src="https://www.youtube.com/embed/z-BFJzWtq1M"
    title="Jasmin Web Panel – Quick Start"
    frameborder="0"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
    allowfullscreen
    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
  </iframe>
</div>

> Prefer a direct link? Watch on YouTube: <https://youtu.be/z-BFJzWtq1M>

## Key Features

- **User Management**: Create and manage groups and users with granular permissions.
- **Routing Control**: Manage MO (Mobile Originated) and MT (Mobile Terminated) routes easily.
- **Filter Management**: Extensive control over Jasmin filters.
- **SMPP Connection Management**: Configure and monitor SMPP client and server connections.
- **Real-time Logging**: Track message status with the integrated Submit Log Viewer.
- **Billing & Quota**: Per-user balance management and rate-limiting.
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

See the [Installation Guide](getting-started/installation.md) for full setup options including [Docker](deployment/docker.md) and [Systemd & Nginx](deployment/systemd-nginx.md).

## Architecture

The panel communicates with the Jasmin SMS Gateway via Telnet for management and uses a shared database/Redis for logs and tasks.

- **Frontend**: HTML/JS served by Django
- **Backend**: Django (Python 3.11+)
- **Task Queue**: Celery with Redis/RabbitMQ
- **Database**: PostgreSQL (recommended) or SQLite for development
- **Gateway**: Jasmin SMS Gateway (separate service)
