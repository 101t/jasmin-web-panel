# Jasmin Web Panel
<p>
	<a href="https://travis-ci.org/101t/jasmin-web-panel"><img src="https://travis-ci.org/101t/jasmin-web-panel.svg?branch=master" alt="travis-ci"></a>
</p>

Jasmin SMS Web Interface for Jasmin SMS Gateway

## Getting Started

In your terminal for **Unix** (Linux/Mac)

```sh
pip install virtualenv

git clone https://github.com/101t/jasmin-web-panel --depth 1

cd jasmin-web-panel/

virtualenv -p python3 env

source env/bin/activate

pip install -r requirements.txt

cp -rf Sample.env .env

./load_data.sh --init
```

In Command Prompt for **Windows**

```sh
python -m pip install virtualenv

git clone https://github.com/101t/jasmin-web-panel --depth 1

cd jasmin-web-panel/

virtualenv env

env/Scripts/activate

pip install -r requirements.txt

copy Sample.env .env

load_data_win.bat --init
```

> Note: the `admin` user automatically added to project as default administrator user, the credentials authentication is **Username: `admin`, Password: `secret`**.

## Development

### Prepare Translations

Adding translation made easy by this commands

```sh
cd jasmin-web-panel/main/

django-admin makemessages -l en

django-admin compilemessages
```
> Note: make sure you have `gettext` installed in your `Unix` Environment

```sh
# using gettext in ubuntu or macOS
msgunfmt [django.mo] > [django.po]
```

### Run Celery

To run your celery in development
```sh
celery worker -A main.taskapp -l debug
```

### Run Channels
To run channels in development as `ASGI` using `daphne`
```sh
daphne config.asgi:application -b 0.0.0.0 -p 9000
```

### Run Django
To run django in development as `HTTP` 
```sh
python manage.py runserver 0.0.0.0:8000
```

### Upgrading Packages

Here the following examples how to upgrade some packages

```sh
pip install -U django
pip install -U channels
pip install -U celery
pip install -U djangorestframework markdown django-filter
```
> Note: be careful about sub-packages compatibility and dependencies conflict while **upgrading**
