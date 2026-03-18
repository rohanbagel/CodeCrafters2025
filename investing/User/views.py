from django.shortcuts import render, redirect, get_object_or_404
from .models import StockPreference, UserProfile, StockTransaction
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
from simulation.models import UserWallet, WalletTransaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import logging
import traceback
import random
from datetime import datetime, timedelta
from twilio.rest import Client
from django.views.decorators.csrf import csrf_exempt
import PyPDF2
from io import BytesIO

# Set up logging
logger = logging.getLogger(__name__)

# Configure the Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)

# Add these settings to your settings.py
# TWILIO_ACCOUNT_SID = 'your_account_sid'
# TWILIO_AUTH_TOKEN = 'your_auth_token'
# TWILIO_PHONE_NUMBER = 'your_twilio_phone_number'

# Store OTPs temporarily (in a real app, use Redis or another cache)
OTP_STORE = {}

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
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
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
    # Define default stocks outside try block
    default_stocks = [
        {'symbol': 'AAPL', 'name': 'Apple Inc.'},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.'},
        {'symbol': 'MSFT', 'name': 'Microsoft Corporation'},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.'},
    ]
    
    try:
        # Get user's profile and transactions
        profile = request.user.profile
        transactions = StockTransaction.objects.filter(user=request.user)
        
        # Calculate total profit/loss and today's profit
        total_profit = Decimal('0')
        portfolio_value = Decimal('0')
        todays_profit = Decimal('0')
        active_investments = 0
        total_profit_percentage = 0
        
        # Get holdings data
        holdings_dict = {}
        for transaction in transactions:
            symbol = transaction.symbol
            if symbol not in holdings_dict:
                holdings_dict[symbol] = {
                    'quantity': 0,
                    'total_cost': Decimal('0')
                }
            
            if transaction.transaction_type == 'BUY':
                holdings_dict[symbol]['quantity'] += transaction.quantity
                holdings_dict[symbol]['total_cost'] += transaction.total_amount
            else:  # SELL
                holdings_dict[symbol]['quantity'] -= transaction.quantity
                holdings_dict[symbol]['total_cost'] -= transaction.total_amount
        
        # Initialize Finnhub client
        finnhub_client = finnhub.Client(api_key='cvam92hr01qsapma5g6gcvam92hr01qsapma5g70')
        
        # Calculate current values and profits
        portfolio_performance = []
        initial_investment = Decimal('0')
        
        for symbol, data in holdings_dict.items():
            if data['quantity'] > 0:
                active_investments += 1
                try:
                    quote = finnhub_client.quote(symbol)
                    current_price = Decimal(str(quote['c']))
                    previous_close = Decimal(str(quote['pc']))
                    current_value = current_price * data['quantity']
                    profit = current_value - data['total_cost']
                    
                    # Calculate today's profit for this stock
                    today_profit_for_stock = (current_price - previous_close) * data['quantity']
                    todays_profit += today_profit_for_stock
                    
                    # Add today's profit to total profit
                    total_profit += profit + today_profit_for_stock
                    portfolio_value += current_value
                    initial_investment += data['total_cost']
                    
                    # Get historical data for performance graph
                    candles = finnhub_client.stock_candles(
                        symbol, 'D', 
                        int((datetime.now() - timedelta(days=180)).timestamp()), 
                        int(datetime.now().timestamp())
                    )
                    if candles['s'] == 'ok':
                        portfolio_performance.append({
                            'symbol': symbol,
                            'dates': [datetime.fromtimestamp(t).strftime('%Y-%m-%d') for t in candles['t']],
                            'values': candles['c']
                        })
                        
                except Exception as e:
                    logger.error(f"Error fetching data for {symbol}: {e}")
        
        # Calculate total profit percentage
        if initial_investment > 0:
            total_profit_percentage = (total_profit / initial_investment) * 100

        context = {
            'api_key': 'cvam92hr01qsapma5g6gcvam92hr01qsapma5g70',
            'stocks': default_stocks,
            'wallet_balance': profile.wallet_balance,
            'total_profit': total_profit,
            'total_profit_percentage': round(total_profit_percentage, 2),
            'portfolio_value': portfolio_value,
            'todays_profit': todays_profit,
            'active_investments': active_investments,
            'portfolio_performance': portfolio_performance
        }
        
    except Exception as e:
        logger.error(f"Error in home view: {e}")
        context = {
            'api_key': 'cvam92hr01qsapma5g6gcvam92hr01qsapma5g70',
            'stocks': default_stocks,
            'error': 'Error loading dashboard data'
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
            # Debug print to check if we're hitting this view
            print("DEBUG: update_wallet view called")
            
            # Debug print to see what's in the POST data
            print("DEBUG: POST data:", request.POST)
            
            amount = Decimal(request.POST.get('amount', '0'))
            print(f"DEBUG: Amount parsed: {amount}")
            
            if amount <= 0:
                print("DEBUG: Amount is <= 0")
                messages.error(request, 'Please enter a positive amount.')
            elif amount > 1000000:
                print("DEBUG: Amount exceeds limit")
                messages.error(request, 'Maximum deposit limit is $1,000,000.')
            else:
                # Get user profile
                try:
                    profile = request.user.profile
                    print(f"DEBUG: Current wallet balance: {profile.wallet_balance}")
                    
                    # Update UserProfile wallet balance
                    old_balance = profile.wallet_balance
                    profile.wallet_balance += amount
                    profile.save()
                    print(f"DEBUG: New wallet balance: {profile.wallet_balance}")
                    print(f"DEBUG: Balance change: {profile.wallet_balance - old_balance}")

                    # Update or create simulation wallet
                    simulation_wallet, created = UserWallet.objects.get_or_create(user=request.user)
                    print(f"DEBUG: Simulation wallet {'created' if created else 'retrieved'}")
                    print(f"DEBUG: Current simulation wallet balance: {simulation_wallet.balance}")
                    
                    simulation_wallet.balance += amount
                    simulation_wallet.save()
                    print(f"DEBUG: New simulation wallet balance: {simulation_wallet.balance}")

                    # Create transaction record
                    transaction = WalletTransaction.objects.create(
                        wallet=simulation_wallet,
                        transaction_type='DEPOSIT',
                        amount=amount,
                        balance_after=simulation_wallet.balance,
                        description=f'Deposit from main wallet'
                    )
                    print(f"DEBUG: Transaction created: {transaction.id}")

                    messages.success(request, f'Successfully added ${amount:,.2f} to your wallet.')
                    
                except UserProfile.DoesNotExist:
                    print("DEBUG: UserProfile does not exist")
                    messages.error(request, 'User profile not found. Please contact support.')
                except Exception as e:
                    print(f"DEBUG: Error updating profile: {str(e)}")
                    messages.error(request, f'Error updating profile: {str(e)}')
                
        except (ValueError, TypeError) as e:
            print(f"DEBUG: Value/Type error: {str(e)}")
            messages.error(request, 'Please enter a valid amount.')
        except Exception as e:
            print(f"DEBUG: Unexpected error: {str(e)}")
            messages.error(request, f'An unexpected error occurred: {str(e)}')
    else:
        print("DEBUG: Non-POST request to update_wallet")
    
    return redirect('profile')

@login_required
def update_profile(request):
    if request.method == 'POST':
        try:
            user = request.user
            profile = user.profile
            
            # Update User model fields
            # The error is happening because we're not preserving the username
            user.username = user.username  # Keep the existing username
            user.email = request.POST.get('email')
            user.save()
            
            # Update UserProfile model fields
            profile.full_name = request.POST.get('full_name')
            profile.phone_number = request.POST.get('phone_number')
            profile.address = request.POST.get('address')
            profile.age = request.POST.get('age')
            
            # Handle government ID upload
            if 'government_id' in request.FILES:
                profile.government_id = request.FILES['government_id']
            
            profile.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
            return redirect('profile')
    
    return redirect('profile')

@login_required
def update_profile_photo(request):
    if request.method == 'POST' and request.FILES.get('profile_photo'):
        profile = request.user.profile
        profile.profile_photo = request.FILES['profile_photo']
        try:
            profile.save()
            messages.success(request, 'Profile photo updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating profile photo: {str(e)}')

    return redirect('profile')

@require_POST
def gemini_chat(request):
    try:
        # Log the start of the request
        logger.info("Gemini chat request received")
        
        # Parse the request body
        data = json.loads(request.body)
        user_message = data.get('message', '')
        logger.info(f"User message: {user_message}")
        
        # Check if Gemini API key is configured
        if not hasattr(settings, 'GEMINI_API_KEY') or not settings.GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not configured properly in settings")
            return JsonResponse({
                'success': False,
                'error': "API key not configured properly"
            })
            
        try:
            # Configure the Gemini API
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Create the model
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            # For portfolio analysis, add specific context
            if "Analyze this investment portfolio" in user_message:
                prompt = f"""You are a professional financial analyst. Please analyze the following portfolio data and provide a detailed report.
                Focus on providing actionable insights and clear recommendations.
                
                {user_message}
                
                Format the report in a clear, structured way with sections and bullet points where appropriate.
                Include specific recommendations based on the portfolio's current composition and market conditions."""
            else:
                prompt = user_message
            
            # Generate response from Gemini
            logger.info("Sending request to Gemini API")
            response = model.generate_content(prompt)
            logger.info("Received response from Gemini API")
            
            # Return the response
            return JsonResponse({
                'success': True,
                'response': response.text
            })
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
        
    except Exception as e:
        logger.error(f"Error in gemini_chat: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def stock_detail(request, symbol):
    # Initialize Finnhub client
    finnhub_client = finnhub.Client(api_key='cvam92hr01qsapma5g6gcvam92hr01qsapma5g70')
    
    # Get stock details
    quote = finnhub_client.quote(symbol)
    company_profile = finnhub_client.company_profile2(symbol=symbol)
    
    stock = {
        'symbol': symbol,
        'company_name': company_profile.get('name', symbol),
        'current_price': quote['c'],
        'price_change': round((quote['c'] - quote['pc']) / quote['pc'] * 100, 2),
    }
    
    return render(request, 'User/stock_detail.html', {'stock': stock})

@login_required
def buy_stock(request, symbol):
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 0))
            finnhub_client = finnhub.Client(api_key='cvam92hr01qsapma5g6gcvam92hr01qsapma5g70')
            quote = finnhub_client.quote(symbol)
            company_profile = finnhub_client.company_profile2(symbol=symbol)
            
            # Convert float to Decimal for precise calculations
            total_cost = Decimal(str(quantity * quote['c']))
            
            profile = request.user.profile
            if profile.wallet_balance >= total_cost:
                profile.wallet_balance -= total_cost
                profile.save()
                messages.success(request, f'Successfully purchased {quantity} shares of {symbol}')

                # Create transaction record with company name from profile
                StockTransaction.objects.create(
                    user=request.user,
                    symbol=symbol,
                    company_name=company_profile.get('name', symbol),  # Use company name from profile
                    transaction_type='BUY',
                    quantity=quantity,
                    price=quote['c'],
                    total_amount=total_cost
                )
            else:
                messages.error(request, 'Insufficient funds in wallet')
        except Exception as e:
            messages.error(request, str(e))
    
    return redirect('stock_detail', symbol=symbol)

