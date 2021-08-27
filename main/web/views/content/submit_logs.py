import json

from main.core.models import SubmitLog
from main.core.utils import paginate

from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponse


def submit_logs_view(request):
    collection_list = SubmitLog.objects.all().order_by("-created_at")
    collection_list = paginate(collection_list, per_page=25, page=request.GET.get("page"))
    return render(request, "web/content/submit_logs.html", dict(collection_list=collection_list))


@login_required
def submit_logs_view_manage(request):
    args, res_status, res_message = {}, 400, _("Sorry, Command does not matched.")
    if request.POST and request.is_ajax():
        s = request.POST.get("s")
    if isinstance(args, dict):
        args["status"] = res_status
        args["message"] = str(res_message)
    else:
        res_status = 200
    return HttpResponse(json.dumps(args), status=res_status, content_type="application/json")
