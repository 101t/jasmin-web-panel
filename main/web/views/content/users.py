from django.utils.translation import gettext as _
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from main.core.smpp import Users
from main.core.models import UsersModel, GroupsModel
from main.core.tools import require_post_ajax

# The edit form has one checkbox per jcli "mt_messaging_cred authorization" key.
AUTHORIZATIONS = (
    'http_send', 'http_balance', 'http_rate', 'http_bulk', 'smpps_send', 'http_long_content', 'dlr_level',
    'http_dlr_method', 'src_addr', 'priority', 'validity_period', 'schedule_delivery_time', 'hex_content',
)
# form field -> "mt_messaging_cred valuefilter" key
VALUE_FILTERS = {
    'src_addr_f': 'src_addr', 'dst_addr_f': 'dst_addr', 'content_f': 'content',
    'priority_f': 'priority', 'validity_period_f': 'validity_period',
}
QUOTAS = ('balance', 'sms_count', 'early_percent', 'http_throughput', 'smpps_throughput')
UNLIMITED = ('', 'ND', 'NONE')


def _same_quota(current, wanted):
    if current.upper() in UNLIMITED or wanted.upper() in UNLIMITED:
        return current.upper() in UNLIMITED and wanted.upper() in UNLIMITED
    try:
        return float(current) == float(wanted)
    except ValueError:
        return current == wanted


def user_updates(post, current):
    """jcli update lines for what the edit form changed.

    Unchanged values are not sent: re-sending the balance or SMS count shown when the form
    was opened would overwrite whatever the user consumed in the meantime.
    """
    cred = current.get('mt_messaging_cred', {})
    updates = []
    gid = post.get('gid', '').strip()
    if gid and gid != current.get('gid'):
        updates.append(['gid', gid])
    if post.get('password'):
        updates.append(['password', post['password']])
    authorization = cred.get('authorization', {})
    for key in AUTHORIZATIONS:
        # An unchecked checkbox is simply absent from the POST data.
        wanted = 'True' if post.get(key) else 'False'
        if key in authorization and authorization[key] != wanted:
            updates.append(['mt_messaging_cred', 'authorization', key, wanted])
    valuefilter = cred.get('valuefilter', {})
    for field, key in VALUE_FILTERS.items():
        wanted = post.get(field, '').strip()
        if wanted and wanted != valuefilter.get(key):
            updates.append(['mt_messaging_cred', 'valuefilter', key, wanted])
    if 'src_addr_d' in post:
        wanted = post['src_addr_d'].strip() or 'None'
        if wanted != cred.get('defaultvalue', {}).get('src_addr', 'None'):
            updates.append(['mt_messaging_cred', 'defaultvalue', 'src_addr', wanted])
    quota = cred.get('quota', {})
    for key in QUOTAS:
        if key not in post:
            continue
        wanted = post[key].strip()
        if not _same_quota(quota.get(key, 'ND'), wanted):
            updates.append(['mt_messaging_cred', 'quota', key, 'None' if wanted.upper() in UNLIMITED else wanted])
    return updates


@login_required
def users_view(request):
    return render(request, "web/content/users.html")


@require_post_ajax
def users_view_manage(request):
    response = {}
    s = request.POST.get("s")
    uid = request.POST.get("uid", "").strip()
    with Users() as users:
        if s == "list":
            response = users.list()
        elif s == "list_summary":
            response = users.list_summary()
        elif s == "add":
            gid = request.POST.get("gid")
            username = request.POST.get("username")
            password = request.POST.get("password")
            users.create(data=dict(uid=uid, gid=gid, username=username, password=password))

            # Store credentials in Django model for send_message feature
            group_model, created = GroupsModel.objects.get_or_create(gid=gid)
            UsersModel.objects.update_or_create(
                uid=uid,
                defaults={
                    'gid': group_model,
                    'username': username,
                    'password': password,
                    'parameters': '',
                    'user': request.user,
                }
            )
            response["message"] = _("User added successfully!")
        elif s == "edit":
            updates = user_updates(request.POST, users.get_user(uid))
            if not updates:
                return JsonResponse({"message": _("Nothing changed, there is nothing to save."), "status": 200})
            users.partial_update(updates, uid=uid)

            password = request.POST.get("password", "")
            if password:
                UsersModel.objects.filter(uid=uid).update(password=password)
            response["message"] = _("User edited successfully!")
        elif s == "delete":
            response = users.destroy(uid=uid)
            # Also delete from Django model
            UsersModel.objects.filter(uid=uid).delete()
            response["message"] = _("User deleted successfully!")
        elif s == "enable":
            response = users.enable(uid=uid)
            response["message"] = _("User enabled successfully!")
        elif s == "disable":
            response = users.disable(uid=uid)
            response["message"] = _("User disabled successfully!")
        elif s == "smpp_unbind":
            response = users.smpp_unbind(uid=uid)
            response["message"] = _("User unbound from the SMPP server successfully!")
        elif s == "smpp_ban":
            response = users.smpp_ban(uid=uid)
            response["message"] = _("User unbound and banned from the SMPP server successfully!")
        else:
            return JsonResponse({"message": _("Sorry, Command does not matched."), "status": 400}, status=400)
    response["status"] = 200
    return JsonResponse(response)
