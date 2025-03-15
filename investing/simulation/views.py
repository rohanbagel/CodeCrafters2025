from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import UserWallet, SimulationScenario, UserProgress, WalletTransaction, Stock, StockHolding, StockTransaction
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from decimal import Decimal
import json
import traceback
import google.generativeai as genai
from django.conf import settings
import logging
import yfinance as yf
import plotly.graph_objects as go
from plotly.offline import plot
import numpy as np
from sklearn import preprocessing, model_selection
from sklearn.linear_model import LinearRegression
import pandas as pd
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)

# Create your views here.

@ensure_csrf_cookie
@login_required
def simulation_home(request):
    # Get or create user wallet
    wallet, created = UserWallet.objects.get_or_create(user=request.user)
    
    # Get user's current progress
    progress = UserProgress.objects.filter(user=request.user)
    current_scenario = SimulationScenario.objects.filter(
        userprogress__user=request.user,
        userprogress__completed=False
    ).order_by('order').first()
    
    if not current_scenario:
        # If no incomplete scenario exists, get the first scenario
        current_scenario = SimulationScenario.objects.order_by('order').first()
        if current_scenario:
            UserProgress.objects.create(user=request.user, scenario=current_scenario)
    
    # Get recent transactions
    recent_transactions = WalletTransaction.objects.filter(
        wallet=wallet
    ).order_by('-created_at')[:5]
    
    return render(request, 'simulation/simulation_home.html', {
        'wallet': wallet,
        'current_scenario': current_scenario,
        'recent_transactions': recent_transactions,
    })

@login_required
def available_stocks(request):
    # Get or create stocks in the database
    stocks_data = [
        {'symbol': 'AAPL', 'name': 'Apple Inc.', 'price': '175.50', 'change': '+2.3%'},
        {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'price': '425.20', 'change': '+1.8%'},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'price': '150.75', 'change': '-0.5%'},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'price': '180.30', 'change': '+1.2%'},
        {'symbol': 'TSLA', 'name': 'Tesla, Inc.', 'price': '175.90', 'change': '-1.5%'},
    ]
    
    # Update or create stocks in database
    stocks = []
    for stock_data in stocks_data:
        stock, created = Stock.objects.update_or_create(
            symbol=stock_data['symbol'],
            defaults={
                'name': stock_data['name'],
                'current_price': Decimal(stock_data['price']),
                'price_change': stock_data['change']
            }
        )
        stocks.append(stock)
    
    wallet = UserWallet.objects.get(user=request.user)
    
    return render(request, 'simulation/available_stocks.html', {
        'stocks': stocks,
        'wallet': wallet,
    })

@login_required
def trade_stock(request, symbol):
    stock = get_object_or_404(Stock, symbol=symbol)
    wallet = UserWallet.objects.get(user=request.user)
    holding = StockHolding.objects.filter(wallet=wallet, stock=stock).first()
    
    # Calculate total value if holding exists
    total_value = holding.quantity * stock.current_price if holding else 0
    
    return render(request, 'simulation/trade_stock.html', {
        'stock': stock,
        'wallet': wallet,
        'holding': holding,
        'total_value': total_value,
    })

@login_required
def buy_stock(request, symbol):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    try:
        quantity = int(request.POST.get('quantity', 0))
        if quantity <= 0:
            messages.error(request, 'Please enter a valid quantity.')
            return redirect('simulation:trade_stock', symbol=symbol)
        
        stock = get_object_or_404(Stock, symbol=symbol)
        wallet = UserWallet.objects.get(user=request.user)
        
        total_cost = stock.current_price * Decimal(quantity)
        
        if not wallet.can_afford(total_cost):
            messages.error(request, 'Insufficient funds for this purchase.')
            return redirect('simulation:trade_stock', symbol=symbol)
        
        # Create or update holding
        holding, created = StockHolding.objects.get_or_create(
            wallet=wallet,
            stock=stock,
            defaults={'quantity': 0, 'average_price': 0}
        )
        
        # Update average price and quantity
        total_value = (holding.average_price * holding.quantity) + total_cost
        holding.quantity += quantity
        holding.average_price = total_value / holding.quantity
        holding.save()
        
        # Create stock transaction
        StockTransaction.objects.create(
            wallet=wallet,
            stock=stock,
            transaction_type='BUY',
            quantity=quantity,
            price_per_share=stock.current_price,
            total_amount=total_cost
        )
        
        # Deduct balance and create wallet transaction
        wallet.deduct_balance(total_cost)
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='STOCK_BUY',
            amount=total_cost,
            balance_after=wallet.balance,
            description=f'Bought {quantity} shares of {symbol}'
        )
        
        messages.success(request, f'Successfully purchased {quantity} shares of {symbol}')
        return redirect('simulation:available_stocks')
        
    except ValueError:
        messages.error(request, 'Please enter a valid quantity.')
        return redirect('simulation:trade_stock', symbol=symbol)

