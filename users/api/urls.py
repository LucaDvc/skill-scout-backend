from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from . import views

urlpatterns = [
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('register/', views.RegisterView.as_view(), name='register'),
    path('confirm-email/<str:token>/', views.confirm_email, name='email_confirm'),
    path('resend-confirm-email/', views.resend_confirm_email, name='resend_confirm_email'),
]
