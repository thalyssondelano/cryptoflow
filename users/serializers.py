from rest_framework import serializers
from .models import Wallet, WalletAsset
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