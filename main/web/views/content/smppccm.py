import time

from django.utils.translation import gettext as _
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from main.core.exceptions import JasminError
from main.core.smpp import SMPPCCM
from main.core.tools import require_post_ajax

# Fields of the add and edit forms, named like the jcli smppccm keys.
ADD_FIELDS = ('cid', 'host', 'port', 'username', 'password')
EDIT_FIELDS = (
    'logfile', 'logrotate', 'loglevel', 'host', 'port', 'ssl', 'username', 'password', 'bind', 'bind_to',
    'trx_to', 'res_to', 'pdu_red_to', 'con_loss_retry', 'con_loss_delay', 'con_fail_retry', 'con_fail_delay',
    'src_addr', 'src_ton', 'src_npi', 'dst_ton', 'dst_npi', 'bind_ton', 'bind_npi', 'validity', 'priority',
    'requeue_delay', 'addr_range', 'systype', 'dlr_expiry', 'submit_throughput', 'proto_id', 'coding',
    'elink_interval', 'def_msg_id', 'ripf', 'dlr_msgid',
)


@login_required
def smppccm_view(request):
    return render(request, "web/content/smppccm.html")


@require_post_ajax
def smppccm_view_manage(request):
    response = {}
    s = request.POST.get("s")
    cid = request.POST.get("cid", "").strip()
    with SMPPCCM() as smppccm:
        if s == "list":
            response = smppccm.list()
        elif s == "add":
            response = smppccm.create(data={k: request.POST.get(k) for k in ADD_FIELDS})
            response["message"] = _("SMPPCCM added successfully!")
        elif s == "edit":
            # Only fields that differ from the running configuration reach jcli.
            response = smppccm.partial_update(
                data={k: request.POST[k] for k in EDIT_FIELDS if k in request.POST}, cid=cid)
            response["message"] = _("SMPPCCM updated successfully!")
        elif s == "delete":
            response = smppccm.destroy(cid=cid)
            response["message"] = _("SMPPCCM deleted successfully!")
        elif s == "start":
            response = smppccm.start(cid=cid)
            response["message"] = _("SMPPCCM started successfully!")
        elif s == "stop":
            response = smppccm.stop(cid=cid)
            response["message"] = _("SMPPCCM stopped successfully!")
        elif s == "restart":
            try:
                smppccm.stop(cid=cid)
            except JasminError:
                pass  # already stopped: starting it is all a restart needs
            time.sleep(6)
            response = smppccm.start(cid=cid)
            response["message"] = _("SMPPCCM restarted successfully!")
        else:
            return JsonResponse({"message": _("Sorry, Command does not matched."), "status": 400}, status=400)
    response["status"] = 200
    return JsonResponse(response)
