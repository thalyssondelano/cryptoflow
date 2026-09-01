from rest_framework import serializers
from .models import Wallet, WalletAsset, TradeHistory
from assets.models import CryptoCurrency
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class WalletAssetSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source='crypto.symbol', read_only=True)
    name = serializers.CharField(source='crypto.name', read_only=True)

    class Meta:
        model = WalletAsset
        fields = ['name', 'symbol', 'quantity']
        read_only_fields = fields


class WalletSerializer(serializers.ModelSerializer):
    crypto_assets = WalletAssetSerializer(many=True, read_only=True)

    class Meta:
        model = Wallet
        fields = ['balance', 'crypto_assets']
        read_only_fields = fields


class UserProfileSerializer(serializers.ModelSerializer):
    wallet = WalletSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'wallet']
        read_only_fields = fields


class BuyCryptoSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("O valor do investimento deve ser maior que zero.")
        return value

    def validate_symbol(self, value):
        # Verifica no banco se a moeda existe e está ativa para negociação
        if not CryptoCurrency.objects.filter(symbol=value, is_active=True).exists():
            raise serializers.ValidationError("Criptomoeda não disponível.")
        return value


class SellCryptoSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10)
    quantity = serializers.DecimalField(max_digits=18, decimal_places=8)

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("A quantidade para venda deve ser maior que zero.")
        return value

    def validate_symbol(self, value):
        # Verifica se a moeda existe e está ativa para negociação
        if not CryptoCurrency.objects.filter(symbol=value, is_active=True).exists():
            raise serializers.ValidationError("Criptomoeda não disponível.")
        return value


class TradeHistorySerializer(serializers.ModelSerializer):
    crypto_symbol = serializers.CharField(source='crypto.symbol', read_only=True)
    crypto_name = serializers.CharField(source='crypto.name', read_only=True)

    class Meta:
        model = TradeHistory
        fields = [
            'id', 
            'trade_type', 
            'crypto_symbol', 
            'crypto_name', 
            'quantity', 
            'price_at_transaction', 
            'usd_amount', 
            'timestamp'
        ]
        read_only_fields = fields