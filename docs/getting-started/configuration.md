# Configuration

The application is configured via environment variables. You can define these in a `.env` file in the root directory or export them as system environment variables.

## Core Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode (do not use in production) | `False` |
| `SECRET_KEY` | Django secret key (required in production) | - |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames | `*` |
| `TIME_ZONE` | Server timezone | `Etc/GMT-3` |
| `LANGUAGE_CODE` | Default language code | `en` |

## Database

| Variable | Description | Example |
|----------|-------------|---------|
| `PRODB_URL` | Check the format [dj-database-url](https://github.com/jakarta/dj-database-url) | `postgres://user:pass@host:port/db` |
| `DEVDB_URL` | Development database URL | `sqlite:///db.sqlite3` |

## Redis (Cache & Celery)

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_HOST` | Redis hostname | `redis` |
| `REDIS_PORT` | Redis port | `6379` |
| `REDIS_DB` | Redis database number | `0` |

## Jasmin Gateway Connection

These settings configure how the panel connects to the Jasmin SMS Gateway.

| Variable | Description | Default |
|----------|-------------|---------|
| `TELNET_HOST` | Jasmin Telnet interface host | `127.0.0.1` |
| `TELNET_PORT` | Jasmin Telnet interface port | `8990` |
| `TELNET_USERNAME` | Jasmin admin username | `jcliadmin` |
| `TELNET_PW` | Jasmin admin password | `jclipwd` |

## Feature Flags

| Variable | Description | Default |
|----------|-------------|---------|
| `SUBMIT_LOG` | Enable collecting and viewing submit logs | `False` |
