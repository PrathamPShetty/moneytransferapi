from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import (
    SignupView, VerifyEmailView, ProfileView,
    TransferView, TransactionsView, 
 
)
from .views import MyTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Public endpoints
    path('signup/', SignupView.as_view(), name='signup'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('transfer/', TransferView.as_view(), name='transfer'),
    path('transactions/', TransactionsView.as_view(), name='transactions'),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
