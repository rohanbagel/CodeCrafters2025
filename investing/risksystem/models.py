from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class RiskProfile(models.Model):
    """User's risk profile and preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='risk_profile')
    
    # Risk tolerance levels (1-10 scale)
    risk_tolerance = models.IntegerField(
        default=5, 
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="User's risk tolerance on a scale of 1-10 (1: very conservative, 10: very aggressive)"
    )
    
    # Alert thresholds
    volatility_threshold = models.FloatField(
        default=2.0,
        validators=[MinValueValidator(0.1)],
        help_text="Volatility threshold percentage that triggers alerts"
    )
    
    price_drop_threshold = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(0.1)],
        help_text="Price drop percentage that triggers alerts"
    )
    
    # Technical indicator thresholds
    rsi_lower_threshold = models.IntegerField(
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="RSI lower threshold that indicates oversold conditions"
    )
    
    rsi_upper_threshold = models.IntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="RSI upper threshold that indicates overbought conditions"
    )
    
    # Notification preferences
    email_alerts = models.BooleanField(default=True)
    in_app_alerts = models.BooleanField(default=True)
    
    # AI exit strategy preferences
    use_ai_exit_strategy = models.BooleanField(default=True)
    ai_confidence_threshold = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.1), MaxValueValidator(1.0)],
        help_text="Minimum confidence level for AI exit recommendations"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Risk Profile"


class StockAlert(models.Model):
    """Alerts generated for stocks based on risk parameters"""
    ALERT_TYPES = [
        ('VOLATILITY', 'High Volatility'),
        ('PRICE_DROP', 'Significant Price Drop'),
        ('RSI_OVERSOLD', 'RSI Oversold'),
        ('RSI_OVERBOUGHT', 'RSI Overbought'),
        ('MACD_BEARISH', 'MACD Bearish Crossover'),
        ('MACD_BULLISH', 'MACD Bullish Crossover'),
        ('BOLLINGER_LOWER', 'Price Below Lower Bollinger Band'),
        ('BOLLINGER_UPPER', 'Price Above Upper Bollinger Band'),
        ('AI_EXIT', 'AI Exit Recommendation'),
    ]
    
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('READ', 'Read'),
        ('ACTED', 'Acted Upon'),
        ('DISMISSED', 'Dismissed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_alerts')
    stock_symbol = models.CharField(max_length=10)
    stock_name = models.CharField(max_length=100)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField()
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    threshold_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='NEW')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.stock_symbol} - {self.get_alert_type_display()}"
    
    class Meta:
        ordering = ['-created_at']


class ExitStrategy(models.Model):
    """AI-generated exit strategies for stocks"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exit_strategies')
    stock_symbol = models.CharField(max_length=10)
    stock_name = models.CharField(max_length=100)
    entry_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    target_exit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stop_loss_price = models.DecimalField(max_digits=10, decimal_places=2)
    confidence_score = models.FloatField()
    reasoning = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.stock_symbol} Exit Strategy"
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name_plural = "Exit Strategies"