@login_required
def add_cash(request):
    wallet = UserWallet.objects.get(user=request.user)
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            if amount <= 0:
                messages.error(request, 'Please enter a positive amount.')
            elif amount > 1000000:  # Set a reasonable limit
                messages.error(request, 'Maximum deposit limit is $1,000,000.')
            else:
                transaction = wallet.add_cash(amount)
                if transaction:
                    messages.success(request, f'Successfully added ${amount:,.2f} to your virtual wallet.')
                    return redirect('simulation:home')
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid amount.')
    
    recent_transactions = WalletTransaction.objects.filter(
        wallet=wallet
    ).order_by('-created_at')[:5]
    
    return render(request, 'simulation/add_cash.html', {
        'wallet': wallet,
        'recent_transactions': recent_transactions,
    })

@login_required
def handle_scenario(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    scenario_id = request.POST.get('scenario_id')
    action = request.POST.get('action')
    
    scenario = SimulationScenario.objects.get(id=scenario_id)
    user_progress = UserProgress.objects.get(user=request.user, scenario=scenario)
    wallet = UserWallet.objects.get(user=request.user)
    
    if action == scenario.correct_action:
        # Update wallet balance
        wallet.balance += scenario.reward
        wallet.save()
        
        # Mark scenario as completed
        user_progress.completed = True
        user_progress.completed_at = timezone.now()
        user_progress.save()
        
        # Get next scenario
        next_scenario = SimulationScenario.objects.filter(
            order__gt=scenario.order
        ).order_by('order').first()
        
        if next_scenario:
            UserProgress.objects.create(user=request.user, scenario=next_scenario)
            
        return JsonResponse({
            'success': True,
            'reward': scenario.reward,
            'new_balance': wallet.balance,
            'next_scenario': {
                'id': next_scenario.id,
                'title': next_scenario.title,
                'description': next_scenario.description
            } if next_scenario else None
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Incorrect action. Try again!'
        })

@login_required
def transactions_overview(request):
    wallet = UserWallet.objects.get(user=request.user)
    
    # Get all stock holdings
    holdings = StockHolding.objects.filter(wallet=wallet).select_related('stock')
    
    # Get all stock transactions
    transactions = StockTransaction.objects.filter(
        wallet=wallet
    ).select_related('stock').order_by('-created_at')
    
    # Calculate profit/loss for each holding
    holdings_data = []
    for holding in holdings:
        current_value = holding.quantity * holding.stock.current_price
        invested_value = holding.quantity * holding.average_price
        profit_loss = current_value - invested_value
        profit_loss_percentage = (profit_loss / invested_value * 100) if invested_value > 0 else 0
        
        holdings_data.append({
            'holding': holding,
            'current_value': current_value,
            'invested_value': invested_value,
            'profit_loss': profit_loss,
            'profit_loss_percentage': profit_loss_percentage
        })
    
    # Calculate total portfolio value and profit/loss
    total_current_value = sum(data['current_value'] for data in holdings_data)
    total_invested_value = sum(data['invested_value'] for data in holdings_data)
    total_profit_loss = total_current_value - total_invested_value
    total_profit_loss_percentage = (total_profit_loss / total_invested_value * 100) if total_invested_value > 0 else 0
    
    return render(request, 'simulation/transactions.html', {
        'wallet': wallet,
        'holdings_data': holdings_data,
        'transactions': transactions,
        'total_current_value': total_current_value,
        'total_invested_value': total_invested_value,
        'total_profit_loss': total_profit_loss,
        'total_profit_loss_percentage': total_profit_loss_percentage,
    })

@login_required
def sell_stock(request, symbol):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    try:
        quantity = int(request.POST.get('quantity', 0))
        if quantity <= 0:
            messages.error(request, 'Please enter a valid quantity.')
            return redirect('simulation:trade_stock', symbol=symbol)
        
        stock = get_object_or_404(Stock, symbol=symbol)
        wallet = UserWallet.objects.get(user=request.user)
        holding = get_object_or_404(StockHolding, wallet=wallet, stock=stock)
        
        if holding.quantity < quantity:
            messages.error(request, 'You do not have enough shares to sell.')
            return redirect('simulation:trade_stock', symbol=symbol)
        
        total_value = stock.current_price * Decimal(quantity)
        
        # Update holding quantity
        holding.quantity -= quantity
        if holding.quantity == 0:
            holding.delete()  # Remove holding if no shares left
        else:
            holding.save()
        
        # Create stock transaction
        StockTransaction.objects.create(
            wallet=wallet,
            stock=stock,
            transaction_type='SELL',
            quantity=quantity,
            price_per_share=stock.current_price,
            total_amount=total_value
        )
        
        # Add balance and create wallet transaction
        wallet.balance += total_value
        wallet.save()
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='STOCK_SELL',
            amount=total_value,
            balance_after=wallet.balance,
            description=f'Sold {quantity} shares of {symbol}'
        )
        
        messages.success(request, f'Successfully sold {quantity} shares of {symbol}')
        return redirect('simulation:available_stocks')
        
    except ValueError:
        messages.error(request, 'Please enter a valid quantity.')
        return redirect('simulation:trade_stock', symbol=symbol)

