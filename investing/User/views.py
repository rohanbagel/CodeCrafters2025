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

    return render(request, 'User/profile.html')

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
