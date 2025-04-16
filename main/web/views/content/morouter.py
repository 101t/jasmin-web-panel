from django.utils.translation import gettext as _
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required

import json

from main.core.smpp import MORouter
from main.core.tools import require_ajax


@login_required
def morouter_view(request):
    return render(request, "web/content/morouter.html")


@require_ajax
def morouter_view_manage(request):
    response = {}
    s = request.POST.get("s")
    morouter = MORouter(telnet=request.telnet)

    if s == "list":
        response = morouter.list()
    elif s == "add":
        try:
            morouter.create(data=dict(
                type=request.POST.get("type"),
                order=request.POST.get("order"),
                smppconnectors=request.POST.get("smppconnectors"),
                httpconnectors=request.POST.get("httpconnectors"),
                filters=request.POST.get("filters"),
            ))
            response["message"] = str(_("MO Router added successfully!"))
        except Exception as e:
            return JsonResponse({"message": str(e), "status": 400}, status=400)
    elif s == "delete":
        response = morouter.destroy(order=request.POST.get("order"))
        response["message"] = str(_("MO Router deleted successfully!"))
    else:
        return JsonResponse({"message": str(_("Sorry, Command does not matched.")), "status": 400}, status=400)
    response["status"] = 200
    return JsonResponse(response)
