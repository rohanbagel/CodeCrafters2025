from django.urls import path
from . import views

app_name = 'simulation'

urlpatterns = [
    path('', views.simulation_home, name='home'),
    path('add-cash/', views.add_cash, name='add_cash'),
    path('reset-wallet/', views.reset_wallet, name='reset_wallet'),
    path('available-stocks/', views.available_stocks, name='available_stocks'),
    path('trade/<str:symbol>/', views.trade_stock, name='trade_stock'),
    path('buy-stock/<str:symbol>/', views.buy_stock, name='buy_stock'),
    path('sell-stock/<str:symbol>/', views.sell_stock, name='sell_stock'),
    path('transactions/', views.transactions_overview, name='transactions'),
    path('handle-scenario/', views.handle_scenario, name='handle_scenario'),
    path('statistics/', views.statistics, name='statistics'),
    path('get-ai-analysis/', views.get_ai_analysis, name='get_ai_analysis'),
] 