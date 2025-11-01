import time

from django.utils.translation import gettext as _
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from main.core.smpp import SMPPCCM
from main.core.tools import require_post_ajax


@login_required
def smppccm_view(request):
    return render(request, "web/content/smppccm.html")


@require_post_ajax
def smppccm_view_manage(request):
    response = {}
    s = request.POST.get("s")
    smppccm = SMPPCCM()
    if s == "list":
        response = smppccm.list()
    elif s == "add":
        smppccm.create(data=dict(
            cid=request.POST.get("cid"),
            host=request.POST.get("host"),
            port=request.POST.get("port"),
            username=request.POST.get("username"),
            password=request.POST.get("password"),
        ))
        response["message"] = str(_("SMPPCCM added successfully!"))
    elif s == "edit":
        smppccm.partial_update(data=dict(
            cid=request.POST.get("cid"),
            logfile=request.POST.get("logfile"),
            logrotate=request.POST.get("logrotate"),
            loglevel=request.POST.get("loglevel"),
            host=request.POST.get("host"),
            port=request.POST.get("port"),
            ssl=request.POST.get("ssl"),
            username=request.POST.get("username"),
            password=request.POST.get("password"),
            bind=request.POST.get("bind"),
            bind_to=request.POST.get("bind_to"),
            trx_to=request.POST.get("trx_to"),
            res_to=request.POST.get("res_to"),
            pdu_red_to=request.POST.get("pdu_red_to"),
            con_loss_retry=request.POST.get("con_loss_retry"),
            con_loss_delay=request.POST.get("con_loss_delay"),
            con_fail_retry=request.POST.get("con_fail_retry"),
            con_fail_delay=request.POST.get("con_fail_delay"),
            src_addr=request.POST.get("src_addr"),
            src_ton=request.POST.get("src_ton"),
            src_npi=request.POST.get("src_npi"),
            dst_ton=request.POST.get("dst_ton"),
            dst_npi=request.POST.get("dst_npi"),
            bind_ton=request.POST.get("bind_ton"),
            bind_npi=request.POST.get("bind_npi"),
            validity=request.POST.get("validity"),
            priority=request.POST.get("priority"),
            requeue_delay=request.POST.get("requeue_delay"),
            addr_range=request.POST.get("addr_range"),
            systype=request.POST.get("systype"),
            dlr_expiry=request.POST.get("dlr_expiry"),
            submit_throughput=request.POST.get("submit_throughput"),
            proto_id=request.POST.get("proto_id"),
            coding=request.POST.get("coding"),
            elink_interval=request.POST.get("elink_interval"),
            def_msg_id=request.POST.get("def_msg_id"),
            ripf=request.POST.get("ripf"),
            dlr_msgid=request.POST.get("dlr_msgid"),
        ), cid=request.POST.get("cid"))
        response["message"] = str(_("SMPPCCM updated successfully!"))
    elif s == "delete":
        response = smppccm.destroy(cid=request.POST.get("cid"))
        response["message"] = str(_("SMPPCCM deleted successfully!"))
    elif s == "start":
        response = smppccm.start(cid=request.POST.get("cid"))
        response["message"] = str(_("SMPPCCM started successfully!"))
    elif s == "stop":
        response = smppccm.stop(cid=request.POST.get("cid"))
        response["message"] = str(_("SMPPCCM stoped successfully!"))
    elif s == "restart":
        smppccm.stop(cid=request.POST.get("cid"))
        time.sleep(6)
        response = smppccm.start(cid=request.POST.get("cid"))
        response["message"] = str(_("SMPPCCM restarted successfully!"))
    else:
        return JsonResponse({"message": str(_("Sorry, Command does not matched.")), "status": 400}, status=400)
    response["status"] = 200
    return JsonResponse(response)
