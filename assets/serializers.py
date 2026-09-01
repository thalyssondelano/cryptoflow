from rest_framework import serializers
from .models import CryptoCurrency

class CryptoCurrencySerializer(serializers.ReadOnlyModelSerializer):
    class Meta:
        model = CryptoCurrency
        fields = ['id', 'name', 'symbol', 'current_price', 'updated_at']