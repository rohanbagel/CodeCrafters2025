from django.contrib import admin
from .models import UserProfile, StockPreference, StockTransaction

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'wallet_balance', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'profile_photo')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'address')
        }),
        ('Financial Information', {
            'fields': ('wallet_balance',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

class StockPreferenceAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'company_name', 'is_active')
    search_fields = ('symbol', 'company_name')
    list_filter = ('is_active',)

class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'symbol', 'quantity', 'price', 'total_amount', 'created_at')
    search_fields = ('user__username', 'symbol', 'company_name')
    list_filter = ('transaction_type', 'created_at')
    readonly_fields = ('created_at',)

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(StockPreference, StockPreferenceAdmin)
admin.site.register(StockTransaction, StockTransactionAdmin)
