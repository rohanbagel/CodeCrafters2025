from django.contrib import admin
from .models import UserWallet, WalletTransaction, Stock, StockHolding, StockTransaction, SimulationScenario, UserProgress

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'current_price', 'price_change', 'last_updated')
    search_fields = ('symbol', 'name')

@admin.register(StockHolding)
class StockHoldingAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'stock', 'quantity', 'average_price')
    list_filter = ('wallet', 'stock')

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'stock', 'transaction_type', 'quantity', 'price_per_share', 'total_amount', 'created_at')
    list_filter = ('transaction_type', 'stock', 'wallet')
    search_fields = ('wallet__user__username', 'stock__symbol')

@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'created_at')
    search_fields = ('user__username',)

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'amount', 'balance_after', 'created_at')
    list_filter = ('transaction_type',)
    search_fields = ('wallet__user__username',)

admin.site.register(SimulationScenario)
admin.site.register(UserProgress)
