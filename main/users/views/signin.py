from django.utils.translation import gettext as _
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.shortcuts import HttpResponseRedirect, render, redirect
from django.db.models import Q

from main.users.models import User
from main.users.forms import SignInForm
from main.core.utils import display_form_validations


def signin_view(request):
    form = SignInForm()
    if request.POST:
        form = SignInForm(request.POST)
        if form.is_valid():
            username = request.POST.get("username")
            password = request.POST.get("password")
            next_page = request.POST.get("next") or "/"
            try:
                user = User.objects.get(Q(username=username) | Q(email=username))
                auth = authenticate(username=user.username, password=password)
                if auth and user:
                    if user.is_active:
                        if not user.is_email:
                            msg = _("Your Email Address is not verified yet! please verify your email address.")
                            messages.warning(request, message=msg)
                        else:
                            login(request, user)
                            return redirect(next_page)
                    else:
                        messages.warning(request, _('User banned, please contact support'))
                else:
                    raise Exception(_("Login Error, Invalid username or password, please try again"))
            except Exception as e:
                print(e)
                messages.error(request, _('Login Error, Invalid username or password, please try again'))
        else:
            display_form_validations(form=form, request=request)
    return render(request, "auth/signin.html", dict(form=form))


def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')
