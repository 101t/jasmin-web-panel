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

To deploy the full stack (Web Panel, Database, Redis, Background Worker), use `docker-compose`.

### 1. Prepare Environment

```bash
cp sample.env .env
# Edit .env and set secure passwords and PRODB_URL
```

### 2. Start Services

```bash
docker compose up -d
```

### 3. Check Status

```bash
docker compose ps
docker compose logs -f jasmin-web
```

## Building Custom Image

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
