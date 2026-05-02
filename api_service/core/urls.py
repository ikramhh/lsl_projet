from django.urls import path
from . import views

urlpatterns = [

    # =========================
    # HOME
    # =========================
    path('', views.home),
    
    # =========================
    # HEALTH CHECK (pour Consul)
    # =========================
    path('health/', views.health_check),

    # =========================
    # TRANSLATIONS API
    # =========================
    path('translations/', views.translations),
    path('translations/<int:id>/', views.translation_detail),

    # =========================
    # HISTORY API
    # =========================
    path('history/', views.HistoryView.as_view()),
    path('history/<int:id>/', views.HistoryDetailView.as_view()),

    path('camera/', views.camera_page),
    path('predict/', views.predict),
    
]

