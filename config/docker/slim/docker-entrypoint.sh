#!/bin/bash

APP_PORT=${APP_PORT:-8000}
APP_DIR=${APP_DIR:-'/app'}
APP_LOG_LEVEL=${APP_LOG_LEVEL:-'warn'}
# APP_WSGI: 'wsgi' or 'asgi'
APP_WSGI=${APP_WSGI:-'wsgi'}
# APP_WORKER_CLASS: 'gevent' or 'uvicorn.workers.UvicornWorker'
APP_WORKER_CLASS=${APP_WORKER_CLASS:-'sync'}
APP_WORKERS=${APP_WORKERS:-4}

# shellcheck disable=SC2164
cd "$APP_DIR"

source "$APP_DIR"/env/bin/activate

python manage.py migrate
python manage.py load_new
python manage.py collectstatic --noinput --clear --no-post-process

"$APP_DIR"/env/bin/gunicorn config."$APP_WSGI":application \
  --workers "$APP_WORKERS" \
  --bind :"$APP_PORT" \
  --log-level "$APP_LOG_LEVEL" \
  --worker-class="$APP_WORKER_CLASS" \
  --reload