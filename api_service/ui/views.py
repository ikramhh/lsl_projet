from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request, "ui/home.html")

@login_required(login_url='/auth/login/')
def camera(request):
    return render(request, "ui/camera.html")

@login_required(login_url='/auth/login/')
def history(request):
    return render(request, "ui/history.html")