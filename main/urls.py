"""main URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django import views
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.views.generic.base import RedirectView
from rest_framework.routers import DefaultRouter

from main.apps.core.views import (
    GroupViewSet, UserViewSet, MORouterViewSet, SMPPCCMViewSet, HTTPCCMViewSet, MTRouterViewSet, FiltersViewSet
)

router = DefaultRouter()
router.register(r'groups', GroupViewSet, base_name='groups')
router.register(r'users', UserViewSet, base_name='users')
router.register(r'morouters', MORouterViewSet, base_name='morouters')
router.register(r'mtrouters', MTRouterViewSet, base_name='mtrouters')
router.register(r'smppsconns', SMPPCCMViewSet, base_name='smppcons')
router.register(r'httpsconns', HTTPCCMViewSet, base_name='httpcons')
router.register(r'filters', FiltersViewSet, base_name='filters')

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^administration/', include('main.apps.administration.urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/', include(router.urls)),
    url(r'^', include('main.apps.account.urls')),

    url(r'^$', RedirectView.as_view(url='/account',permanent=False),name='index'),
]

if settings.SHOW_SWAGGER:
    #urlpatterns += [url(r'^docs/', include('rest_framework_swagger.urls'))]
    from rest_framework_swagger.views import get_swagger_view
    schema_view = get_swagger_view(title='Pastebin API', url='/api')
    urlpatterns += [url(r'^docs/', schema_view),]
    # from main.apps.core.views.schema import SwaggerSchemaView
    # urlpatterns += [url(r'^docs/', SwaggerSchemaView.as_view()),]