@login_required
def sell_stock(request, symbol):
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 0))
            finnhub_client = finnhub.Client(api_key='cvam92hr01qsapma5g6gcvam92hr01qsapma5g70')
            quote = finnhub_client.quote(symbol)
            company_profile = finnhub_client.company_profile2(symbol=symbol)
            
            # Check if user has enough shares to sell
            user_transactions = StockTransaction.objects.filter(user=request.user, symbol=symbol)
            shares_owned = sum(
                t.quantity if t.transaction_type == 'BUY' else -t.quantity 
                for t in user_transactions
            )
            
            if shares_owned >= quantity:
                # Convert float to Decimal
                total_value = Decimal(str(quantity * quote['c']))
                
                profile = request.user.profile
                profile.wallet_balance += total_value
                profile.save()
                messages.success(request, f'Successfully sold {quantity} shares of {symbol}')

                # Create transaction record with company name from profile
                StockTransaction.objects.create(
                    user=request.user,
                    symbol=symbol,
                    company_name=company_profile.get('name', symbol),  # Use company name from profile
                    transaction_type='SELL',
                    quantity=quantity,
                    price=quote['c'],
                    total_amount=total_value
                )
            else:
                messages.error(request, f'Insufficient shares. You only have {shares_owned} shares of {symbol}')
        except Exception as e:
            messages.error(request, str(e))
    
    return redirect('stock_detail', symbol=symbol)

