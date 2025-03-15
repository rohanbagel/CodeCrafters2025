from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.risk_dashboard, name='risk_dashboard'),
    path('profile/settings/', views.risk_profile_settings, name='risk_profile_settings'),
    path('alerts/', views.stock_alerts, name='stock_alerts'),
    path('exit-strategies/', views.exit_strategies, name='exit_strategies'),
    path('analyze/<str:symbol>/', views.analyze_stock_risk, name='analyze_stock_risk'),
    path('api/mark-alert-read/', views.mark_alert_read, name='mark_alert_read'),
    path('api/dismiss-alert/', views.dismiss_alert, name='dismiss_alert'),
] 