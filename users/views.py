from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from .serializers import UserRegistrationSerializer, UserProfileSerializer
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CustomUser, Wallet, WalletAsset, TradeHistory
from .serializers import BuyCryptoSerializer, SellCryptoSerializer, TradeHistorySerializer
from assets.models import CryptoCurrency
from decimal import Decimal, ROUND_DOWN

User = get_user_model()

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
            quantity_bought = (amount / crypto.current_price).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)

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

            # Cria o recibo da compra no banco de dados
            TradeHistory.objects.create(
                wallet=wallet,
                crypto=crypto,
                trade_type='BUY',
                quantity=quantity_bought,
                price_at_transaction=crypto.current_price,
                usd_amount=amount
            )

        # Devolve o sucesso para o front-end
        return Response({
            "message": "Compra executada com sucesso.",
            "symbol": symbol,
            "quantity_bought": quantity_bought,
            "remaining_balance": wallet.balance
        }, status=status.HTTP_200_OK)


class SellCryptoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SellCryptoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        symbol = serializer.validated_data['symbol']
        quantity_to_sell = serializer.validated_data['quantity']

        # Só finaliza se nada der erro no meio do caminho
        with transaction.atomic():
            wallet = request.user.wallet
            
            # Busca a moeda no catálogo
            crypto = CryptoCurrency.objects.get(symbol=symbol)

            # Tenta pegar a linha específica dessa cripto na mochila do usuário
            try:
                asset = WalletAsset.objects.get(wallet=wallet, crypto=crypto)
            except WalletAsset.DoesNotExist:
                # Se não encontrar a linha, ele nunca comprou essa moeda
                return Response(
                    {"error": f"Você não possui {symbol} na sua carteira para vender."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Ele tem saldo suficiente daquela moeda?
            if asset.quantity < quantity_to_sell:
                return Response(
                    {"error": "Saldo insuficiente da criptomoeda selecionada para realizar a venda."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Converte a fração de cripto em dólares
            usd_earned = (quantity_to_sell * crypto.current_price).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

            # Atualiza a mochila e debita a cripto
            asset.quantity -= quantity_to_sell
            asset.save()

            # Atualiza a carteira e adiciona o dinheiro
            wallet.balance += usd_earned
            wallet.save()

            # Cria o recibo da venda no banco de dados
            TradeHistory.objects.create(
                wallet=wallet,
                crypto=crypto,
                trade_type='SELL',
                quantity=quantity_to_sell,
                price_at_transaction=crypto.current_price,
                usd_amount=usd_earned
            )

        # Devolve o recibo para o front-end
        return Response({
            "message": "Venda executada com sucesso.",
            "symbol": symbol,
            "quantity_sold": quantity_to_sell,
            "usd_earned": usd_earned,
            "remaining_crypto": asset.quantity,
            "new_balance": wallet.balance
        }, status=status.HTTP_200_OK)


class TradeHistoryView(generics.ListAPIView):
    serializer_class = TradeHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TradeHistory.objects.filter(wallet__user=self.request.user).order_by('-timestamp')