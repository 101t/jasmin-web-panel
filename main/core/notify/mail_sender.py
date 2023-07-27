import logging

from django.utils.translation import gettext_lazy as _
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.conf import settings

from main.core.tasks import mail_html_mails
from main.core.utils import get_current_site, reset_password_token, email_active_token

logger = logging.getLogger(__name__)


def send_mail_reset_email(request) -> bool:
    if request.user.is_authenticated:
        uidb64 = urlsafe_base64_encode(force_bytes(request.user.pk))  # noqa
        token = email_active_token.make_token(request.user)
        subject = str(_("Verify your email address"))
        template_name = "core/mail_reset_email.html"
        current_site = get_current_site(request=request)
        reset_email_url = reverse("users:email_verification_view", kwargs={"uidb64": uidb64, "token": token})  # noqa
        reset_email_confirm = f"{current_site}{reset_email_url}"
        details = {
            "email": request.user.email,
            "welcome_message": _("Verify your email address"),
            "site_url": current_site,
            "reset_email_confirm": reset_email_confirm,
            "current_site": current_site,
        }
        mail_html_mails.delay([request.user.email], subject, template_name, details, settings.LANGUAGE_CODE)
        return True
    else:
        return False


def send_mail_reset_password(request, user) -> bool:
    current_site = get_current_site(request=request)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))  # noqa
    token = reset_password_token.make_token(user=user)
    reset_password_url = reverse("users:reset_password_view", kwargs={"uidb64": uidb64, "token": token})  # noqa
    reset_password_confirm = f"{current_site}{reset_password_url}"
    site_name = settings.SITE_NAME
    details = {
        "email": user.email,
        "welcome_message": _("Reset your password on %(site_name)s") % {"site_name": site_name},
        "site_url": current_site,
        "site_name": site_name,
        "reset_password_confirm": reset_password_confirm,
        "current_site": current_site,
    }
    subject = str(_("%(site_name)s Reset Password") % {"site_name": site_name})
    template_name = "core/mail_reset_password.html"
    mail_html_mails.delay([user.email], subject, template_name, details, settings.LANGUAGE_CODE)
    return True
