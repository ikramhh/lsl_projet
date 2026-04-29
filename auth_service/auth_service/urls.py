from django.contrib import admin
from django.urls import path, include
from accounts import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Create accounts URL patterns
accounts_urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('camera-redirect/', views.camera_redirect, name='camera_redirect'),
    path('history-redirect/', views.history_redirect, name='history_redirect'),
    
    # JWT API Endpoints
    path('api/login/', views.api_login, name='api_login'),  # Custom login with JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include(accounts_urlpatterns)),
]