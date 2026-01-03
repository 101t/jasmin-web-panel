# Kubernetes Deployment

Deploying Jasmin Web Panel on Kubernetes allows for high availability and easy scaling. This guide assumes you have a running Kubernetes cluster and `kubectl` configured.

## Architecture

The deployment consists of:
- **Deployment**: Runs the Django application (Gunicorn/Uvicorn).
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
  DEBUG: "False"
  ALLOWED_HOSTS: "*"
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
data:
  # Base64 encoded values
  SECRET_KEY: "CHANGE_ME_TO_BASE64_ENCODED_KEY"
  PRODB_URL: "cG9zdGdyZXM6Ly91c2VyOnBhc3NAcG9zdGdyZXM6NTQzMi9qYXNtaW4=" # postgres://...
  TELNET_PW: "amRsaXB3ZA==" # jclipwd
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
        image: tarekaec/jasmin_web_panel:1.4
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: jasmin-web-config
        - secretRef:
            name: jasmin-web-secret
        livenessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## 3. Celery Worker

You also need a worker deployment for background tasks.

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
        image: tarekaec/jasmin_web_panel:1.4
        command: ["celery", "-A", "config", "worker", "-l", "info"]
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
