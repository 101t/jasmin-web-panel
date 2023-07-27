from django.urls import path
from .views import *

app_name = 'users'

urlpatterns = [
    path(route='profile/', view=profile_view, name='profile_view'),
    path(route='settings/', view=settings_view, name='settings_view'),
    path(route='activity_log/', view=activity_log_view, name='activity_log_view'),
    path(route='login/', view=signin_view, name="signin_view"),
    path(route='logout/', view=logout_view, name="logout_view"),
    path(route='verify-email/<str:uidb64>/<str:token>/', view=email_verification_view, name='email_verification_view'),
    path(route='reset/<str:uidb64>/<str:token>/', view=reset_password_view, name="reset_password_view"),  # noqa
    path(route='reset/', view=reset_view, name="reset_view"),
]
