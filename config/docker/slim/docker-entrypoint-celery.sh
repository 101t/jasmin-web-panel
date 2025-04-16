#!/bin/bash

set -e

APP_DIR=${APP_DIR:-'/app'}
CELERY_LOG_LEVEL=${CELERY_LOG_LEVEL:-'warning'}

# shellcheck disable=SC2164
cd "$APP_DIR"

source "$APP_DIR"/env/bin/activate

"$APP_DIR"/env/bin/celery --app config worker --max-tasks-per-child 1 -l "$CELERY_LOG_LEVEL"
