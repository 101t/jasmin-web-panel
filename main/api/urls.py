from rest_framework.urlpatterns import format_suffix_patterns
from django.urls import path, include

from . import views

app_name = 'api'

urlpatterns = format_suffix_patterns([
    path('groups/', include(arg=[
        path('<str:gid>/enable/', view=views.groups_enable, name='groups_enable'),
        path('<str:gid>/disable/', view=views.groups_disable, name='groups_disable'),
        path('<str:gid>/', view=views.groups_detail, name='groups_detail'),
        path('', view=views.groups_list, name='groups_list'),
    ])),
    path('health_check', view=views.health_check, name="health_check")
])
