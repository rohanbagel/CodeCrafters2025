from django.contrib import admin
from .models import RiskProfile, StockAlert, ExitStrategy

@admin.register(RiskProfile)
class RiskProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'risk_tolerance', 'email_alerts', 'use_ai_exit_strategy', 'updated_at')
    list_filter = ('email_alerts', 'in_app_alerts', 'use_ai_exit_strategy')
    search_fields = ('user__username', 'user__email')

@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ('stock_symbol', 'alert_type', 'user', 'status', 'created_at')
    list_filter = ('alert_type', 'status', 'created_at')
    search_fields = ('user__username', 'stock_symbol', 'stock_name', 'message')
    date_hierarchy = 'created_at'

@admin.register(ExitStrategy)
class ExitStrategyAdmin(admin.ModelAdmin):
    list_display = ('stock_symbol', 'user', 'current_price', 'target_exit_price', 'confidence_score', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'stock_symbol', 'stock_name', 'reasoning')
    date_hierarchy = 'updated_at'
