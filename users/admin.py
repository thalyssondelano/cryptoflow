from django.contrib import admin
from .models import CustomUser, Wallet, WalletAsset, TradeHistory
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'username')

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )

    list_display = ('email', 'username', 'is_staff')
    search_fields = ('email', 'username')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('username',)}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas', {'fields': ('last_login', 'date_joined')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)

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

@admin.register(TradeHistory)
class TradeHistoryAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'trade_type', 'crypto', 'quantity', 'usd_amount', 'timestamp')
    list_filter = ('trade_type', 'timestamp')
    search_fields = ('wallet__user__username', 'crypto__symbol')
    readonly_fields = ('timestamp', 'wallet', 'crypto', 'trade_type', 'quantity', 'price_at_transaction', 'usd_amount') 

    def get_username(self, obj):
        return obj.wallet.user.username
    get_username.short_description = 'Usuário'