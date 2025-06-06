# Jasmin Web Panel

<p>
	<a href="https://travis-ci.org/101t/jasmin-web-panel"><img src="https://travis-ci.org/101t/jasmin-web-panel.svg?branch=master" alt="travis-ci"></a>
</p>

Jasmin Web Application to manage [Jasmin SMS Gateway](https://github.com/jookies/jasmin)

### Table Of Contents:

1. [Installing and Deployment](#installing-and-deployment)
    - [Installation](#installation)
    - [Deployment with NGiNX and Systemd](#deployment-with-nginx-and-systemd)
    - [Deployment using Docker](#deployment-using-docker)
    - [Submit Log](#submit-log)
2. [Release Notes](#release-notes)
3. [Tracking Issue](#tracking-issue)
4. [Contact Us](#contacts)

## Installing and Deployment

Before starting please make sure you have installed and running [Jasmin SMS Gateway](http://docs.jasminsms.com/en/latest/installation/index.html) on your server.

### Installation

Download and Extract folder We recommended installing python dependencies in `virtualenv`

Install dependencies:

> This version using `python >= 3.11` make sure you have installed on your system.

go to `jasmin-web-panel/` and run

```sh
cd jasmin-web-panel/
pip install --upgrade pip wheel uv
uv pip install -r pyproject.toml --extra=prod
cp sample.env .env
```

Preparing your `database` by running migrate commads:

```sh
python manage.py migrate
python manage.py samples
python manage.py collectstatic --no-input
```

These commands used in production server, also you may edit **Jasmin SMS Gateway** credential connection

```sh
TELNET_HOST=127.0.0.1
TELNET_PORT=8990
TELNET_USERNAME=jcliadmin
TELNET_PW=jclipwd
TELNET_TIMEOUT=10
```

for production make sure `DEBUG=False` in `.env` file to ensure security.
You may run project manually

```sh
python manage.py runserver
```

### Deployment with `NGiNX and Systemd`

> Make sure you have installed `gunicorn` using `pip`.

Navigate to `/etc/systemd/system` and create new service called `jasmin-web.service`

```ini
[Unit]
Description=Jasmin Web Panel
Requires=postgresql.service
After=network.target postgresql.service

[Service]
Type=simple
SyslogIdentifier=jasminwebpanel
PermissionsStartOnly=true
User=username
Group=username
Environment="DJANGO_SETTINGS_MODULE=config.settings.pro"
WorkingDirectory=/opt/jasmin-web-panel
ExecStart=/opt/jasmin-web-panel/env/bin/gunicorn --bind 127.0.0.1:8000 config.wsgi -w 3 --timeout=120 --log-level=info
StandardOutput=file:/opt/jasmin-web-panel/logs/gunicorn.log
StandardError=file:/opt/jasmin-web-panel/logs/gunicorn_error.log
StandardOutput=journal+console
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Reload systemd

```sh
sudo systemctl daemon-reload
```

Now, you can do:

```sh
sudo systemctl enable jasmin-web.service
sudo systemctl start jasmin-web.service
```

To ensure web app running without issue:

```sh
sudo systemctl status jasmin-web.service
```

For NGiNX go to `/etc/nginx/sites-available` and create a new file `jasmin_web`

```nginx
upstream jasmin_web{
    server 127.0.0.1:8000;
}

server {
    listen 80;
    charset utf-8;
    # server_name sms.example.com;
    server_name _; # for IP Address access
    client_body_timeout 500;
    client_header_timeout 500;
    keepalive_timeout 500 500;
    send_timeout 30;
    access_log /var/log/nginx/jasmin_web_access.log combined;
    error_log /var/log/nginx/jasmin_web_error.log;

    location / {
        proxy_pass http://jasmin_web;
        proxy_http_version 1.1;
        proxy_read_timeout 86400;
        proxy_redirect     off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_max_temp_file_size 1600m;
        proxy_buffering off;
        proxy_request_buffering on;
        client_max_body_size 20M;
        client_body_buffer_size  256K;
    }

    location ^~ /media/ {
        root /opt/jasmin-web-panel/public/;
        add_header Accept-Ranges bytes;
    }
    location ^~ /static/ {
        root /opt/jasmin-web-panel/public/;
        add_header Pragma public;
        add_header Cache-Control "public";
        expires 30d;
    }
}
```

> Note: Don't forget to replace `sms.example.com` with your real domain

Once you are done, test and restart the Nginx Service with:

```sh
ln -s /etc/nginx/sites-available/jasmin_web /etc/nginx/sites-enabled/jasmin_web
sudo nginx -t
sudo nginx -s reload
# or sudo service nginx restart
# or sudo systemctl restart nginx
```

### Login information:

```shell
Username: admin
Password: secret  # please change the default password to avoid the security issue
```

## Deployment using Docker

You could download the built image on [docker hub](https://hub.docker.com/u/tarekaec):

```shell
docker pull tarekaec/jasmin_web_panel
```

also, you could build it on your local machine by navigating to the project directory

```shell
docker build -f config/docker/slim/Dockerfile -t jasmin_web_panel:latest .
```

You need to configure the environment variable in `.env` file

```shell
DJANGO_SETTINGS_MODULE=config.settings.pro
PRODB_URL=postgres://username:strong_password@postgre_hostname:5432/jasmin_web_db
```

to start docker container

```shell
docker stack deploy -c docker-compose.yml jasmin1
```

you could check service on terminal

```shell
docker service ls | grep jasmin
```

## Deployment using Docker Compose (Works with AArch64 or ARM64)

You need to configure the environment variable in `.env` file
You also need to comment line 38 of "config/docker/slim/Dockerfile" (ENV LD_PRELOAD /usr/lib/x86_64-linux-gnu/libjemalloc.so.2) 
Then start docker container in detach mode. You can remove "-d" if you want to see logs
```
docker compose up -d
```

Then check docker containers
```
docker ps
```

## Submit Log

To work with Submit Log you need to install and configure [Submit Log](https://github.com/101t/jasmin-submit-logs) service, make sure you have `SUBMIT_LOG` (default `False`) in environment variable:

```shell
SUBMIT_LOG=True
```

## Tracking Issue

You may submit issue [here](https://github.com/101t/jasmin-web-panel/issues)

## Contacts

For question and suggestion: [tarek.it.eng@gmail.com](mailto:tarek.it.eng@gmail.com), Join Telegram Channel: [https://t.me/jasminwebpanel](https://t.me/jasminwebpanel), all suggestion and questions are welcomed.
