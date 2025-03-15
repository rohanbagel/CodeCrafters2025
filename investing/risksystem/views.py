from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST
import json
import finnhub
import pandas as pd
import numpy as np
import google.generativeai as genai
from datetime import datetime, timedelta
import logging
import yfinance as yf
import time
import random

from .models import RiskProfile, StockAlert, ExitStrategy
from .forms import RiskProfileForm

logger = logging.getLogger(__name__)

# Configure Finnhub client
finnhub_client = finnhub.Client(api_key=settings.FINNHUB_API_KEY)

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

@login_required
def risk_dashboard(request):
    """Main risk management dashboard"""
    # Get or create user's risk profile
    risk_profile, created = RiskProfile.objects.get_or_create(user=request.user)
    
    # Get recent alerts
    alerts = StockAlert.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    # Get exit strategies
    exit_strategies = ExitStrategy.objects.filter(user=request.user).order_by('-updated_at')[:5]
    
    context = {
        'risk_profile': risk_profile,
        'alerts': alerts,
        'exit_strategies': exit_strategies,
    }
    
    return render(request, 'risksystem/dashboard.html', context)

@login_required
def risk_profile_settings(request):
    """Update risk profile settings"""
    risk_profile, created = RiskProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = RiskProfileForm(request.POST, instance=risk_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Risk profile updated successfully!')
            return redirect('risk_dashboard')
    else:
        form = RiskProfileForm(instance=risk_profile)
    
    return render(request, 'risksystem/risk_profile_settings.html', {'form': form})

@login_required
def stock_alerts(request):
    """View all stock alerts"""
    alerts = StockAlert.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'risksystem/alerts.html', {'alerts': alerts})

@login_required
def exit_strategies(request):
    """View all exit strategies"""
    strategies = ExitStrategy.objects.filter(user=request.user).order_by('-updated_at')
    
    # Check if a specific symbol needs to be generated
    symbol = request.GET.get('generate')
    if symbol:
        try:
            # Get stock data
            stock_data = get_stock_data(symbol)
            
            # Calculate technical indicators
            indicators = calculate_technical_indicators(symbol)
            
            # Generate exit strategy
            exit_strategy = generate_exit_strategy(request.user, symbol, stock_data, indicators)
            
            if exit_strategy:
                messages.success(request, f"Exit strategy for {symbol} generated successfully!")
            else:
                messages.error(request, f"Failed to generate exit strategy for {symbol}. Please try again later.")
                
            return redirect('exit_strategies')
        except Exception as e:
            messages.error(request, f"Error generating exit strategy: {str(e)}")
    
    return render(request, 'risksystem/exit_strategies.html', {'strategies': strategies})

@login_required
def analyze_stock_risk(request, symbol):
    """Analyze risk for a specific stock"""
    try:
        # Get stock data
        stock_data = get_stock_data(symbol)
        
        # Get user's risk profile
        risk_profile = RiskProfile.objects.get(user=request.user)
        
        # Calculate technical indicators
        indicators = calculate_technical_indicators(symbol)
        
        # Check for risk alerts
        alerts = check_risk_alerts(request.user, symbol, stock_data, indicators, risk_profile)
        
        # Generate AI exit strategy if enabled
        exit_strategy = None
        if risk_profile.use_ai_exit_strategy:
            exit_strategy = generate_exit_strategy(request.user, symbol, stock_data, indicators)
        
        context = {
            'symbol': symbol,
            'stock_data': stock_data,
            'indicators': indicators,
            'alerts': alerts,
            'exit_strategy': exit_strategy,
        }
        
        return render(request, 'risksystem/stock_analysis.html', context)
        
    except Exception as e:
        logger.error(f"Error analyzing stock {symbol}: {str(e)}")
        messages.error(request, f"Error analyzing stock: {str(e)}")
        return redirect('risk_dashboard')

@require_POST
def mark_alert_read(request):
    """Mark an alert as read"""
    try:
        data = json.loads(request.body)
        alert_id = data.get('alert_id')
        
        alert = get_object_or_404(StockAlert, id=alert_id, user=request.user)
        alert.status = 'READ'
        alert.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
def dismiss_alert(request):
    """Dismiss an alert"""
    try:
        data = json.loads(request.body)
        alert_id = data.get('alert_id')
        
        alert = get_object_or_404(StockAlert, id=alert_id, user=request.user)
        alert.status = 'DISMISSED'
        alert.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Helper functions
