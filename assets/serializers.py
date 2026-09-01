from rest_framework import serializers
from .models import CryptoCurrency

class CryptoCurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = CryptoCurrency
        fields = ['id', 'name', 'symbol', 'current_price', 'updated_at']
        read_only_fields = fields
        