@login_required
def reset_wallet(request):
    if request.method == 'POST':
        try:
            wallet = UserWallet.objects.get(user=request.user)
            if wallet.balance > 0:
                transaction = wallet.reset_balance()
                messages.success(request, 'Successfully reset your virtual wallet balance to $0.00')
            else:
                messages.info(request, 'Your wallet balance is already $0.00')
        except UserWallet.DoesNotExist:
            messages.error(request, 'Wallet not found. Please contact support.')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
    
    return redirect('simulation:add_cash')

@login_required
def statistics(request):
    wallet = UserWallet.objects.get(user=request.user)
    
    # Get all transactions ordered by date
    stock_transactions = StockTransaction.objects.filter(wallet=wallet).order_by('created_at')
    
    # Calculate portfolio value over time
    dates = []
    portfolio_values = []
    running_cash_balance = wallet.balance  # Start with current balance
    stock_holdings = {}  # Keep track of stock holdings: {symbol: {quantity, price}}
    
    # Process stock transactions chronologically
    for trans in stock_transactions:
        symbol = trans.stock.symbol
        
        if symbol not in stock_holdings:
            stock_holdings[symbol] = {'quantity': 0, 'price': 0}
        
        if trans.transaction_type == 'BUY':
            # Update cash balance
            running_cash_balance += trans.total_amount  # Add back the purchase amount
            
            # Update average price and quantity for buys
            current_value = stock_holdings[symbol]['quantity'] * stock_holdings[symbol]['price']
            new_value = trans.quantity * trans.price_per_share
            new_quantity = stock_holdings[symbol]['quantity'] + trans.quantity
            
            if new_quantity > 0:
                stock_holdings[symbol]['price'] = (current_value + new_value) / new_quantity
            stock_holdings[symbol]['quantity'] = new_quantity
        else:  # SELL
            # Update cash balance
            running_cash_balance -= trans.total_amount  # Subtract the sell proceeds
            
            # Update holdings
            stock_holdings[symbol]['quantity'] -= trans.quantity
            if stock_holdings[symbol]['quantity'] <= 0:
                stock_holdings[symbol]['quantity'] = 0
                stock_holdings[symbol]['price'] = 0
        
        # Calculate total portfolio value at this point
        stock_value = sum(
            holding['quantity'] * holding['price']
            for holding in stock_holdings.values()
        )
        total_value = running_cash_balance + stock_value
        
        dates.append(trans.created_at.strftime('%Y-%m-%d'))
        portfolio_values.append(float(total_value))
    
    # Add current point if there are no transactions
    if not dates:
        dates.append(timezone.now().strftime('%Y-%m-%d'))
        portfolio_values.append(float(wallet.balance))
    
    # Calculate profit/loss by stock
    holdings = StockHolding.objects.filter(wallet=wallet).select_related('stock')
    stock_symbols = []
    profit_loss_by_stock = []
    profit_loss_colors = []
    
    for holding in holdings:
        current_value = holding.quantity * holding.stock.current_price
        invested_value = holding.quantity * holding.average_price
        profit_loss = current_value - invested_value
        
        stock_symbols.append(holding.stock.symbol)
        profit_loss_by_stock.append(float(profit_loss))
        profit_loss_colors.append('#BFE953' if profit_loss >= 0 else '#ef4444')
    
    # Calculate transaction history
    transaction_dates = []
    buy_amounts = []
    sell_amounts = []
    
    for trans in stock_transactions:
        transaction_dates.append(trans.created_at.strftime('%Y-%m-%d'))
        if trans.transaction_type == 'BUY':
            buy_amounts.append(float(trans.total_amount))
            sell_amounts.append(0)
        else:
            buy_amounts.append(0)
            sell_amounts.append(float(trans.total_amount))
    
    # Calculate asset allocation
    total_value = sum(holding.quantity * holding.stock.current_price for holding in holdings)
    allocation_labels = []
    allocation_data = []
    allocation_colors = ['#BFE953', '#ef4444', '#3b82f6', '#f59e0b', '#8b5cf6']
    
    for i, holding in enumerate(holdings):
        value = holding.quantity * holding.stock.current_price
        percentage = (value / total_value * 100) if total_value > 0 else 0
        allocation_labels.append(holding.stock.symbol)
        allocation_data.append(float(percentage))
    
    # Calculate total profit/loss and ROI
    total_invested = sum(holding.quantity * holding.average_price for holding in holdings)
    total_current = sum(holding.quantity * holding.stock.current_price for holding in holdings)
    total_profit_loss = total_current - total_invested
    total_roi = ((total_current / total_invested) * 100 - 100) if total_invested > 0 else 0
    
    context = {
        'wallet': wallet,
        'total_value': total_current,
        'total_profit_loss': total_profit_loss,
        'total_roi': total_roi,
        'dates': dates,
        'portfolio_values': portfolio_values,
        'stock_symbols': stock_symbols,
        'profit_loss_by_stock': profit_loss_by_stock,
        'profit_loss_colors': profit_loss_colors,
        'transaction_dates': transaction_dates,
        'buy_amounts': buy_amounts,
        'sell_amounts': sell_amounts,
        'allocation_labels': allocation_labels,
        'allocation_data': allocation_data,
        'allocation_colors': allocation_colors,
    }
    
    return render(request, 'simulation/statistics.html', context)

