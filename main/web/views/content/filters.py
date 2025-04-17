from django.utils.translation import gettext as _
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from main.core.tools import require_post_ajax
from main.core.smpp import Filters


@login_required
def filters_view(request):
    return render(request, "web/content/filters.html")


@require_post_ajax
def filters_view_manage(request):
    filters = Filters()
    s = request.POST.get("s")
    if s == "list":
        response = filters.list()
    elif s == "add":
        response = filters.create(
            fid=request.POST.get("fid"),
            type=request.POST.get("type"),
            parameter=request.POST.get("parameter"),
        )
        response["message"] = str(_("Filter added successfully!"))
    elif s == "delete":
        response = filters.destroy(fid=request.POST.get("fid"))
        response["message"] = str(_("Filter deleted successfully!"))
    else:
        return JsonResponse({"message": str(_("Sorry, Command does not matched.")), "status": 400}, status=400)

    response["status"] = 200
    return JsonResponse(response, status=200)
