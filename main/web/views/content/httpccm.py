from django.utils.translation import gettext as _
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from main.core.smpp import HTTPCCM
from main.core.tools import require_post_ajax


@login_required
def httpccm_view(request):
    return render(request, "web/content/httpccm.html")


@require_post_ajax
def httpccm_view_manage(request):
    response = {}
    httpccm = HTTPCCM()
    s = request.POST.get("s")
    if s == "list":
        response = httpccm.list()
    elif s == "add":
        httpccm.create(data=dict(
            cid=request.POST.get("cid"),
            url=request.POST.get("url"),
            method=request.POST.get("method"),
        ))
        response["message"] = str(_("HTTPCCM added successfully!"))
    elif s == "delete":
        response = httpccm.destroy(cid=request.POST.get("cid"))
        response["message"] = str(_("HTTPCCM deleted successfully!"))
    else:
        return JsonResponse({"message": str(_("Sorry, Command does not matched.")), "status": 400}, status=400)

    response["status"] = 200
    return JsonResponse(response, status=200)
