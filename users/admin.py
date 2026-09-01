from django.contrib import admin
from .models import CustomUser, Wallet, WalletAsset
from django.contrib.auth.admin import UserAdmin

admin.site.register(CustomUser, UserAdmin)

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    search_fields = ('user__username', 'user__email')

@admin.register(WalletAsset)
class WalletAssetAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'crypto', 'quantity')
    search_fields = ('wallet__user__username', 'crypto__symbol') 
    
    def get_username(self, obj):
        return obj.wallet.user.username
    get_username.short_description = 'Usuário'