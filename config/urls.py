from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('jet/', include('jet.urls', namespace="jet")),
    path('jet/dashboard/', include('jet.dashboard.urls', namespace="jet-dashboard")),
    path(settings.ADMIN_URL, admin.site.urls),
    path('account/', include('main.users.urls', namespace="users")),
    path('api/', include('main.api.urls', namespace="api")),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', include('main.web.urls', namespace="web")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)