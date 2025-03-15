from django.shortcuts import render
from .models import StockPreference
import requests
from django.conf import settings

# Create your views here.

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
