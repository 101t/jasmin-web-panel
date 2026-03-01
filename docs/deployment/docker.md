# Docker Deployment

Docker is the easiest way to deploy Jasmin Web Panel. We provide a pre-built image and a Docker Compose setup.

## Quick Run

```bash
docker run -d \
  --name jasmin-web \
  -p 8999:8000 \
  --env-file .env \
  -v $(pwd)/public:/app/public \
  tarekaec/jasmin_web_panel:1.4
```

## Docker Compose (Recommended)

To deploy the full stack (Web Panel, Database, Redis, Background Worker), use `docker compose`.

### 1. Prepare Environment

```bash
cp sample.env .env
# Edit .env and set secure passwords, SECRET_KEY, and PRODB_URL
nano .env
```

Key variables to set:

```dotenv
DEBUG=False
SECRET_KEY=your-very-secret-key-here
ALLOWED_HOSTS=sms.yourdomain.com,localhost
PRODB_URL=postgres://jasmin_user:strong_password@postgres:5432/jasmin_db
REDIS_HOST=redis
REDIS_PORT=6379
TELNET_HOST=jasmin
TELNET_PORT=8990
```

### 2. Start Services

```bash
docker compose up -d
```

### 3. Run Database Migrations

After the containers start, run the database migrations:

```bash
docker compose exec jasmin-web python manage.py migrate
```

If you see permission errors related to PostgreSQL (e.g., `permission denied for schema public`), connect to the database and grant privileges:

```bash
docker compose exec postgres psql -U postgres -c "GRANT ALL ON SCHEMA public TO jasmin_user;"
docker compose exec postgres psql -U postgres -c "ALTER SCHEMA public OWNER TO jasmin_user;"
```

Then re-run migrations:

```bash
docker compose exec jasmin-web python manage.py migrate
```

### 4. Create an Admin User

```bash
docker compose exec jasmin-web python manage.py createsuperuser
```

### 5. Collect Static Files

```bash
docker compose exec jasmin-web python manage.py collectstatic --noinput
```

### 6. Check Status

```bash
docker compose ps
docker compose logs -f jasmin-web
```

## Building a Custom Image

If you need to modify the code or dependencies:

```bash
# Build the image
docker build -f config/docker/slim/Dockerfile -t my-jasmin-panel .

# Run it
docker run -d \
  --name jasmin-web \
  -p 8999:8000 \
  --env-file .env \
  my-jasmin-panel
```

## ARM64 / AArch64 Support

If you are deploying on ARM architecture (e.g., AWS Graviton, Raspberry Pi):

1. Edit `config/docker/slim/Dockerfile`
2. Comment out or remove the x86 specific preload:
   ```dockerfile
   # ENV LD_PRELOAD /usr/lib/x86_64-linux-gnu/libjemalloc.so.2
   ```
3. Rebuild or run `docker compose up -d` (if building locally).

## Upgrading

When upgrading to a newer version, always run migrations after pulling the new image:

```bash
docker compose pull
docker compose up -d
docker compose exec jasmin-web python manage.py migrate
```
