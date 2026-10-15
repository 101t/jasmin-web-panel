from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from main.core.smpp import Groups
from main.core.tools import require_post_ajax


@login_required
def groups_view(request):
    return render(request, "web/content/groups.html")


@require_post_ajax
def groups_view_manage(request):
    response = {}
    s = request.POST.get("s")
    gid = request.POST.get("gid", "").strip()
    with Groups() as groups:
        if s == "list":
            response = groups.list()
        elif s == "add":
            response = groups.create(data=dict(gid=gid))
            response["message"] = _("Group added successfully!")
        elif s == "delete":
            response = groups.destroy(gid=gid)
            response["message"] = _("Group deleted successfully!")
        elif s == "enable":
            response = groups.enable(gid=gid)
            response["message"] = _("Group enabled successfully!")
        elif s == "disable":
            response = groups.disable(gid=gid)
            response["message"] = _("Group disabled successfully!")
        else:
            return JsonResponse({"message": _("Sorry, Command does not matched."), "status": 400}, status=400)
    response["status"] = 200
    return JsonResponse(response, status=200)
