from django.core.management.base import BaseCommand
from assets.models import CryptoCurrency

class Command(BaseCommand):
    help = 'Popula o banco de dados com as moedas iniciais do simulador'

    def handle(self, *args, **kwargs):
        initial_coins = [
            {'name': 'Bitcoin', 'symbol': 'BTC'},
            {'name': 'Ethereum', 'symbol': 'ETH'},
            {'name': 'Solana', 'symbol': 'SOL'},
            {'name': 'Dogecoin', 'symbol': 'DOGE'},
        ]

        for coin in initial_coins:
            obj, created = CryptoCurrency.objects.get_or_create(
                symbol=coin['symbol'],
                defaults={
                    'name': coin['name'],
                    'current_price': 1.00, 
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ {coin['name']} Cadastrada com Sucesso!"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ {coin['name']} já existe no Banco."))