@login_required
def portfolio(request):
    holdings = []
    transactions = []
    finnhub_client = finnhub.Client(api_key='cvam92hr01qsapma5g6gcvam92hr01qsapma5g70')
    
    try:
        # Get all stock transactions for the user
        stock_transactions = StockTransaction.objects.filter(user=request.user).order_by('-created_at')
        
        # Calculate holdings
        holdings_dict = {}
        for transaction in stock_transactions:
            symbol = transaction.symbol
            if symbol not in holdings_dict:
                holdings_dict[symbol] = {
                    'symbol': symbol,
                    'company_name': transaction.company_name,
                    'quantity': 0,
                    'total_cost': Decimal('0')
                }
            
            # Update quantity and total cost based on transaction type
            if transaction.transaction_type == 'BUY':
                holdings_dict[symbol]['quantity'] += transaction.quantity
                holdings_dict[symbol]['total_cost'] += transaction.total_amount
            else:  # SELL
                holdings_dict[symbol]['quantity'] -= transaction.quantity
                holdings_dict[symbol]['total_cost'] -= transaction.total_amount
        
        # Get current prices and calculate profits
        for symbol, holding in holdings_dict.items():
            if holding['quantity'] > 0:  # Only show active holdings
                try:
                    quote = finnhub_client.quote(symbol)
                    current_price = Decimal(str(quote['c']))
                    average_price = holding['total_cost'] / holding['quantity']
                    total_value = current_price * holding['quantity']
                    profit_loss = total_value - holding['total_cost']
                    
                    holdings.append({
                        'symbol': symbol,
                        'company_name': holding['company_name'],
                        'quantity': holding['quantity'],
                        'average_price': round(float(average_price), 2),
                        'current_price': round(float(current_price), 2),
                        'total_value': round(float(total_value), 2),
                        'profit_loss': round(float(profit_loss), 2),
                        'profit_loss_percentage': round(float(profit_loss / holding['total_cost'] * 100), 2) if holding['total_cost'] else 0
                    })
                except Exception as e:
                    print(f"Error fetching quote for {symbol}: {e}")
        
        # Get recent transactions (last 10)
        transactions = stock_transactions[:10]
        
    except Exception as e:
        print(f"Error fetching portfolio data: {e}")
        messages.error(request, "Error loading portfolio data")
    
    context = {
        'holdings': holdings,
        'transactions': transactions,
    }
    return render(request, 'User/portfolio.html', context)

