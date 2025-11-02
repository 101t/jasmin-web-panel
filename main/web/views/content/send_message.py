from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from main.web.forms import SendMessageForm
from main.web.helpers import send_smpp, send_http
from main.core.utils import display_form_validations
from main.core.smpp import Users


@login_required
def send_message_view(request):
    form = SendMessageForm()
    if request.method == 'POST':
        send_type = request.POST.get('send_type')
        user_uid = request.POST.get('user_uid', '').strip()
        src_addr = request.POST.get('src_addr')
        dst_addr = request.POST.get('dst_addr')
        text = request.POST.get('text')
        form = SendMessageForm(request.POST)
        if form.is_valid():
            # Get user credentials if user_uid is provided
            username = None
            password = None
            if user_uid:
                try:
                    users = Users()
                    user_list = users.list()
                    if 'users' in user_list:
                        user_data = next((u for u in user_list['users'] if u['uid'] == user_uid), None)
                        if user_data:
                            username = user_data.get('username')
                            password = user_data.get('password')
                except Exception as e:
                    messages.warning(request, f'Could not fetch user credentials: {e}. Using defaults.')
            
            if send_type == 'smpp':
                if username and password:
                    res_status, res_message = send_smpp(src_addr, dst_addr, text, system_id=username, password=password)
                else:
                    res_status, res_message = send_smpp(src_addr, dst_addr, text)
            elif send_type == 'http':
                if username and password:
                    res_status, res_message = send_http(src_addr, dst_addr, text, username=username, password=password)
                else:
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
    if request.method == 'POST':
        action = request.POST.get('s', '')
        if action == 'list_users':
            try:
                users = Users()
                response = users.list()
                response['status'] = 200
                return JsonResponse(response)
            except Exception as e:
                return JsonResponse({'status': 400, 'message': str(e)}, status=400)
    return JsonResponse({'status': 200, 'message': 'OK'})
