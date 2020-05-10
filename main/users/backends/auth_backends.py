from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ImproperlyConfigured
from django.apps import apps

class UserModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        from ..models import User as UserModel
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

    def get_user(self, user_id):
        try:
            return self.user_class.objects.get(pk=user_id)
        except self.user_class.DoesNotExist:
            return None

    @property
    def user_class(self):
        if not hasattr(self, '_user_class'):
            self._user_class = apps.get_model(*settings.AUTH_USER_MODEL.split('.', 2))
            if not self._user_class:
                raise ImproperlyConfigured('Could not get auth user model')
        return self._user_class
    # def user_can_authenticate(self, user):
    #     return True