import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

# Classes 
class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.email})"

class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=5000.00)

    def __str__(self):
        return f"{self.user.username} - Saldo: ${self.balance}"

    
class WalletAsset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='crypto_assets')
    
    crypto = models.ForeignKey('assets.CryptoCurrency', on_delete=models.CASCADE)
    
    quantity = models.DecimalField(max_digits=18, decimal_places=8, default=0.00000000)

    class Meta:
        # Uma carteira não pode ter duas linhas separadas para o mesmo ativo.
        unique_together = ('wallet', 'crypto') 

    def __str__(self):
        return f"{self.quantity} {self.crypto.symbol} - {self.wallet.user.username}"


class TradeHistory(models.Model):
    TRADE_TYPES = (
        ('BUY', 'Compra'),
        ('SELL', 'Venda'),
    )

    # De quem é o recibo
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='trade_history')
    
    # Qual moeda foi negociada
    crypto = models.ForeignKey('assets.CryptoCurrency', on_delete=models.SET_NULL, null=True)
    
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)
    
    # Fração da cripto e preço que ela estava no momento da transação
    quantity = models.DecimalField(max_digits=18, decimal_places=8)
    price_at_transaction = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Total em dólares gasto (na compra) ou recebido (na venda)
    usd_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Data e hora exatas
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        crypto_symbol = self.crypto.symbol if self.crypto else 'Moeda Excluída'
        return f"{self.wallet.user.username} - {self.trade_type} - {self.quantity} {crypto_symbol}"

    
# Automações
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)