from django.contrib import admin
from .models import CryptoCurrency

@admin.register(CryptoCurrency)
class CryptoCurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'current_price', 'is_active', 'updated_at')
    search_fields = ('name', 'symbol')
    list_filter = ('is_active',)