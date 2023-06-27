from django.utils import timezone
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.db.models.expressions import F

from main.users.models import User

from datetime import timedelta
from dateutil.parser import parse


class LastUserActivityMiddleware(MiddlewareMixin):
    KEY = "last-activity"

    def process_request(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get(self.KEY)

            # If key is old enough, update database
            too_old_time = timezone.now() - timedelta(seconds=settings.LAST_ACTIVITY_INTERVAL_SECS)
            if not last_activity or parse(last_activity) < too_old_time:
                User.objects.filter(pk=request.user.pk).update(
                    last_login=timezone.now(),
                    login_count=F('login_count') + 1)
            request.session[self.KEY] = timezone.now().isoformat()
        return None