@login_required
def get_ai_analysis(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    try:
        # Check if Gemini API key is configured
        if not hasattr(settings, 'GEMINI_API_KEY') or not settings.GEMINI_API_KEY:
            return JsonResponse({
                'success': False,
                'error': 'Gemini API key not configured',
                'response': 'The AI analysis feature is currently unavailable. Please configure the Gemini API key.'
            })

        wallet = UserWallet.objects.get(user=request.user)
        holdings = StockHolding.objects.filter(wallet=wallet).select_related('stock')
        
        # Prepare portfolio data for AI analysis
        portfolio_data = []
        total_value = Decimal('0')
        
        for holding in holdings:
            current_value = holding.quantity * holding.stock.current_price
            invested_value = holding.quantity * holding.average_price
            profit_loss = current_value - invested_value
            profit_loss_percentage = (profit_loss / invested_value * 100) if invested_value > 0 else 0
            
            portfolio_data.append({
                'symbol': holding.stock.symbol,
                'quantity': holding.quantity,
                'current_price': float(holding.stock.current_price),
                'average_price': float(holding.average_price),
                'profit_loss_percentage': float(profit_loss_percentage)
            })
            
            total_value += current_value
        
        # If no holdings, return appropriate message
        if not portfolio_data:
            return JsonResponse({
                'success': True,
                'response': 'Your portfolio is currently empty. Start by buying some stocks to receive AI analysis.'
            })

        # Prepare prompt for Gemini
        prompt = f"""As a financial advisor, analyze this investment portfolio and provide insights:

Portfolio Summary:
Total Value: ${total_value:,.2f}
Holdings:
{json.dumps(portfolio_data, indent=2)}

Please provide:
1. Overall portfolio performance analysis
2. Risk assessment
3. Diversification analysis
4. Specific recommendations for improvement
5. Market outlook for these holdings

Keep the response concise and focused on actionable insights."""

        try:
            # Get Gemini's analysis
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            response = model.generate_content(prompt)
            
            return JsonResponse({
                'success': True,
                'response': response.text
            })
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error connecting to AI service',
                'response': 'Unable to generate AI analysis at this time. Please try again later.'
            })
        
    except Exception as e:
        logger.error(f"Error in AI analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def predict_stock(request, symbol):
    try:
        # Define valid tickers for our simulation
        VALID_TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        
        if symbol not in VALID_TICKERS:
            messages.error(request, f'Invalid ticker symbol. Please choose from: {", ".join(VALID_TICKERS)}')
            return redirect('simulation:available_stocks')
        
        # Redirect to the prediction display page
        return redirect('simulation:show_prediction', symbol=symbol)
        
    except Exception as e:
        messages.error(request, f'Error accessing stock prediction: {str(e)}')
        return redirect('simulation:available_stocks')

@login_required
def show_prediction(request, symbol):
    try:
        # Define valid tickers for our simulation
        VALID_TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        
        if symbol not in VALID_TICKERS:
            messages.error(request, f'Invalid ticker symbol. Please choose from: {", ".join(VALID_TICKERS)}')
            return redirect('simulation:available_stocks')
        
        stock = get_object_or_404(Stock, symbol=symbol)
        
        # Fetch historical data with error handling
        try:
            df = yf.download(tickers=symbol, period='3mo', interval='1d')
            if df.empty:
                raise ValueError(f"No data available for {symbol}")
            
            # Debug log to see available columns
            logger.info(f"Available columns: {df.columns.tolist()}")
            
            # Create candlestick chart
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Market Data'
            ))
            
            fig.update_layout(
                title=f'{symbol} Stock Price Evolution',
                yaxis_title='Stock Price (USD)',
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            
            # Use 'Close' instead of 'Adj Close'
            df_ml = df[['Close']].copy()
            forecast_out = 7  # Predict next 7 days
            df_ml['Prediction'] = df_ml[['Close']].shift(-forecast_out)
            
            # Prepare features
            X = np.array(df_ml.drop(columns=['Prediction']))
            X = preprocessing.scale(X)
            X_forecast = X[-forecast_out:]
            X = X[:-forecast_out]
            y = np.array(df_ml['Prediction'])
            y = y[:-forecast_out]
            
            # Split data
            X_train, X_test, y_train, y_test = model_selection.train_test_split(X, y, test_size=0.2)
            
            # Train model
            clf = LinearRegression()
            clf.fit(X_train, y_train)
            confidence = clf.score(X_test, y_test)
            
            # Make predictions
            forecast_prediction = clf.predict(X_forecast)
            
            # Create prediction chart
            dates = [datetime.now() + timedelta(days=x) for x in range(forecast_out)]
            pred_fig = go.Figure()
            pred_fig.add_trace(go.Scatter(
                x=dates,
                y=forecast_prediction,
                mode='lines+markers',
                name='Predicted Price',
                line=dict(color='#BFE953')
            ))
            
            pred_fig.update_layout(
                title=f'{symbol} Price Prediction (Next {forecast_out} Days)',
                yaxis_title='Predicted Price (USD)',
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            
            plot_div_pred = plot(pred_fig, output_type='div', include_plotlyjs=False)
            
            # Get the last closing price using proper pandas indexing and convert to float
            last_close = float(df['Close'].iloc[-1])
            
            # Convert forecast prediction to list of floats
            forecast_prediction_list = [float(x) for x in forecast_prediction]
            
            context = {
                'stock': stock,
                'plot_div': plot(fig, output_type='div', include_plotlyjs=True),
                'plot_div_pred': plot_div_pred,
                'confidence': round(confidence * 100, 2),
                'forecast': forecast_prediction_list,
                'current_price': last_close,
                'predicted_price': float(forecast_prediction[-1]),
                'price_change': round(((float(forecast_prediction[-1]) - last_close) / last_close) * 100, 2)
            }
            
            return render(request, 'simulation/predict_stock.html', context)
        
        except Exception as e:
            logger.error(f"Error in prediction calculation: {str(e)}\n{traceback.format_exc()}")
            messages.error(request, f'Error calculating stock prediction: {str(e)}')
            return redirect('simulation:available_stocks')
        
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        logger.error(traceback.format_exc())
        messages.error(request, f'Error accessing stock prediction: {str(e)}')
        return redirect('simulation:available_stocks')
