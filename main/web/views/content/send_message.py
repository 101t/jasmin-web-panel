from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from main.web.forms import SendMessageForm
from main.web.helpers import send_smpp, send_http
from main.core.utils import display_form_validations


@login_required
def send_message_view(request):
    form = SendMessageForm()
    if request.method == 'POST':
        send_type = request.POST.get('send_type')
        src_addr = request.POST.get('src_addr')
        dst_addr = request.POST.get('dst_addr')
        text = request.POST.get('text')
        form = SendMessageForm(request.POST)
        if form.is_valid():
            if send_type == 'smpp':
                res_status, res_message = send_smpp(src_addr, dst_addr, text)
            elif send_type == 'http':
                res_status, res_message = send_http(src_addr, dst_addr, text)
            else:
                res_status, res_message = 400, f"Unknown send type: {send_type}"

            if res_status == 200:
                messages.success(request, 'Message sent successfully')
            else:
                messages.error(request, f'Message sending failed: {res_message}')
            return redirect(reverse('web:send_message_view'))
        else:
            display_form_validations(form=form, request=request)
    return render(request, 'web/content/send_message.html', {'form': form})


@login_required
def send_message_view_manage(request):
    return JsonResponse({'status': 200, 'message': 'OK'})
