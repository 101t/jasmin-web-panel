#!/bin/bash

set -e

APP_PORT=${APP_PORT:-8000}
APP_DIR=${APP_DIR:-'/app'}
APP_LOG_LEVEL=${APP_LOG_LEVEL:-'warn'}

APP_WSGI=${APP_WSGI:-'wsgi'}

APP_WORKER_CLASS=${APP_WORKER_CLASS:-'sync'}
APP_WORKERS=${APP_WORKERS:-4}

cd "$APP_DIR"

# Optional (not strictly needed if PATH is set in Dockerfile)
source "$APP_DIR"/env/bin/activate

python manage.py migrate
python manage.py samples
python manage.py collectstatic --noinput --clear

exec "$APP_DIR"/env/bin/gunicorn config."$APP_WSGI":application \
  --workers "$APP_WORKERS" \
  --bind :"$APP_PORT" \
  --log-level "$APP_LOG_LEVEL" \
  --worker-class="$APP_WORKER_CLASS" \
  --reload