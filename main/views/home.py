from django.shortcuts import render_to_response, HttpResponseRedirect, render, redirect, HttpResponse

def home_view(request):
    return render(request,'templates/main.html')