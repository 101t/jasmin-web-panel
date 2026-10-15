# Kubernetes Deployment

Deploying Jasmin Web Panel on Kubernetes allows for high availability and easy scaling. This guide assumes you have a running Kubernetes cluster and `kubectl` configured.

## Architecture

The deployment consists of:
- **Deployment**: Runs the Django application (Gunicorn).
- **Service**: Exposes the application internally.
- **ConfigMap/Secret**: Manages environment variables.
- **Ingress** (Optional): Exposes the app to the internet.

!!! note "External Dependencies"
    You need to have PostgreSQL, Redis, and a Jasmin SMS Gateway running in your cluster or externally. Update the connection strings in the ConfigMap accordingly.

## 1. Configuration (ConfigMap & Secret)

Create `jasmin-config.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: jasmin-web-config
data:
  DJANGO_SETTINGS_MODULE: "config.settings.pro"
  DEBUG: "False"
  ALLOWED_HOSTS: "sms.example.com"
  CSRF_TRUSTED_ORIGINS: "https://sms.example.com"
  HTTPS_ONLY: "True"            # TLS terminated by the Ingress
  TIME_ZONE: "UTC"
  TELNET_HOST: "jasmin-service" # Service name of your Jasmin Gateway
  TELNET_PORT: "8990"
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
---
apiVersion: v1
kind: Secret
metadata:
  name: jasmin-web-secret
type: Opaque
# stringData takes plain values; Kubernetes encodes them for you.
stringData:
  SECRET_KEY: "change-me-to-a-long-random-value"
  PRODB_URL: "postgres://user:pass@postgres:5432/jasmin"
  TELNET_USERNAME: "jcliadmin"
  TELNET_PW: "jclipwd"
```

## 2. Deployment

Create `jasmin-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jasmin-web
  labels:
    app: jasmin-web
spec:
  replicas: 2
  selector:
    matchLabels:
      app: jasmin-web
  template:
    metadata:
      labels:
        app: jasmin-web
    spec:
      containers:
      - name: web
        image: tarekaec/jasmin_web_panel:3.1.0
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: jasmin-web-config
        - secretRef:
            name: jasmin-web-secret
        # /api/health_check needs no login (other pages redirect to the sign-in page).
        livenessProbe:
          httpGet:
            path: /api/health_check
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health_check
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

!!! note "Health checks and HTTPS_ONLY"
    `/api/health_check` is exempt from the HTTPS redirect, so plain-HTTP probes keep working with `HTTPS_ONLY=True`.

## 3. Celery Worker

You also need a worker deployment for background tasks (submit log exports).

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jasmin-worker
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jasmin-worker
  template:
    metadata:
      labels:
        app: jasmin-worker
    spec:
      containers:
      - name: worker
        image: tarekaec/jasmin_web_panel:3.1.0
        command: ["bash", "./docker-entrypoint-celery.sh"]
        envFrom:
        - configMapRef:
            name: jasmin-web-config
        - secretRef:
            name: jasmin-web-secret
```

## 4. Service

Create `jasmin-service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: jasmin-web
spec:
  selector:
    app: jasmin-web
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

## 5. Apply Configurations

```bash
kubectl apply -f jasmin-config.yaml
kubectl apply -f jasmin-deployment.yaml
kubectl apply -f jasmin-service.yaml
```
