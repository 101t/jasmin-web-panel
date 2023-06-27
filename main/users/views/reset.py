from django.shortcuts import HttpResponseRedirect, render, redirect, HttpResponse


def reset_view(request):
    return render(request, "auth/reset.html")
