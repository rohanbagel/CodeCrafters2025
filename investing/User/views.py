from django.shortcuts import render, redirect, get_object_or_404
from .models import StockPreference, UserProfile
import requests
from django.conf import settings
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import google.generativeai as genai
import json
import finnhub
import pandas as pd
from django.core.paginator import Paginator
from decimal import Decimal

def get_started(request):
    return render(request, 'User/get_started.html')

def logout_view(request):
    logout(request)
    return redirect('get_started')

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'User/signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'User/signup.html')

        user = User.objects.create_user(username=username, password=password1)
        login(request, user)
        return redirect('home')

    return render(request, 'User/signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, 'User/login.html')

    return render(request, 'User/login.html')

# Create your views here.

@login_required
def home(request):
    # Default stocks to track
    default_stocks = [
        {'symbol': 'AAPL', 'name': 'Apple Inc.'},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.'},
        {'symbol': 'MSFT', 'name': 'Microsoft Corporation'},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.'},
    ]
    
    context = {
        'api_key': 'cvam92hr01qsapma5g6gcvam92hr01qsapma5g70',
        'stocks': default_stocks,
    }
    return render(request, 'User/home.html', context)

@login_required
def profile(request):
    # Get or create profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update user information
        user = request.user
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        
        # Update profile information
        profile.phone_number = request.POST.get('phone_number')
        profile.address = request.POST.get('address')

        # Handle profile photo upload
        if 'profile_photo' in request.FILES:
            profile.profile_photo = request.FILES['profile_photo']

        try:
            user.save()
            profile.save()
            messages.success(request, 'Profile updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')

        return redirect('profile')

    context = {
        'user': request.user,
        'profile': profile,
        'wallet_balance': profile.wallet_balance
    }
    return render(request, 'User/profile.html', context)

@login_required
def market_analytics(request):
    # Static data for all sections
    context = {
        'sentiment_data': {
            'positive': 35,
            'neutral': 40,
            'negative': 25
        },
        'sector_data': [
            {'sector': 'Technology', 'change': 2.5},
            {'sector': 'Healthcare', 'change': -1.2},
            {'sector': 'Finance', 'change': 1.8},
            {'sector': 'Energy', 'change': -0.5},
            {'sector': 'Consumer', 'change': 3.1},
            {'sector': 'Industrial', 'change': 0.7},
            {'sector': 'Materials', 'change': -2.1},
            {'sector': 'Real Estate', 'change': 1.4}
        ],
        'indicators_data': {
            'indicators': [
                {'name': 'RSI', 'value': 58, 'signal': 'NEUTRAL'},
                {'name': 'MACD', 'value': 0.5, 'signal': 'BULLISH'},
                {'name': 'Moving Average', 'value': 1.2, 'signal': 'BULLISH'},
                {'name': 'Bollinger Bands', 'value': 65, 'signal': 'NEUTRAL'}
            ]
        },
        'trends_data': {
            'trend_data': [
                {'date': '2024-03-10', 'value': 45},
                {'date': '2024-03-11', 'value': 52},
                {'date': '2024-03-12', 'value': 48},
                {'date': '2024-03-13', 'value': 55},
                {'date': '2024-03-14', 'value': 51},
                {'date': '2024-03-15', 'value': 58},
                {'date': '2024-03-16', 'value': 62}
            ]
        },
        'volume_data': {
            'volume_data': [44, 55, 57, 56, 61, 58, 63]
        }
    }
    
    return render(request, 'User/market_analytics.html', context)

@login_required
def market_stocks(request):
    # Initialize Finnhub client
    finnhub_client = finnhub.Client(api_key='cvam92hr01qsapma5g6gcvam92hr01qsapma5g70')
    
    # Get stock symbols from US market - limit to first 100 stocks for better performance
    stock_symbols = finnhub_client.stock_symbols('US')[:100]  # Limiting initial data load
    
    # Convert to DataFrame for easier filtering
    df = pd.DataFrame(stock_symbols)
    
    # Get filter parameters from request
    search_query = request.GET.get('search', '')
    market_cap_filter = request.GET.get('market_cap', 'all')
    sector_filter = request.GET.get('sector', 'all')
    
    # Apply filters
    if search_query:
        df = df[df['description'].str.contains(search_query, case=False) | 
                df['symbol'].str.contains(search_query, case=False)]
        # Limit search results to 50 for better performance
        df = df.head(50)
    
    if market_cap_filter != 'all':
        # Add market cap filtering logic here if available from API
        pass
    
    if sector_filter != 'all':
        # Add sector filtering logic here if available from API
        pass

    # Convert filtered DataFrame back to list of dicts
    stocks = df.to_dict('records')
    
    # Add real-time price data for each stock
    # Limit to 15 stocks per page for better performance
    for stock in stocks[:15]:
        try:
            quote = finnhub_client.quote(stock['symbol'])
            stock['current_price'] = round(quote['c'], 2) if quote['c'] else 'N/A'
            stock['price_change'] = round(quote['d'], 2) if quote['d'] else 'N/A'
            stock['price_change_percent'] = round(quote['dp'], 2) if quote['dp'] else 'N/A'
        except:
            stock['current_price'] = 'N/A'
            stock['price_change'] = 'N/A'
            stock['price_change_percent'] = 'N/A'
    
    # Pagination - reduce page size to 15 for better performance
    paginator = Paginator(stocks, 15)  # Show 15 stocks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'stocks': page_obj,
        'search_query': search_query,
        'market_cap_filter': market_cap_filter,
        'sector_filter': sector_filter,
    }
    
    return render(request, 'User/market_stocks.html', context)

@login_required
def update_wallet(request):
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            if amount <= 0:
                messages.error(request, 'Amount must be greater than 0')
                return redirect('profile')
                
            profile = request.user.profile  # Use the related_name to get profile directly
            profile.wallet_balance += amount
            profile.save()
            
            messages.success(request, f'Successfully added ${amount:,.2f} to your wallet')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount')
        except UserProfile.DoesNotExist:
            messages.error(request, 'User profile not found')
        except Exception as e:
            messages.error(request, f'Error updating wallet: {str(e)}')
    
    return redirect('profile')
