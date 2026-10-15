from django.utils.translation import gettext as _
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from main.core.tools import require_post_ajax
from main.core.smpp import Filters


@login_required
def filters_view(request):
    context = {
        "filter_types": Filters.FILTER_TYPES,
    }
    return render(request, "web/content/filters.html", context)


@require_post_ajax
def filters_view_manage(request):
    s = request.POST.get("s")
    with Filters() as filters:
        if s == "list":
            response = filters.list()
        elif s == "add":
            response = filters.create(data={
                "fid": request.POST.get("fid"),
                "type": request.POST.get("type"),
                "parameter": request.POST.get("parameter"),
            })
            response["message"] = _("Filter added successfully!")
        elif s == "delete":
            response = filters.destroy(fid=request.POST.get("fid"))
            response["message"] = _("Filter deleted successfully!")
        else:
            return JsonResponse({"message": _("Sorry, Command does not matched."), "status": 400}, status=400)

    response["status"] = 200
    return JsonResponse(response, status=200)
