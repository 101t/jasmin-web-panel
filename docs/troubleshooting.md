# Troubleshooting

## The panel cannot reach Jasmin

The tables show the reason instead of staying empty.

**"Could not connect to Jasmin jcli at HOST:PORT. Is the gateway running and reachable?"**

- Check that Jasmin runs: `systemctl status jasmin` or `docker compose ps jasmin`.
- Check `TELNET_HOST` / `TELNET_PORT` in `.env`. With Docker Compose, the host is `jasmin`.
- Test from the panel host: `telnet TELNET_HOST 8990` should show a `Username:` prompt.
- On manual installs, install the telnet client the panel uses: `sudo apt install telnet`.

**"Jasmin jcli login failed, check TELNET_USERNAME and TELNET_PW"**

The jcli credentials are wrong. Jasmin's defaults are `jcliadmin` / `jclipwd` (`[jcli]` section of `jasmin.cfg`).

**"Connection to Jasmin jcli at HOST:PORT timed out"** or **"Jasmin did not answer … in time"**

The gateway is slow or overloaded. Raise `TELNET_TIMEOUT` (seconds) if it happens regularly.

## A change is refused

The message comes from Jasmin itself, prefixed with the field it rejected, for example
`gid: Unknown Group gid:partners, you must first create the Group`. Common cases:

| Message | Fix |
|---------|-----|
| `... already exists` | Pick another id: adding an existing id would overwrite that object in Jasmin |
| `Unknown Group gid:...` | Create the group first |
| `UserFilter#... is not a valid filter for MORoute` | User and group filters only work on MT routes |
| `FailoverMORoute cannot have mixed connector types` | Use only HTTP connectors or only SMPP users in a failover MO route |
| `... requires at least two connectors` | Round robin and failover routes need two or more connectors |
| `HttpConnector url syntax is invalid` | Use a full URL, e.g. `https://example.com/receive` |

## "Your session has expired, please sign in again"

The panel sends you to the sign-in page and back to where you were. Sign in again.

## Cannot sign in with an account made by `createsuperuser`

Older releases saved such accounts with an unverified email, which the sign-in page refuses. Mark them verified:

```bash
python manage.py shell -c "from main.users.models import User; User.objects.filter(is_superuser=True).update(is_email=True, is_verified=True)"
```

## Pages have no styling

Static files are served by the panel once collected. The Docker image collects them on start; on manual installs run:

```bash
python manage.py collectstatic --no-input
```

Behind Nginx, check that the `/static/` location points at `public/static/`.

## CSRF verification failed

Behind a reverse proxy on another host, port or scheme, list the public address in `CSRF_TRUSTED_ORIGINS`, e.g.
`CSRF_TRUSTED_ORIGINS=https://sms.example.com`.

## `permission denied for schema public` during migrations

PostgreSQL 15+ no longer lets every user create tables in the `public` schema. As a PostgreSQL superuser:

```sql
\c your_db_name
GRANT USAGE, CREATE ON SCHEMA public TO your_db_user;
```

## Submit logs do not appear

- Set `SUBMIT_LOG=True` in `.env`.
- Enable `publish_submit_sm_resp = True` in the `[sm-listener]` section of `jasmin.cfg` and restart Jasmin.
- Check the consumer: `docker compose logs sms_logger`.

## Logs

```bash
docker compose logs -f jasmin-web    # Docker
tail -f logs/app.log logs/django.log # manual installs (production settings)
```
