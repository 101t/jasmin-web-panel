from django.conf.urls import url
from .views.smppccm import smppccm_view, smppccm_view_manage
from .views.httpccm import httpccm_view, httpccm_view_manage
from .views.users import users_view, users_view_manage
from .views.groups import groups_view, groups_view_manage
from .views.filters import filters_view, filters_view_manage
from .views.mtrouter import mtrouter_view, mtrouter_view_manage
from .views.morouter import morouter_view, morouter_view_manage
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
	url(r'^smppccm/manage/$', smppccm_view_manage, name='smppccm_view_manage'),
	url(r'^smppccm/$', smppccm_view, name='smppccm_view'),
	url(r'^httpccm/manage/$', httpccm_view_manage, name='httpccm_view_manage'),
	url(r'^httpccm/$', httpccm_view, name='httpccm_view'),
	url(r'^users/manage/$', users_view_manage, name='users_view_manage'),
	url(r'^users/$', users_view, name='users_view'),
	url(r'^groups/manage/$', groups_view_manage, name='groups_view_manage'),
	url(r'^groups/$', groups_view, name='groups_view'),
	url(r'^filters/manage/$', filters_view_manage, name='filters_view_manage'),
	url(r'^filters/$', filters_view, name='filters_view'),
	url(r'^mtrouter/manage/$', mtrouter_view_manage, name='mtrouter_view_manage'),
	url(r'^mtrouter/$', mtrouter_view, name='mtrouter_view'),
	url(r'^morouter/manage/$', morouter_view_manage, name='morouter_view_manage'),
	url(r'^morouter/$', morouter_view, name='morouter_view'),
]