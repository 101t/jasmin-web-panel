from django.utils.translation import gettext as _
from django.db.models import Q
from django.shortcuts import HttpResponseRedirect, render, redirect, HttpResponse
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib import messages
from django.urls import reverse

from main.core.utils import reset_password_token, email_active_token, display_form_validations
from main.core.notify import send_mail_reset_password
from main.users.models import User
from main.users.forms import ResetPasswordConfirmForm, ResetPasswordForm


def reset_view(request):
    if request.POST:
        form = ResetPasswordForm(request.POST)
        username = request.POST.get("username")
        if form.is_valid():
            user = User.objects.filter(Q(username=username) | Q(email=username)).first()
            if user and send_mail_reset_password(request=request, user=user):
                messages.success(
                    request,
                    _("Success, reset password email has been sent, please check your email inbox")
                )
                return redirect(reverse("users:signin_view"))
            else:
                messages.warning(request, _("Warning, invalid username or email address"))
        else:
            display_form_validations(form=form, request=request)
    return render(request, "auth/reset.html")


def reset_password_view(request, uidb64: str = None, token: str = None):  # noqa
    user, show_confirm_form = None, False
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        show_confirm_form = True
    except User.DoesNotExist:  # noqa
        messages.error(request, _("Error, User does not match"))
    except (TypeError, ValueError, OverflowError):
        messages.error(request, _("Error, Unknown error occurred, please reset password and try again"))
    if request.POST:
        form = ResetPasswordConfirmForm(request.POST)
        if user and reset_password_token.check_token(user, token=token):
            password = request.POST.get("password")
            if form.is_valid():
                user.set_password(str(password))
                user.save()
                messages.success(request, _("Success, Your password has been reset successfully"))
                return redirect(reverse("users:signin_view"))
            else:
                display_form_validations(form=form, request=request)
        else:
            messages.error(request, _("Error, Invalid link, please try again"))
    return render(request, "auth/reset.html", {"show_confirm_form": show_confirm_form})


def email_verification_view(request, uidb64: str = None, token: str = None):  # noqa
    user = None
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except User.DoesNotExist:  # noqa
        messages.error(request, _("Error, User does not match"))
    except (TypeError, ValueError, OverflowError):
        messages.error(request, _("Error, Unknown error occurred, please reset password and try again"))
    if user:
        if user.is_email:
            messages.warning(request, _("Warning, Your email address already verified"))
        elif email_active_token.check_token(user, token=token):
            user.is_email = True
            user.is_verified = True
            user.save()
            messages.success(request, _("Your email hase been verified successfully"))
    else:
        messages.error(request, _("Unknown error occurred!"))
    return redirect(reverse("users:signin_view"))