def get_stock_data(symbol):
    """Get stock data from Finnhub or fall back to Yahoo Finance"""
    try:
        # Try Finnhub first
        quote = finnhub_client.quote(symbol)
        profile = finnhub_client.company_profile2(symbol=symbol)
        
        return {
            'name': profile.get('name', symbol),
            'current_price': quote['c'],
            'previous_close': quote['pc'],
            'open': quote['o'],
            'high': quote['h'],
            'low': quote['l'],
            'percent_change': ((quote['c'] - quote['pc']) / quote['pc']) * 100,
        }
    except Exception as e:
        logger.warning(f"Error fetching stock data from Finnhub for {symbol}: {str(e)}")
        logger.info(f"Falling back to Yahoo Finance for {symbol}")
        
        # Fall back to Yahoo Finance
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="2d")
            
            return {
                'name': info.get('shortName', symbol),
                'current_price': info.get('currentPrice', hist['Close'].iloc[-1]),
                'previous_close': info.get('previousClose', hist['Close'].iloc[-2] if len(hist) > 1 else hist['Close'].iloc[-1]),
                'open': info.get('open', hist['Open'].iloc[-1]),
                'high': info.get('dayHigh', hist['High'].iloc[-1]),
                'low': info.get('dayLow', hist['Low'].iloc[-1]),
                'percent_change': info.get('regularMarketChangePercent', 
                                          ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100) if len(hist) > 1 else 0),
            }
        except Exception as yf_error:
            logger.error(f"Error fetching stock data from Yahoo Finance for {symbol}: {str(yf_error)}")
            raise Exception(f"Could not fetch stock data for {symbol} from any source")

