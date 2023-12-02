from django.urls import path

from .views import *

app_name = 'web'

urlpatterns = [
    path('filters/manage/', filters_view_manage, name='filters_view_manage'),
    path('filters/', filters_view, name='filters_view'),
    path('groups/manage/', groups_view_manage, name='groups_view_manage'),
    path('groups/', groups_view, name='groups_view'),
    path('httpccm/manage/', httpccm_view_manage, name='httpccm_view_manage'),
    path('httpccm/', httpccm_view, name='httpccm_view'),
    path('morouter/manage/', morouter_view_manage, name='morouter_view_manage'),
    path('morouter/', morouter_view, name='morouter_view'),
    path('mtrouter/manage/', mtrouter_view_manage, name='mtrouter_view_manage'),
    path('mtrouter/', mtrouter_view, name='mtrouter_view'),
    path('smppccm/manage/', smppccm_view_manage, name='smppccm_view_manage'),
    path('smppccm/', smppccm_view, name='smppccm_view'),
    path('submit_logs/manage/', submit_logs_view_manage, name='submit_logs_view_manage'),
    path('submit_logs/', submit_logs_view, name='submit_logs_view'),
    path('users/manage/', users_view_manage, name='users_view_manage'),
    path('users/', users_view, name='users_view'),
    path('manage/', global_manage, name='global_manage'),
    path('send_sms/', send_sms_view, name='send_sms_view'),
    path('', dashboard_view, name='dashboard_view'),
]
