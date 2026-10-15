from django.utils.translation import gettext as _
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from main.core.smpp import MTRouter
from main.core.tools import require_post_ajax


@login_required
def mtrouter_view(request):
    context = {
        "mt_router_types": MTRouter.MT_ROUTER_TYPES,
    }
    return render(request, "web/content/mtrouter.html", context)


@require_post_ajax
def mtrouter_view_manage(request):
    response = {}
    s = request.POST.get("s")
    with MTRouter() as mtrouter:
        if s == "list":
            response = mtrouter.list()
        elif s == "add":
            # Multi-selects post one value per selected option; .get() would keep only the last (#107).
            response = mtrouter.create(data=dict(
                type=request.POST.get("type"),
                order=request.POST.get("order"),
                rate=request.POST.get("rate"),
                smppconnectors=request.POST.getlist("smppconnectors"),
                filters=request.POST.getlist("filters"),
            ))
            response["message"] = _("MT Router added successfully!")
        elif s == "delete":
            response = mtrouter.destroy(order=request.POST.get("order"))
            response["message"] = _("MT Router deleted successfully!")
        else:
            return JsonResponse({"message": _("Sorry, Command does not matched."), "status": 400}, status=400)
    response["status"] = 200
    return JsonResponse(response)
