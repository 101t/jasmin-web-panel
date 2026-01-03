# Systemd & Nginx Deployment

For traditional Linux server deployments (Ubuntu/Debian), we recommend running the application with Gunicorn managed by Systemd, and using Nginx as a reverse proxy.

## 1. Systemd Service

Create a service file to keep the application running.

**/etc/systemd/system/jasmin-web.service**

```ini
[Unit]
Description=Jasmin Web Panel
Requires=postgresql.service
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/jasmin-web-panel
Environment="DJANGO_SETTINGS_MODULE=config.settings.pro"
# Ensure you have your virtualenv path correct
ExecStart=/opt/jasmin-web-panel/env/bin/gunicorn \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --timeout 120 \
    --log-level info \
    --access-logfile /opt/jasmin-web-panel/logs/gunicorn.log \
    --error-logfile /opt/jasmin-web-panel/logs/gunicorn_error.log \
    config.wsgi:application
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable jasmin-web
sudo systemctl start jasmin-web
```

## 2. Nginx Configuration

Configure Nginx to proxy requests to Gunicorn and serve static files.

**/etc/nginx/sites-available/jasmin_web**

```nginx
upstream jasmin_web {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name sms.yourdomain.com;

    client_max_body_size 20M;

    # Static Files
    location /static/ {
        alias /opt/jasmin-web-panel/public/static/;
        expires 30d;
    }

    # Proxy to Django
    location / {
        proxy_pass http://jasmin_web;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/jasmin_web /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 3. SSL (Certbot)

Secure your panel with HTTPS:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d sms.yourdomain.com
```
