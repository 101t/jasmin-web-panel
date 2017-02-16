from django.shortcuts import render_to_response, HttpResponseRedirect, render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import user_passes_test
import json
from main.apps.core.smpp import TelnetConnection, SMPPCCM

@user_passes_test(lambda u: u.is_superuser)
def smppccm_view(request):
	args = {}
	return render(request, 'administration/smppccm.html', args)

@user_passes_test(lambda u: u.is_superuser)
def smppccm_view_manage(request):
	args = {}
	if request.POST:
		service = request.POST.get("s", None)
		if service == "list":
			tc = TelnetConnection()
			smppccm = SMPPCCM(telnet=tc.telnet)
			args = smppccm.list()
		elif service == "add":
			tc = TelnetConnection()
			smppccm = SMPPCCM(telnet=tc.telnet)
			smppccm.create(data={
				"cid": request.POST.get("cid"),
				"host": request.POST.get("host"),
				"port": request.POST.get("port"),
				"username": request.POST.get("username"),
				"password": request.POST.get("password"),
			})
		elif service == "edit":
			tc = TelnetConnection()
			smppccm = SMPPCCM(telnet=tc.telnet)
			smppccm.partial_update(data={
				"cid": request.POST.get("cid"),
				"logfile": request.POST.get("logfile"),
				"logrotate": request.POST.get("logrotate"),
				"loglevel": request.POST.get("loglevel"),
				"host": request.POST.get("host"),
				"port": request.POST.get("port"),
				"ssl": request.POST.get("ssl"),
				"username": request.POST.get("username"),
				"password": request.POST.get("password"),
				"bind": request.POST.get("bind"),
				"bind_to": request.POST.get("bind_to"),
				"trx_to": request.POST.get("trx_to"),
				"res_to": request.POST.get("res_to"),
				"pdu_red_to": request.POST.get("pdu_red_to"),
				"con_loss_retry": request.POST.get("con_loss_retry"),
				"con_loss_delay": request.POST.get("con_loss_delay"),
				"con_fail_retry": request.POST.get("con_fail_retry"),
				"con_fail_delay": request.POST.get("con_fail_delay"),
				"src_addr": request.POST.get("src_addr"),
				"src_ton": request.POST.get("src_ton"),
				"src_npi": request.POST.get("src_npi"),
				"dst_ton": request.POST.get("dst_ton"),
				"dst_npi": request.POST.get("dst_npi"),
				"bind_ton": request.POST.get("bind_ton"),
				"bind_npi": request.POST.get("bind_npi"),
				"validity": request.POST.get("validity"),
				"priority": request.POST.get("priority"),
				"requeue_delay": request.POST.get("requeue_delay"),
				"addr_range": request.POST.get("addr_range"),
				"systype": request.POST.get("systype"),
				"dlr_expiry": request.POST.get("dlr_expiry"),
				"submit_throughput": request.POST.get("submit_throughput"),
				"proto_id": request.POST.get("proto_id"),
				"coding": request.POST.get("coding"),
				"elink_interval": request.POST.get("elink_interval"),
				"def_msg_id": request.POST.get("def_msg_id"),
				"ripf": request.POST.get("ripf"),
				"dlr_msgid": request.POST.get("dlr_msgid"),
			}, cid=request.POST.get("cid"))
		elif service == "delete":
			tc = TelnetConnection()
			smppccm = SMPPCCM(telnet=tc.telnet)
			args = smppccm.destroy(cid=request.POST.get("cid"))
		elif service == "start":
			tc = TelnetConnection()
			smppccm = SMPPCCM(telnet=tc.telnet)
			args = smppccm.start(cid=request.POST.get("cid"))
		elif service == "stop":
			tc = TelnetConnection()
			smppccm = SMPPCCM(telnet=tc.telnet)
			args = smppccm.stop(cid=request.POST.get("cid"))
		elif service == "restart":
			tc = TelnetConnection()
			smppccm = SMPPCCM(telnet=tc.telnet)
			args = smppccm.stop(cid=request.POST.get("cid"))
			args = smppccm.start(cid=request.POST.get("cid"))
	return HttpResponse(json.dumps(args), content_type='application/json')