#!/bin/bash

cd $JASMIN_HOME

python manage.py migrate
python manage.py load_new
python manage.py collectstatic --noinput --clear --no-post-process

/usr/local/bin/gunicorn config.wsgi:application --workers 4 -b :$JASMIN_PORT --log-level info --worker-class=gevent --reload