def calculate_technical_indicators(symbol):
    """Calculate technical indicators using Yahoo Finance data with improved error handling"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Get historical data from Yahoo Finance with increased timeout
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="60d", timeout=20)
            
            if hist.empty:
                raise Exception(f"No historical data available for {symbol}")
            
            # Convert index to UTC to avoid timezone comparison issues
            hist.index = hist.index.tz_localize(None)
            
            # Calculate RSI
            delta = hist['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            
            # Handle division by zero
            avg_loss = avg_loss.replace(0, 0.001)
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # Calculate MACD
            exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
            exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            
            # Calculate Bollinger Bands
            sma = hist['Close'].rolling(window=20).mean()
            std = hist['Close'].rolling(window=20).std()
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
            
            # Calculate volatility
            volatility = hist['Close'].pct_change().rolling(window=20).std() * np.sqrt(252) * 100
            
            # Check for bearish/bullish crossovers
            is_bearish_crossover = False
            is_bullish_crossover = False
            
            if len(macd) >= 2 and len(signal) >= 2:
                is_bearish_crossover = macd.iloc[-2] > signal.iloc[-2] and macd.iloc[-1] < signal.iloc[-1]
                is_bullish_crossover = macd.iloc[-2] < signal.iloc[-2] and macd.iloc[-1] > signal.iloc[-1]
            
            # Check if price is above upper Bollinger Band
            is_above_upper = hist['Close'].iloc[-1] > upper_band.iloc[-1] if not pd.isna(upper_band.iloc[-1]) else False
            
            # Get volatility value
            volatility_value = float(volatility.iloc[-1]) if not pd.isna(volatility.iloc[-1]) else 15
            
            return {
                'dataframe': hist,  # Add the dataframe to the returned dictionary
                'rsi': {
                    'value': float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50,
                    'previous': float(rsi.iloc[-2]) if len(rsi) > 1 and not pd.isna(rsi.iloc[-2]) else 50,
                    'oversold': float(rsi.iloc[-1]) < 30 if not pd.isna(rsi.iloc[-1]) else False,
                    'overbought': float(rsi.iloc[-1]) > 70 if not pd.isna(rsi.iloc[-1]) else False,
                },
                'macd': {
                    'macd': float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else 0,
                    'signal': float(signal.iloc[-1]) if not pd.isna(signal.iloc[-1]) else 0,
                    'histogram': float(macd.iloc[-1] - signal.iloc[-1]) if not pd.isna(macd.iloc[-1]) and not pd.isna(signal.iloc[-1]) else 0,
                    'bullish': float(macd.iloc[-1]) > float(signal.iloc[-1]) if not pd.isna(macd.iloc[-1]) and not pd.isna(signal.iloc[-1]) else False,
                    'bearish': float(macd.iloc[-1]) < float(signal.iloc[-1]) if not pd.isna(macd.iloc[-1]) and not pd.isna(signal.iloc[-1]) else False,
                    'is_bearish_crossover': is_bearish_crossover,
                    'is_bullish_crossover': is_bullish_crossover,
                },
                'bollinger': {
                    'upper': float(upper_band.iloc[-1]) if not pd.isna(upper_band.iloc[-1]) else 0,
                    'middle': float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else 0,
                    'lower': float(lower_band.iloc[-1]) if not pd.isna(lower_band.iloc[-1]) else 0,
                    'width': float((upper_band.iloc[-1] - lower_band.iloc[-1]) / sma.iloc[-1]) if not pd.isna(upper_band.iloc[-1]) and not pd.isna(lower_band.iloc[-1]) and not pd.isna(sma.iloc[-1]) and sma.iloc[-1] != 0 else 0,
                    'percent_b': float((hist['Close'].iloc[-1] - lower_band.iloc[-1]) / (upper_band.iloc[-1] - lower_band.iloc[-1])) if not pd.isna(upper_band.iloc[-1]) and not pd.isna(lower_band.iloc[-1]) and not pd.isna(hist['Close'].iloc[-1]) and (upper_band.iloc[-1] - lower_band.iloc[-1]) != 0 else 0.5,
                    'is_above_upper': is_above_upper,
                },
                'volatility': volatility_value,
            }
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {symbol}: {str(e)}")
            retry_count += 1
            
            if retry_count < max_retries:
                # Add exponential backoff with jitter
                sleep_time = (2 ** retry_count) + random.uniform(0, 1)
                logger.info(f"Retrying in {sleep_time:.2f} seconds... (Attempt {retry_count} of {max_retries})")
                time.sleep(sleep_time)
            else:
                # Return default values if all retries fail
                return {
                    'dataframe': pd.DataFrame(),  # Empty dataframe as fallback
                    'rsi': {'value': 50, 'previous': 50, 'oversold': False, 'overbought': False},
                    'macd': {
                        'macd': 0, 'signal': 0, 'histogram': 0, 
                        'bullish': False, 'bearish': False,
                        'is_bearish_crossover': False, 'is_bullish_crossover': False
                    },
                    'bollinger': {'upper': 0, 'middle': 0, 'lower': 0, 'width': 0, 'percent_b': 0.5, 'is_above_upper': False},
                    'volatility': 15,
                }

def check_risk_alerts(user, symbol, stock_data, indicators, risk_profile):
    """Check for risk alerts based on technical indicators and user preferences"""
    alerts = []
    
    # Get company name
    company_name = stock_data['name']
    current_price = stock_data['current_price']
    
    # Check price drop
    percent_change = stock_data['percent_change']
    if percent_change < -risk_profile.price_drop_threshold:
        alert = StockAlert.objects.create(
            user=user,
            stock_symbol=symbol,
            stock_name=company_name,
            alert_type='PRICE_DROP',
            message=f"{symbol} has dropped by {abs(percent_change):.2f}%, exceeding your threshold of {risk_profile.price_drop_threshold}%.",
            current_price=current_price,
            threshold_value=risk_profile.price_drop_threshold
        )
        alerts.append(alert)
        
        # Send email alert if enabled
        if risk_profile.email_alerts:
            send_alert_email(user, alert)
    
    # Check RSI oversold
    if indicators['rsi']['value'] < risk_profile.rsi_lower_threshold:
        alert = StockAlert.objects.create(
            user=user,
            stock_symbol=symbol,
            stock_name=company_name,
            alert_type='RSI_OVERSOLD',
            message=f"{symbol} RSI is at {indicators['rsi']['value']:.2f}, below your oversold threshold of {risk_profile.rsi_lower_threshold}.",
            current_price=current_price,
            threshold_value=risk_profile.rsi_lower_threshold
        )
        alerts.append(alert)
        
        if risk_profile.email_alerts:
            send_alert_email(user, alert)
    
    # Check RSI overbought
    if indicators['rsi']['value'] > risk_profile.rsi_upper_threshold:
        alert = StockAlert.objects.create(
            user=user,
            stock_symbol=symbol,
            stock_name=company_name,
            alert_type='RSI_OVERBOUGHT',
            message=f"{symbol} RSI is at {indicators['rsi']['value']:.2f}, above your overbought threshold of {risk_profile.rsi_upper_threshold}.",
            current_price=current_price,
            threshold_value=risk_profile.rsi_upper_threshold
        )
        alerts.append(alert)
        
        if risk_profile.email_alerts:
            send_alert_email(user, alert)
    
    # Check MACD bearish crossover
    if indicators['macd']['is_bearish_crossover']:
        alert = StockAlert.objects.create(
            user=user,
            stock_symbol=symbol,
            stock_name=company_name,
            alert_type='MACD_BEARISH',
            message=f"{symbol} has formed a bearish MACD crossover, which may indicate a potential downtrend.",
            current_price=current_price
        )
        alerts.append(alert)
        
        if risk_profile.email_alerts:
            send_alert_email(user, alert)
    
    # Check Bollinger Bands
    if indicators['bollinger']['is_above_upper']:
        alert = StockAlert.objects.create(
            user=user,
            stock_symbol=symbol,
            stock_name=company_name,
            alert_type='BOLLINGER_UPPER',
            message=f"{symbol} price is above the upper Bollinger Band, indicating potential overbought conditions.",
            current_price=current_price,
            threshold_value=indicators['bollinger']['upper']
        )
        alerts.append(alert)
        
        if risk_profile.email_alerts:
            send_alert_email(user, alert)
    
    return alerts

def generate_exit_strategy(user, symbol, stock_data, indicators):
    """Generate AI-powered exit strategy using Gemini API"""
    try:
        # Get current price
        current_price = stock_data['current_price']
        
        # Prepare data for AI analysis
        data_summary = {
            'symbol': symbol,
            'name': stock_data['name'],
            'current_price': current_price,
            'percent_change': stock_data['percent_change'],
            'rsi': indicators['rsi']['value'],
            'macd': indicators['macd']['macd'],
            'signal': indicators['macd']['signal'],
            'bollinger_upper': indicators['bollinger']['upper'],
            'bollinger_lower': indicators['bollinger']['lower'],
            'volatility': indicators['volatility'],
        }
        
        # Create prompt for Gemini
        prompt = f"""
        As a financial AI advisor, analyze this stock and provide an exit strategy recommendation:
        
        Stock: {symbol} ({stock_data['name']})
        Current Price: ${current_price}
        Recent Performance: {stock_data['percent_change']}% change
        
        Technical Indicators:
        - RSI: {indicators['rsi']['value']:.2f}
        - MACD: {indicators['macd']['macd']:.4f}
        - MACD Signal: {indicators['macd']['signal']:.4f}
        - Bollinger Upper: ${indicators['bollinger']['upper']:.2f}
        - Bollinger Lower: ${indicators['bollinger']['lower']:.2f}
        - Volatility: {indicators['volatility']:.4f}
        
        Based on these indicators, provide:
        1. A recommended exit strategy (hold, sell partially, or sell completely)
        2. A target exit price
        3. A recommended stop-loss price
        4. A confidence score (0.0-1.0) for your recommendation
        5. Brief reasoning for your recommendation
        
        Format your response as JSON with the following structure:
        {{
            "recommendation": "hold|sell_partial|sell_all",
            "target_price": float,
            "stop_loss": float,
            "confidence": float,
            "reasoning": "string"
        }}
        
        Do not include markdown code block formatting in your response. Just return the raw JSON.
        """
        
        # Generate response from Gemini
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        # Parse JSON response
        try:
            response_text = response.text
            
            # Clean up the response if it contains markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1]
            if "```" in response_text:
                response_text = response_text.split("```")[0]
                
            # Strip any leading/trailing whitespace
            response_text = response_text.strip()
            
            # Parse the JSON
            result = json.loads(response_text)
            
            # Create or update exit strategy
            exit_strategy, created = ExitStrategy.objects.update_or_create(
                user=user,
                stock_symbol=symbol,
                defaults={
                    'stock_name': stock_data['name'],
                    'entry_price': current_price,  # Assuming current price as entry for simplicity
                    'current_price': current_price,
                    'target_exit_price': result['target_price'],
                    'stop_loss_price': result['stop_loss'],
                    'confidence_score': result['confidence'],
                    # 'recommendation': result['recommendation'],
                    'reasoning': result['reasoning']
                }
            )
            
            return exit_strategy
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Gemini response for {symbol}: {response.text}")
            logger.error(f"JSON decode error: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating exit strategy for {symbol}: {str(e)}")
        return None

def send_alert_email(user, alert):
    """Send email alert to user"""
    try:
        subject = f'Risk Alert: {alert.get_alert_type_display()} for {alert.stock_symbol}'
        
        # Render email template
        html_message = render_to_string('risksystem/email/alert_email.html', {
            'user': user,
            'alert': alert
        })
        
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Sent risk alert email to {user.email} for {alert.stock_symbol}")
        
    except Exception as e:
        logger.error(f"Error sending alert email: {str(e)}")
