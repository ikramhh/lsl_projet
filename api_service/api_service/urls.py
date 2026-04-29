from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth URLs (includes home at /auth/)
    path('auth/', include('accounts.urls')),

    # API REST
    path('api/', include('core.urls')),

    # UI
    path('ui/', include('ui.urls')),
    
    path('api/predict/', views.predict),
    
    # Root redirect to auth home
    path('', RedirectView.as_view(url='/auth/', permanent=False)),
]
