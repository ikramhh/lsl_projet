from django.urls import path
from django.shortcuts import render
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
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
    
    # JWT API Endpoints
    path('api/login/', views.api_login, name='api_login'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]