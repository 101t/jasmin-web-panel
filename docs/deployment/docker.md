# Docker Deployment

Docker is the easiest way to deploy Jasmin Web Panel. We provide a pre-built image and a Docker Compose setup.

On every start the image runs the database migrations, creates the default `admin` / `secret` account if it does not
exist, collects static files and starts Gunicorn. The panel serves its own static files, so no extra web server is needed
(put one in front for HTTPS).

## Docker Compose (Recommended)

`docker-compose.yml` runs the full stack: the panel, a Celery worker, PostgreSQL, Redis, RabbitMQ, Jasmin itself and the
submit-log consumer.

### 1. Prepare Environment

```bash
cp sample.env .env
nano .env
```

Set at least:

```dotenv
SECRET_KEY=a-long-random-value           # python -c "import secrets; print(secrets.token_urlsafe(50))"
ALLOWED_HOSTS=sms.yourdomain.com,localhost
POSTGRES_PASSWORD=strong_password
PRODB_URL=postgres://jasmin:strong_password@db:5432/jasmin
```

`POSTGRES_*` create the database container; `PRODB_URL` is how the panel connects to it, so keep the two in sync.
Inside the compose network the panel reaches Jasmin as `jasmin` (jcli, SMPP and HTTP API); `docker-compose.yml`
sets those hosts for you.

### 2. Start Services

```bash
docker compose up -d
docker compose ps
```

Open <http://localhost:8999> (or `JASMIN_WEB_PORT`) and sign in with `admin` / `secret`, then change the password.

### 3. Optional: your own admin account

```bash
docker compose exec jasmin-web python manage.py createsuperuser
```

### 4. Logs

```bash
docker compose logs -f jasmin-web
docker compose logs -f jasmin
```

### Ports

| Variable | Service | Default |
|----------|---------|---------|
| `JASMIN_WEB_PORT` | Web panel | `8999` |
| `JASMIN_SMS_PORT` | Jasmin SMPP server | `2775` |
| `JASMIN_DASHBOARD_PORT` | Jasmin jcli | `8990` |
| `JASMIN_HTTP_API_PORT` | Jasmin HTTP API | `1401` |

!!! warning "jcli access"
    The jcli port gives full control of the gateway. Do not expose `8990` to the internet: remove that port mapping
    if you do not need jcli from outside the compose network.

### Jasmin configuration

Jasmin's configuration lives in the `jasmin_config` named volume: it starts from the image's defaults and keeps what
jcli persists (users, connectors, routes) across restarts. To use your own `jasmin.cfg`, copy it in and restart:

```bash
docker compose cp ./jasmin.cfg jasmin:/etc/jasmin/jasmin.cfg
docker compose restart jasmin
```

## Image tags

Images are published to [Docker Hub](https://hub.docker.com/r/tarekaec/jasmin_web_panel) for amd64 and arm64:

| Tag | Content |
|-----|---------|
| `3.1.0` | A release; pin this in production |
| `3.1`, `3` | The latest release of that minor or major version |
| `latest` | The latest release |
| `edge` | The `master` branch; for testing upcoming changes |

## Panel only (existing Jasmin)

If Jasmin already runs elsewhere, run just the panel and point `TELNET_HOST`/`TELNET_PORT` at its jcli port:

```bash
docker run -d \
  --name jasmin-web \
  -p 8999:8000 \
  --env-file .env \
  -v $(pwd)/public:/app/public \
  tarekaec/jasmin_web_panel:3.1.0
```

## Building a Custom Image

If you need to modify the code or dependencies:

```bash
docker build -f config/docker/slim/Dockerfile -t my-jasmin-panel .
```

The Dockerfile builds on both amd64 and arm64 (AWS Graviton, Raspberry Pi) without changes.

## Upgrading

```bash
docker compose pull
docker compose up -d
```

Migrations run automatically when the container starts.

!!! note "Upgrading from a release that used `./jasmin_config`"
    Older compose files bind-mounted `./jasmin_config` over `/etc/jasmin`. If you kept a real Jasmin configuration
    there, copy it into the new volume once (`docker compose cp ./jasmin_config/. jasmin:/etc/jasmin/`) and restart
    Jasmin. If that directory was empty, Jasmin could not start before; nothing needs to be migrated.

## Troubleshooting

If you see PostgreSQL permission errors (e.g., `permission denied for schema public`) on an existing volume:

```bash
docker compose exec db psql -U jasmin -d jasmin -c "GRANT ALL ON SCHEMA public TO jasmin;"
docker compose restart jasmin-web
```

More in [Troubleshooting](../troubleshooting.md).
