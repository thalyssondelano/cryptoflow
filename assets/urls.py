from django.urls import path
from .views import CryptoCurrencyListView

urlpatterns = [
    path('currencies/', CryptoCurrencyListView.as_view(), name='crypto-list'),
]