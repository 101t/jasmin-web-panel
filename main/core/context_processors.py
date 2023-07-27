from django.conf import settings

from config.version import VERSION


def site(request):
    return {
        "SETTINGS": settings,
        "VERSION": VERSION,
    }
