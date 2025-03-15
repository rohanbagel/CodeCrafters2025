from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.get_started, name='get_started'),
    path('home/', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('market-analytics/', views.market_analytics, name='market_analytics'),
    path('market-stocks/', views.market_stocks, name='market_stocks'),
    path('gemini-chat/', views.gemini_chat, name='gemini_chat'),
    path('update-wallet/', views.update_wallet, name='update_wallet'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('update-profile-photo/', views.update_profile_photo, name='update_profile_photo'),
    path('stock/<str:symbol>/', views.stock_detail, name='stock_detail'),
    path('stock/<str:symbol>/buy/', views.buy_stock, name='buy_stock'),
    path('stock/<str:symbol>/sell/', views.sell_stock, name='sell_stock'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('generate-portfolio-report/', views.generate_portfolio_report, name='generate_portfolio_report'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
