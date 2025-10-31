from django.urls import path

from main.web import views

app_name = 'web'

urlpatterns = [
    path('filters/manage/', views.filters_view_manage, name='filters_view_manage'),
    path('filters/', views.filters_view, name='filters_view'),
    path('groups/manage/', views.groups_view_manage, name='groups_view_manage'),
    path('groups/', views.groups_view, name='groups_view'),
    path('httpccm/manage/', views.httpccm_view_manage, name='httpccm_view_manage'),
    path('httpccm/', views.httpccm_view, name='httpccm_view'),
    path('morouter/manage/', views.morouter_view_manage, name='morouter_view_manage'),
    path('morouter/', views.morouter_view, name='morouter_view'),
    path('mtrouter/manage/', views.mtrouter_view_manage, name='mtrouter_view_manage'),
    path('mtrouter/', views.mtrouter_view, name='mtrouter_view'),
    path('smppccm/manage/', views.smppccm_view_manage, name='smppccm_view_manage'),
    path('smppccm/', views.smppccm_view, name='smppccm_view'),
    path('send_message/manage/', views.send_message_view_manage, name='send_message_view_manage'),
    path('send_message/', views.send_message_view, name='send_message_view'),
    path('submit_logs/export/', views.submit_logs_export, name='submit_logs_export'),
    path('submit_logs/export/progress/<str:task_id>/', views.submit_logs_export_progress, name='submit_logs_export_progress'),
    path('submit_logs/export/download/<str:task_id>/', views.submit_logs_export_download, name='submit_logs_export_download'),
    path('submit_logs/manage/', views.submit_logs_view_manage, name='submit_logs_view_manage'),
    path('submit_logs/', views.submit_logs_view, name='submit_logs_view'),
    path('users/manage/', views.users_view_manage, name='users_view_manage'),
    path('users/', views.users_view, name='users_view'),
    path('manage/', views.global_manage, name='global_manage'),
    path('', views.dashboard_view, name='dashboard_view'),
]
