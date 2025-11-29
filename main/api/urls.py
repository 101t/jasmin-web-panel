from rest_framework.urlpatterns import format_suffix_patterns
from django.urls import path, include

from . import views

app_name = 'api'

urlpatterns = format_suffix_patterns([
    # API Root
    path('', view=views.api_root, name='api_root'),
    # Groups
    path('groups/', include(arg=[
        path('<str:gid>/enable/', view=views.groups_enable, name='groups_enable'),
        path('<str:gid>/disable/', view=views.groups_disable, name='groups_disable'),
        path('<str:gid>/', view=views.groups_detail, name='groups_detail'),
        path('', view=views.groups_list, name='groups_list'),
    ])),
    # Users
    path('users/', include(arg=[
        path('<str:uid>/enable/', view=views.users_enable, name='users_enable'),
        path('<str:uid>/disable/', view=views.users_disable, name='users_disable'),
        path('<str:uid>/', view=views.users_detail, name='users_detail'),
        path('', view=views.users_list, name='users_list'),
    ])),
    # Filters
    path('filters/', include(arg=[
        path('<str:fid>/', view=views.filters_detail, name='filters_detail'),
        path('', view=views.filters_list, name='filters_list'),
    ])),
    # HTTP Client Connectors
    path('httpccm/', include(arg=[
        path('<str:cid>/', view=views.httpccm_detail, name='httpccm_detail'),
        path('', view=views.httpccm_list, name='httpccm_list'),
    ])),
    # SMPP Client Connectors
    path('smppccm/', include(arg=[
        path('<str:cid>/start/', view=views.smppccm_start, name='smppccm_start'),
        path('<str:cid>/stop/', view=views.smppccm_stop, name='smppccm_stop'),
        path('<str:cid>/', view=views.smppccm_detail, name='smppccm_detail'),
        path('', view=views.smppccm_list, name='smppccm_list'),
    ])),
    # MO Routers
    path('morouter/', include(arg=[
        path('flush/', view=views.morouter_flush, name='morouter_flush'),
        path('<str:order>/', view=views.morouter_detail, name='morouter_detail'),
        path('', view=views.morouter_list, name='morouter_list'),
    ])),
    # MT Routers
    path('mtrouter/', include(arg=[
        path('flush/', view=views.mtrouter_flush, name='mtrouter_flush'),
        path('<str:order>/', view=views.mtrouter_detail, name='mtrouter_detail'),
        path('', view=views.mtrouter_list, name='mtrouter_list'),
    ])),
    # Health Check
    path('health_check', view=views.health_check, name="health_check")
])
