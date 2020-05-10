<h1 align="center">Django AIO</h1>
<p align="center">
	<img src="https://github.com/101t/django-aio/blob/master/main/static/assets/img/django-aio.png" alt="Django AIO">
</p>
<p>
	<a href="https://travis-ci.org/101t/django-aio"><img src="https://travis-ci.org/101t/django-aio.svg?branch=master" alt="travis-ci"></a>
	<a href='https://coveralls.io/github/101t/django-aio'><img src='https://coveralls.io/repos/github/101t/django-aio/badge.svg' alt='Coverage Status' /></a>
</p>

## Features I thought About

Django AIO (All-In-One) to get project ready to develop with my flavor configurations.

All in one pre-configured and prepared as django project, your project will be ready to use:

1. Django
2. Celery
3. Channels
4. Postgres
5. Redis
6. DRF (Django REST Framework)

Also has some features customization:

1. Custom User
2. Custom sending Mail
3. Sending Notification via channels
4. loggin everything in the system
5. custom sample data loader `python manage.py load_new` and migrations reseter `python manage.py reseter`
6. custom utils functions
7. easy to deployments
8. easy to translate
9. seperating `config/` for configurations and `main/` for all `apps`, `static`, `templates`


## Getting Started

In your terminal for **Unix** (Linux/Mac)

```sh
pip install virtualenv

git clone https://github.com/101t/django-aio --depth 1

cd django-aio/

virtualenv -p python3 env

source env/bin/activate

pip install -r requirements.txt

cp -rf Sample.env .env

./load_data.sh --init
```

In Command Prompt for **Windows**

```sh
python -m pip install virtualenv

git clone https://github.com/101t/django-aio --depth 1

cd django-aio/

virtualenv env

env/Scripts/activate

pip install -r requirements.txt

copy Sample.env .env

load_data_win.bat --init
```

Or using as new project templates

```sh
django-admin.py startproject --template=https://github.com/101t/django-aio/archive/latest.zip --extension=py,gitignore PROJECT_NAME
```

> Note: the `admin` user automatically added to project as default administrator user, the credentials authentication is **Username: `admin`, Password: `secret`**.

## Development

### Prepare Translations

Adding translation made easy by this commands

```sh
cd django-aio/main/

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

## Conclusion

The `django-aio` [Django All-in-One] repository is the result of team collaboration with developing a big web application. It's designed to make quick-starting for the pre-defined installed packages with all nice features to make sure the implementation initialized, these efforts represent predefined goals and base templates for django frameworks and its beautiful 3rd-party packages.