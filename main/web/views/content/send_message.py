from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from main.web.forms import SendMessageForm
from main.web.helpers import send_smpp, send_http
from main.core.utils import display_form_validations
from main.core.smpp import Users
from main.core.models import UsersModel
from main.core.tools import require_post_ajax


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
                    # First try to get from Django model (has stored password)
                    user_model = UsersModel.objects.filter(uid=user_uid).first()
                    if user_model:
                        username = user_model.username
                        password = user_model.password
                        if not password:
                            messages.warning(
                                request,
                                f'The stored password of {user_uid} cannot be decrypted (SECRET_KEY or '
                                'FIELD_ENCRYPTION_KEY changed); set it again from the Users page. '
                                'The message was sent with the default credentials.')
                    else:
                        # Fallback to Jasmin telnet (won't have password)
                        with Users() as users:
                            user_list = users.list_summary()
                        user_data = next((u for u in user_list['users'] if u['uid'] == user_uid), None)
                        if user_data:
                            username = user_data.get('username')
                            # Note: password won't be available from Jasmin
                            messages.warning(
                                request,
                                f'User {user_uid} was not created from this panel, so its password is unknown; '
                                'the message was sent with the default credentials.')
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


@require_post_ajax
def send_message_view_manage(request):
    if request.POST.get('s', '') == 'list_users':
        with Users() as users:
            response = users.list_summary()
        # Only these users can send as themselves: the panel stored their password.
        known = set(UsersModel.objects.values_list('uid', flat=True))
        for user in response['users']:
            user['has_password'] = user['uid'] in known
        response['status'] = 200
        return JsonResponse(response)
    return JsonResponse({'status': 400, 'message': 'Sorry, Command does not matched.'}, status=400)
