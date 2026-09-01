import requests
from celery import shared_task
from django.db import transaction
from .models import CryptoCurrency

@shared_task
def fetch_and_update_prices():
    # Mapeamento para o ID oficial da CoinGecko
    coin_map = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'SOL': 'solana',
        'DOGE': 'dogecoin'
    }
    
    # Junta tudo e monta a URL (bitcoin,ethereum,solana,dogecoin)
    coingecko_ids = ','.join(coin_map.values())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coingecko_ids}&vs_currencies=usd"
    
    try:
        # Bate na API com timeout de 10 segundos
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Transação atômica para garantir a integridade do banco
        with transaction.atomic():
            for symbol, gecko_id in coin_map.items():
                if gecko_id in data:
                    new_price = data[gecko_id]['usd']
                    
                    CryptoCurrency.objects.filter(symbol=symbol).update(current_price=new_price)
                    
        return f"Preços atualizados com sucesso: {data}"
        
    except requests.RequestException as e:
        return f"Erro na comunicação com a CoinGecko: {str(e)}"