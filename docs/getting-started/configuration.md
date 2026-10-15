# Configuration

The application is configured via environment variables. You can define these in a `.env` file in the root directory or export them as system environment variables. Start from `sample.env`:

```bash
cp sample.env .env
```

Boolean values accept `True`/`False` (also `1`/`0`, `yes`/`no`).

## Core Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.pro` (PostgreSQL, file logging) or `config.settings.dev` (SQLite) | `config.settings.pro` in Docker |
| `DEBUG` | Enable debug mode. Never in production: it shows source code and settings on errors | `False` |
| `SECRET_KEY` | Django secret key; **required in production**. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(50))"` | insecure sample value |
| `ALLOWED_HOSTS` | Comma-separated list of hostnames the panel answers to | `*` |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated origins allowed to submit forms, e.g. `https://sms.example.com`; needed behind a reverse proxy on another host or port | empty |
| `HTTPS_ONLY` | Serve over HTTPS only: secure cookies, HTTP → HTTPS redirect, trusts `X-Forwarded-Proto` from your proxy | `False` |
| `SECURE_HSTS_SECONDS` | HSTS max-age when `HTTPS_ONLY` is on (read the Django docs before enabling) | `0` |
| `TIME_ZONE` | Server timezone | `UTC` |
| `LANGUAGE_CODE` | Default language code (`en`, `tr`) | `en` |
| `ADMIN_URL` | Path of the Django admin | `admin/` |
| `SITE_ID` | Django sites framework id | `1` |
| `SITE_NAME` / `SITE_NAME_HTML` | Name shown in the interface | `Jasmin Panel` |
| `DJANGO_LOG_LEVEL` | Log level of `logs/app.log` and `logs/django.log` (production settings) | `WARNING` |

!!! warning "Production checklist"
    Set `DEBUG=False`, a long random `SECRET_KEY`, your real `ALLOWED_HOSTS`, and change the default `admin` / `secret`
    account. When the panel is served over HTTPS, also set `HTTPS_ONLY=True`.

## Database

| Variable | Description | Example |
|----------|-------------|---------|
| `PRODB_URL` | Database used by `config.settings.pro`, in [django-environ URL format](https://django-environ.readthedocs.io/en/latest/types.html#environ-env-db-url) | `postgres://user:pass@host:5432/db` |
| `DEVDB_URL` | Database used by `config.settings.dev` | `sqlite:///db.sqlite3` |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Docker Compose only: creates the `db` service. Keep them in sync with `PRODB_URL` | `jasmin` |

## Redis (Cache & Celery)

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_HOST` | Redis hostname | `redis` |
| `REDIS_PORT` | Redis port | `6379` |
| `REDIS_DB` | Redis database number | `0` |
| `REDIS_PASSWORD` | Redis password, if any | empty |

## Jasmin Gateway Connection

The panel manages Jasmin through its jcli console. On manual installs, the `telnet` client must be installed on the
panel host (`apt install telnet`); the Docker image already includes it.

| Variable | Description | Default |
|----------|-------------|---------|
| `TELNET_HOST` | Jasmin jcli host | `127.0.0.1` |
| `TELNET_PORT` | Jasmin jcli port | `8990` |
| `TELNET_USERNAME` | jcli admin username | `jcliadmin` |
| `TELNET_PW` | jcli admin password | `jclipwd` |
| `TELNET_TIMEOUT` | Seconds to wait for a jcli answer | `10` |

## Send SMS

The **Send SMS** page sends test messages through Jasmin's HTTP API or SMPP server. Users created from the panel send
with their own credentials; otherwise these defaults are used.

| Variable | Description | Default |
|----------|-------------|---------|
| `HTTP_HOST` / `HTTP_PORT` | Jasmin HTTP API | `http://127.0.0.1` / `1401` |
| `HTTP_USERNAME` / `HTTP_PASSWORD` | Default HTTP API credentials | `jasmin_user` / `jasmin_pass` |
| `SMPP_HOST` / `SMPP_PORT` | Jasmin SMPP server | `127.0.0.1` / `2775` |
| `SMPP_SYSTEM_ID` / `SMPP_PASSWORD` | Default SMPP credentials | `jasmin_user` / `jasmin_pass` |

## REST API

| Variable | Description | Default |
|----------|-------------|---------|
| `API_THROTTLE_ANON` | Rate limit for anonymous requests | `20/minute` |
| `API_THROTTLE_USER` | Rate limit for authenticated requests | `120/minute` |

## Feature Flags

| Variable | Description | Default |
|----------|-------------|---------|
| `SUBMIT_LOG` | Enable collecting and viewing submit logs (see [Submit Log](../features/submit-log.md)) | `False` |
