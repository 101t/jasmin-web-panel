from django.conf.urls import url
from .views.login import login_view, logout_view
from .views.dashboard import dashboard_view

urlpatterns = [
    url(r'^account/$', login_view, name='login_view'),
    url(r'^logout/$', view=logout_view, name='logout_view',),
    url(r'^dashboard/$', dashboard_view, name='dashboard_view'),
]
