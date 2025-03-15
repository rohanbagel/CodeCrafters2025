from django.shortcuts import render, redirect, get_object_or_404
from .models import StockPreference, UserProfile
import requests
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def get_started(request):
    return render(request, 'User/get_started.html')

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
