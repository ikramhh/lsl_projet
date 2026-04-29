from django.urls import path
from . import views

urlpatterns = [
    path('camera/', views.camera),
    path('history/', views.history),
]