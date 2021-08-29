# Installing Jasmin SMS Gateway on Ubuntu 20.04 TLS Server

- You need to install `python3.6` version to get Jasmin SMS Gateway works properly.

```shell
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.6 python3.6-dev python3.6-venv
```

## 1. Preparing your system
Login to your machine as a sudo user and update the system to the latest packages:

```shell
sudo apt update && sudo apt -y upgrade
```

Install Git, PIP, NodeJS and the tools required to build dependencies:
```shell
sudo apt install git python3-pip build-essential wget python3-dev python3-venv python3-wheel python3-setuptools libffi-dev libssl-dev python3-twisted virtualenv
```

Install **RabbitMQ** and **Redis server**
```shell
sudo apt install rabbitmq-server redis-server
```

## 2. Create Jasmin user
Create a new system user named jasmin with home directory /jasmin using the following command:
```shell
sudo useradd -m -d /jasmin -U -r -s /bin/bash jasmin
```

## 3. Install and Configure Jasmin
Before starting with the installation process, change to user "jasmin":
```shell
sudo su - jasmin
su ~
```
Create jasmin virtualenv
```shell
virtualenv -p python3.6 jasmin
```
you will get path `/jasmin/jasmin`

Next, activate the environment with the following command:
```shell
source jasmin/bin/activate
```
Install all required Python modules with pip:
```shell
pip install jasmin
```
> Note: If you encounter any compilation errors during the installation, make sure that you installed all of the required dependencies listed in the Before you begin section.


## 4. Create a Systemd Unit File
To run jasmin as a service we need to create a service unit file in the `/etc/systemd/system/` directory.

Open your text editor and paste the following configuration:

### a. Create `jasmind.service` Service

```shell
sudo nano /etc/systemd/system/jasmind.service
```
In directory: /etc/systemd/system/jasmind.service
```editorconfig
[Unit]
Description=Jasmin SMS Gateway
Requires=network.target jasmin-interceptord.service jasmin-dlrd.service jasmin-dlrlookupd.service
After=network.target

[Service]
SyslogIdentifier=jasmind
PIDFile=/run/jasmind.pid
User=jasmin
Group=jasmin
ExecStart=/jasmin/jasmin/bin/jasmind.py --username jcliadmin --password jclipwd

[Install]
WantedBy=multi-user.target
```
### b. Create `jasmin-celery.service` Service

```shell
sudo nano /etc/systemd/system/jasmin-celery.service
```

```editorconfig
[Unit]
Description=Jasmin Celery server
Requires=network.target jasmin-restapi.service
After=network.target
Before=jasmin-restapi.service

[Service]
SyslogIdentifier=jasmin-celery
PIDFile=/run/jasmin-celery.pid
User=jasmin
Group=jasmin
ExecStart=/bin/sh -c "/jasmin/jasmin/bin/celery -A jasmin.protocols.rest.tasks worker -l INFO -c 4 --autoscale=10,3"

[Install]
WantedBy=multi-user.target
```

### c. Create `jasmin-dlrd` Service

```shell
sudo nano /etc/systemd/system/jasmin-dlrd.service
```

```editorconfig
[Unit]
Description=Jasmin SMS Gateway DLR throwing standalone daemon
Requires=network.target jasmind.service
After=network.target jasmind.service

[Service]
SyslogIdentifier=jasmin-dlrd
PIDFile=/run/jasmin-dlrd.pid
User=jasmin
Group=jasmin
ExecStart=/jasmin/jasmin/bin/dlrd.py

[Install]
WantedBy=multi-user.target
```

### d. Create `jasmin-dlrlookupd.service` Service

```shell
sudo nano /etc/systemd/system/jasmin-dlrlookupd.service
```

```editorconfig
[Unit]
Description=Jasmin SMS Gateway DLR lookup standalone daemon
Requires=network.target jasmind.service
After=network.target jasmind.service

[Service]
SyslogIdentifier=jasmin-dlrlookupd
PIDFile=/run/jasmin-dlrlookupd.pid
User=jasmin
Group=jasmin
ExecStart=/jasmin/jasmin/bin/dlrlookupd.py

[Install]
WantedBy=multi-user.target
```

### e. Create `jasmin-interceptord.service` Service

```shell
sudo nano /etc/systemd/system/jasmin-interceptord.service
```

```editorconfig
[Unit]
Description=Jasmin SMS Gateway interceptor
Requires=network.target jasmind.service
After=network.target
Before=jasmind.service

[Service]
SyslogIdentifier=interceptord
PIDFile=/run/interceptord.pid
User=jasmin
Group=jasmin
ExecStart=/jasmin/jasmin/bin/interceptord.py

[Install]
WantedBy=multi-user.target
```

### f. Create `jasmin-restapi.service` Service

Create symlink for twisted main file.
```shell
sudo -u jasmin ln -s /jasmin/jasmin/bin/twistd /jasmin/jasmin/twistd3
```

```shell
sudo nano /etc/systemd/system/jasmin-restapi.service
```

```editorconfig
[Unit]
Description=Jasmin SMS Restful API server
Requires=network.target jasmind.service jasmin-celery.service
After=network.target jasmind.service

[Service]
SyslogIdentifier=jasmin-restapi
PIDFile=/run/jasmin-restapi.pid
User=jasmin
Group=jasmin
ExecStart=/bin/sh -c "/jasmin/jasmin/twistd3 -n --pidfile=/tmp/twistd-web-restapi.pid web --wsgi=jasmin.protocols.rest.api"

[Install]
WantedBy=multi-user.target
```


Reload systemd

```shell
sudo systemctl daemon-reload
```

Now, you can enable Jasmin services:

```shell
systemctl enable jasmin-{celery,dlrd,dlrlookupd,interceptord,restapi}.service jasmind.service
```

You could start all Jasmin services
```shell
systemctl start jasmin-{celery,dlrd,dlrlookupd,interceptord,restapi}.service jasmind.service
```

To ensure web app running without issue:

```shell
systemctl list-unit-files | grep jasmin
```

To check the running and failed daemons:
```shell
systemctl list-units | grep jasmin
```
