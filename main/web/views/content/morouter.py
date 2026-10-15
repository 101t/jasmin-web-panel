from django.utils.translation import gettext as _
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from main.core.smpp import MORouter
from main.core.tools import require_post_ajax


@login_required
def morouter_view(request):
    context = {
        "mo_router_types": MORouter.MO_ROUTER_TYPES,
    }
    return render(request, "web/content/morouter.html", context)


@require_post_ajax
def morouter_view_manage(request):
    response = {}
    s = request.POST.get("s")
    with MORouter() as morouter:
        if s == "list":
            response = morouter.list()
        elif s == "add":
            # Multi-selects post one value per selected option; .get() would keep only the last.
            response = morouter.create(data=dict(
                type=request.POST.get("type"),
                order=request.POST.get("order"),
                smppconnectors=request.POST.getlist("smppconnectors"),
                httpconnectors=request.POST.getlist("httpconnectors"),
                filters=request.POST.getlist("filters"),
            ))
            response["message"] = _("MO Router added successfully!")
        elif s == "delete":
            response = morouter.destroy(order=request.POST.get("order"))
            response["message"] = _("MO Router deleted successfully!")
        else:
            return JsonResponse({"message": _("Sorry, Command does not matched."), "status": 400}, status=400)
    response["status"] = 200
    return JsonResponse(response)
