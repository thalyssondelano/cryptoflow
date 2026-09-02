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
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    throttle_scope = 'login'

class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    throttle_scope = 'register'


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


class UserNetWorthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = request.user.wallet
        balance = wallet.balance
        
        crypto_assets_total = Decimal('0.00')
        assets_detail = []

        # Percorre todos os ativos da mochila do usuário
        for asset in wallet.crypto_assets.all():
            crypto = asset.crypto
            current_price = crypto.current_price
            total_value = (asset.quantity * current_price).quantize(Decimal('0.01'))
            
            crypto_assets_total += total_value
            assets_detail.append({
                "symbol": crypto.symbol,
                "name": crypto.name,
                "quantity": asset.quantity,
                "current_price": current_price,
                "total_value_usd": total_value
            })

        net_worth = (balance + crypto_assets_total).quantize(Decimal('0.01'))

        return Response({
            "balance_usd": balance,
            "crypto_assets_usd": crypto_assets_total,
            "net_worth_usd": net_worth,
            "assets": assets_detail
        }, status=status.HTTP_200_OK)


class GlobalLeaderboardView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = None # Ignora a config global de paginação

    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 10))
        except ValueError:
            limit = 10

        # Trava de segurança: mínimo de 1 e máximo de 50 itens por requisição
        limit = max(1, min(limit, 50))

        # Otimiza a consulta para evitar gargalos de N+1 queries
        wallets = Wallet.objects.select_related('user').prefetch_related('crypto_assets__crypto')
        leaderboard_data = []

        for wallet in wallets:
            balance = wallet.balance
            crypto_assets_total = Decimal('0.00')

            for asset in wallet.crypto_assets.all():
                current_price = asset.crypto.current_price
                crypto_assets_total += asset.quantity * current_price

            net_worth = balance + crypto_assets_total

            leaderboard_data.append({
                "username": wallet.user.username,
                "net_worth_usd": net_worth.quantize(Decimal('0.01'))
            })

        # Ordena do maior patrimônio para o menor
        leaderboard_data = sorted(leaderboard_data, key=lambda x: x['net_worth_usd'], reverse=True)

        return Response(leaderboard_data[:limit], status=status.HTTP_200_OK)