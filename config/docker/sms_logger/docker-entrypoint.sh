#!/bin/bash

APP_DIR=${APP_DIR:-'/app'}
APP_LOG_LEVEL=${APP_LOG_LEVEL:-'warn'}

# shellcheck disable=SC2164
cd "$APP_DIR"

source "$APP_DIR"/env/bin/activate

"$APP_DIR"/env/bin/python sms_logger.py