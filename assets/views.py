from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import CryptoCurrency
from .serializers import CryptoCurrencySerializer

class CryptoCurrencyListView(generics.ListAPIView):
    queryset = CryptoCurrency.objects.filter(is_active=True)
    serializer_class = CryptoCurrencySerializer
    permission_classes = [IsAuthenticated]