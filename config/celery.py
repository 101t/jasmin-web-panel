import os
from django.conf import settings
from celery import Celery
from celery.utils.log import get_task_logger

from django.utils import timezone

logger = get_task_logger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery('config')

app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.broker_url = settings.CELERY_BROKER_URL
app.conf.result_backend = settings.CELERY_RESULT_BACKEND
app.conf.broker_connection_max_retries = 0
app.conf.broker_connection_retry_on_startup = True
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, related_name='tasks')

BROKER_CONNECTION_TIMEOUT = 120

CELERY_DEFAULT_UP_TIME = timezone.now()


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.Request))


def revoke_task(task_id):
    app.control.revoke(task_id)


def clear_tasks():
    return app.control.purge()
