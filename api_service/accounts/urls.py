from django.urls import path
from django.shortcuts import render
from . import views

def home(request):
    """Home page"""
    return render(request, 'ui/home.html')

urlpatterns = [
    path('', home, name='home'),
    path('login/', views.login_view),
    path('register/', views.register_view),
    path('logout/', views.logout_view),
    path('camera-redirect/', views.camera_redirect),
    path('history-redirect/', views.history_redirect),
]