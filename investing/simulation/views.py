from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import UserWallet, SimulationScenario, UserProgress, WalletTransaction, Stock, StockHolding, StockTransaction
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from decimal import Decimal

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
