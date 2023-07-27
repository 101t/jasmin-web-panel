from django.http import JsonResponse

from config.version import VERSION


def health_check(request):
    return JsonResponse({"version": VERSION})
