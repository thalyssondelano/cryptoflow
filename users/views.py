from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from .serializers import UserRegistrationSerializer, UserProfileSerializer
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

User = get_user_model()

from .models import WalletAsset
from .serializers import BuyCryptoSerializer
from assets.models import CryptoCurrency


class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer

    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Previne IDOR buscando apenas os dados do dono do token JWT
        return self.request.user


class BuyCryptoView(APIView):
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        serializer = BuyCryptoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data['amount']
        symbol = serializer.validated_data['symbol']

        # Só finaliza se nada der erro no meio do caminho
        with transaction.atomic():
            wallet = request.user.wallet
            
            if wallet.balance < amount:
                return Response(
                    {"error": "Saldo insuficiente na carteira."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            crypto = CryptoCurrency.objects.get(symbol=symbol)
            
            # Converte dólares na fração da cripto
            quantity_bought = amount / crypto.current_price

            # Debita o dinheiro
            wallet.balance -= amount
            wallet.save()

            # Coloca a moeda na mochila
            asset, created = WalletAsset.objects.get_or_create(
                wallet=wallet, 
                crypto=crypto,
                defaults={'quantity': 0} 
            )
            
            # Soma a quantidade comprada e salva
            asset.quantity += quantity_bought
            asset.save()

        # Devolve o sucesso para o front-end
        return Response({
            "message": "Compra executada com sucesso.",
            "symbol": symbol,
            "quantity_bought": round(quantity_bought, 8),
            "remaining_balance": wallet.balance
        }, status=status.HTTP_200_OK)