@login_required
@require_POST
def send_phone_verification(request):
    data = json.loads(request.body)
    phone_number = data.get('phone_number')
    
    if not phone_number:
        return JsonResponse({'success': False, 'error': 'Phone number is required'})
    
    # Generate a 6-digit OTP
    otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    # Store OTP with user ID
    OTP_STORE[request.user.id] = {
        'phone_number': phone_number,
        'otp': otp,
        'timestamp': datetime.now()
    }
    
    try:
        # Initialize Twilio client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # For trial accounts, we'll simulate sending the OTP instead of actually sending it
        # This avoids the "unverified number" error
        if settings.TWILIO_TRIAL_MODE:
            # Just log the OTP instead of sending it
            print(f"SIMULATED SMS to {phone_number}: Your ProfitPulse verification code is: {otp}")
            return JsonResponse({'success': True, 'message': 'OTP sent successfully (SIMULATED)'})
        else:
            # Send SMS with OTP for non-trial accounts
            message = client.messages.create(
                body=f"Your ProfitPulse verification code is: {otp}",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            return JsonResponse({'success': True, 'message': 'OTP sent successfully'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def verify_phone_otp(request):
    data = json.loads(request.body)
    phone_number = data.get('phone_number')
    otp = data.get('otp')
    
    if not phone_number or not otp:
        return JsonResponse({'success': False, 'error': 'Phone number and OTP are required'})
    
    # Get stored OTP data
    stored_data = OTP_STORE.get(request.user.id)
    
    if not stored_data:
        return JsonResponse({'success': False, 'error': 'No verification code was sent'})
    
    # Check if OTP matches and phone number matches
    if stored_data['otp'] == otp and stored_data['phone_number'] == phone_number:
        # OTP is valid, update user profile
        profile = request.user.profile
        profile.phone_number = phone_number
        profile.is_phone_verified = True
        profile.save()
        
        # Remove OTP from store
        del OTP_STORE[request.user.id]
        
        return JsonResponse({'success': True, 'message': 'Phone verified successfully'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid verification code'})

@login_required
def analyze_portfolio_pdf(request):
    if request.method == 'POST' and request.FILES.get('portfolio_pdf'):
        try:
            pdf_file = request.FILES['portfolio_pdf']
            
            # Read PDF content
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_file.read()))
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text()

            # Create prompt for Gemini
            prompt = f"""As an investment analyst, analyze this portfolio data from a PDF and provide:
            1. Current portfolio composition analysis
            2. Investment opportunities based on the current holdings
            3. Risk assessment and diversification suggestions
            4. Specific stock recommendations for future investment

            Portfolio Content:
            {text_content}

            Please provide a detailed, structured analysis with specific recommendations."""

            # Use Gemini API for analysis
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            
            # Get regular suggestions
            suggestion_details = get_stock_suggestions(request.user)
            
            context = {
                'suggestions': suggestion_details,
                'analysis_results': response.text
            }
            
            messages.success(request, 'Portfolio analysis completed successfully!')
            return render(request, 'User/suggestions.html', context)
            
        except Exception as e:
            logger.error(f"Error analyzing PDF: {str(e)}")
            messages.error(request, 'Error analyzing portfolio PDF. Please try again.')
            return redirect('suggestions')
    
    return redirect('suggestions')

# Helper function to get stock suggestions
def get_stock_suggestions(user):
    user_transactions = StockTransaction.objects.filter(user=user)
    user_stocks = set(transaction.symbol for transaction in user_transactions)
    
    finnhub_client = finnhub.Client(api_key='cvam92hr01qsapma5g6gcvam92hr01qsapma5g70')
    suggestion_details = []
    
    try:
        suggestions = []
        for symbol in user_stocks:
            try:
                company_profile = finnhub_client.company_profile2(symbol=symbol)
                if company_profile:
                    similar_companies = finnhub_client.company_peers(symbol)
                    if similar_companies:
                        suggestions.extend(similar_companies[:2])
            except Exception as e:
                logger.error(f"Error fetching peers for {symbol}: {str(e)}")
                pass  # Continue execution even if fetching peers fails

        # Ensure suggestions do not contain already owned stocks
        suggestions = list(set(suggestions) - set(user_stocks))[:5]

        for symbol in suggestions:
            try:
                company_data = finnhub_client.company_profile2(symbol=symbol)
                if company_data:
                    suggestion_details.append({
                        'symbol': symbol,
                        'name': company_data.get('name', ''),
                        'industry': company_data.get('finnhubIndustry', ''),
                        'logo': company_data.get('logo', ''),
                        'weburl': company_data.get('weburl', '')
                    })
            except Exception as e:
                logger.error(f"Error fetching company data for {symbol}: {str(e)}")
                pass  # Continue execution even if a company's data cannot be fetched
    
    except Exception as e:
        logger.error(f"Error generating stock suggestions: {str(e)}")
    
    return suggestion_details

@login_required
def suggestions(request):
    # Get user's portfolio data
    user_transactions = StockTransaction.objects.filter(user=request.user)
    user_stocks = set(transaction.symbol for transaction in user_transactions)
    
    # Initialize Finnhub client
    finnhub_client = finnhub.Client(api_key='cvam92hr01qsapma5g6gcvam92hr01qsapma5g70')
    
    # Get market data and generate suggestions
    suggestions = []
    try:
        # Example: Get similar stocks based on sector/industry
        for symbol in user_stocks:
            company_profile = finnhub_client.company_profile2(symbol=symbol)
            if company_profile:
                similar_companies = finnhub_client.company_peers(symbol)
                if similar_companies:
                    suggestions.extend(similar_companies[:2])  # Add top 2 similar companies
        
        # Remove duplicates and user's existing stocks
        suggestions = list(set(suggestions) - user_stocks)[:5]  # Show top 5 unique suggestions
        
        # Get company details for suggestions
        suggestion_details = []
        for symbol in suggestions:
            try:
                company_data = finnhub_client.company_profile2(symbol=symbol)
                if company_data:
                    suggestion_details.append({
                        'symbol': symbol,
                        'name': company_data.get('name', ''),
                        'industry': company_data.get('finnhubIndustry', ''),
                        'logo': company_data.get('logo', ''),
                        'weburl': company_data.get('weburl', '')
                    })
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error generating suggestions: {str(e)}")
        suggestion_details = []
    
    context = {
        'suggestions': suggestion_details
    }
    return render(request, 'User/suggestions.html', context)
