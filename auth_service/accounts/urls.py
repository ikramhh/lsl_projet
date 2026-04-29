from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view),
    path('register/', views.register_view),
    path('logout/', views.logout_view),
    path('camera-redirect/', views.camera_redirect),
    path('history-redirect/', views.history_redirect),
]