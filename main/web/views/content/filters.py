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
    filters = Filters()
    s = request.POST.get("s")
    if s == "list":
        response = filters.list()
    elif s == "add":
        filter_type = request.POST.get("type")
        data_filter = {
            "fid": request.POST.get("fid"),
            "type": filter_type,
        }
        
        if filter_type != "transparentfilter":
            data_filter['parameter'] = request.POST.get("parameter")
        
        response = filters.create(data=data_filter)
        response["message"] = str(_("Filter added successfully!"))
    elif s == "delete":
        response = filters.destroy(fid=request.POST.get("fid"))
        response["message"] = str(_("Filter deleted successfully!"))
    else:
        return JsonResponse({"message": str(_("Sorry, Command does not matched.")), "status": 400}, status=400)

    response["status"] = 200
    return JsonResponse(response, status=200)
