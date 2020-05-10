from django.db.models import Q
from django.db.models.signals import pre_delete, post_save
from django.dispatch.dispatcher import receiver

from main.notify.models import NotificationRequest

@receiver(post_save, sender=NotificationRequest)
def create_notifications_as_notification_request(sender, instance, created, **kwargs):
	from main.notify.tasks import request_notification_task
	if created:
		request_notification_task.apply_async(args=(instance.pk,), kwargs={}, countdown=1,)
post_save.connect(create_notifications_as_notification_request, sender=NotificationRequest)