import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.pro")

# Setup Django before importing any Django modules
django.setup()

from django.conf import settings
from celery import Celery
from celery.utils.log import get_task_logger
from django.utils import timezone

logger = get_task_logger(__name__)
CELERY_BROKER_URL = settings.REDIS_URL
CELERY_RESULT_BACKEND = settings.REDIS_URL


app = Celery('config')

app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.broker_url = CELERY_BROKER_URL
app.conf.result_backend = CELERY_RESULT_BACKEND
app.conf.broker_connection_max_retries = 0
app.conf.broker_connection_retry_on_startup = True
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, related_name='tasks')

# Close database connections after each task to prevent leaks
from django.db import connection
from celery.signals import task_postrun, task_prerun

@task_prerun.connect
def task_prerun_handler(sender=None, **kwargs):
    """Close database connections before task starts."""
    connection.close()

@task_postrun.connect
def task_postrun_handler(sender=None, **kwargs):
    """Close database connections after task completes."""
    connection.close()

BROKER_CONNECTION_TIMEOUT = 120

CELERY_DEFAULT_UP_TIME = timezone.now()


@app.task(bind=True)
def debug_task(self):
    logger.info("Request: {0!r}".format(self.Request))


def revoke_task(task_id):
    app.control.revoke(task_id)


def clear_tasks():
    return app.control.purge()
