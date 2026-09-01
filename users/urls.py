from django.urls import path
from .views import UserRegisterView, UserProfileView, BuyCryptoView, SellCryptoView, TradeHistoryView, UserNetWorthView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='user-register'),

    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('me/', UserProfileView.as_view(), name='user-profile'),
    path('buy/', BuyCryptoView.as_view(), name='buy_crypto'),
    path('sell/', SellCryptoView.as_view(), name='sell_crypto'),
    path('history/', TradeHistoryView.as_view(), name='trade-history'),
    path('net-worth/', UserNetWorthView.as_view(), name='user-net-worth'),
]