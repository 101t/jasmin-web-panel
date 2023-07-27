import json
import os

from PIL import Image
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from main.core.models import ActivityLog, EmailServer
from main.core.notify import send_mail_reset_email
from main.core.utils import display_form_validations, is_json, get_query, paginate
from main.users.forms import ChangePhotoForm, ChangePasswordForm, ProfileForm
from main.users.models import User


@login_required
def profile_view(request):
    if request.POST:
        s = request.POST.get("s")
        if s == "profile":
            try:
                form = ProfileForm(request.POST)
                if form.is_valid():
                    email = request.POST.get("email") or ""
                    email = email.strip()
                    user = User.objects.get(pk=request.user.pk)
                    user.first_name = request.POST.get("first_name")
                    user.last_name = request.POST.get("last_name")
                    if email and user.email != email:
                        user.email = email
                        if EmailServer.objects.filter(active=True).exists():
                            user.is_email = False
                            send_mail_reset_email(request=request)
                            messages.info(request, _("Please check your email inbox to verify your email address"))
                    user.save()
                    messages.success(request, _("Congrats!, Your profile has been updated successfully"))
                else:
                    display_form_validations(form=form, request=request)
            except Exception as e:
                messages.error(request, _("Oops, An error occured while updating profile"))
        elif s == "avatar":
            form = ChangePhotoForm(request.POST, request.FILES)
            if form.is_valid():
                f = request.FILES.get("avatar_file")
                avatar_data = request.POST.get("avatar_data", "")
                x, y, w, h = 0.0, 0.0, 0.0, 0.0
                if is_json(avatar_data):
                    avatar_data = json.loads(avatar_data)
                    x = avatar_data.get("x")
                    y = avatar_data.get("y")
                    w = avatar_data.get("w")
                    h = avatar_data.get("h")
                fn, fx = os.path.splitext(f.name)
                img_directory = "{}/avatars/".format(settings.MEDIA_ROOT)
                if not os.path.exists(img_directory):
                    os.makedirs(img_directory)
                tmp_filename = "{}/avatars/{}_tmp{}".format(settings.MEDIA_ROOT, request.user.username, fx)
                jpg_filename = "{}/avatars/{}_tmp.jpg".format(settings.MEDIA_ROOT, request.user.username)
                with open(tmp_filename, 'wb+') as destination:
                    for chunk in f.chunks():
                        destination.write(chunk)
                im = Image.open(tmp_filename)
                im = im.convert("RGB")
                im.save(jpg_filename, "JPEG", optimize=True, quality=95)
                im = Image.open(jpg_filename)
                cropped_im = im.crop((x, y, w + x, h + y))
                cropped_im.thumbnail((512, 512), Image.ANTIALIAS)
                cropped_im.save(jpg_filename.replace("_tmp", ""), optimize=True, quality=95)
                if os.path.exists(tmp_filename):
                    os.remove(tmp_filename)
                if os.path.exists(jpg_filename):
                    os.remove(jpg_filename)
                filename = "{}avatars/{}.jpg".format(settings.MEDIA_URL, request.user.username)
                user = User.objects.filter(pk=request.user.pk).first()
                if user:
                    user.img = filename
                    user.save()
                return JsonResponse(dict(
                    message=str(_("Amazing!, Your profile picture has been updated successfully")),
                    state=200,
                    result="%(filename)s?s=%(timenow)s" % dict(filename=filename, timenow=timezone.now())
                ))
        elif s == "avatar_reset":
            try:
                user = User.objects.get(pk=request.user.pk)
                user.img = settings.DEFAULT_USER_AVATAR
                user.save()
                messages.success(request, _("OK, Your avatar profile has been reseted successfully"))
            except:
                messages.error(request, _("Oops, An error occured while removing avatar"))
        elif s == "password":
            password = request.POST.get("password")
            password1 = request.POST.get("password1")
            # password2 = request.POST.get("password2")
            form = ChangePasswordForm(request.POST)
            user = User.objects.get(pk=request.user.pk)
            if user.check_password(password):
                if form.is_valid():
                    user.set_password(password1)
                    user.save()
                    update_session_auth_hash(request, user)
                    messages.success(request, "OK, Your password has been changed successfully")
                else:
                    display_form_validations(form=form, request=request)
            else:
                messages.warning(request, "Error, Your password incorrect, please try again")
        return redirect(reverse("users:profile_view"))
    return render(request, "auth/profile.html")


@login_required
def settings_view(request):
    return render(request, "auth/settings.html")


@login_required
def activity_log_view(request):
    activitylogs = ActivityLog.objects.filter(user=request.user)
    search = request.GET.get("search")
    if search:
        entry_query = get_query(search, ("ip", "path",))
        activitylogs = activitylogs.filter(entry_query)
    activitylogs = paginate(objects=activitylogs, per_page=24, page=request.GET.get("page"))
    return render(request, "auth/activity_log.html", dict(activitylogs=activitylogs))
