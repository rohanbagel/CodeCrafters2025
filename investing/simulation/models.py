from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

# Create your models here.

class UserWallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=10000.00)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def add_cash(self, amount):
        if amount > 0:
            self.balance += Decimal(amount)
            transaction = WalletTransaction.objects.create(
                wallet=self,
                transaction_type='DEPOSIT',
                amount=amount,
                balance_after=self.balance
            )
            self.save()
            return transaction
        return None

    def can_afford(self, amount):
        return self.balance >= amount

    def deduct_balance(self, amount):
        if self.can_afford(amount):
            self.balance -= amount
            self.save()
            return True
        return False

class Stock(models.Model):
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_change = models.CharField(max_length=10)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.symbol} - {self.name}"

class StockHolding(models.Model):
    wallet = models.ForeignKey(UserWallet, on_delete=models.CASCADE, related_name='holdings')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    average_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ('wallet', 'stock')
    
    def __str__(self):
        return f"{self.wallet.user.username}'s {self.stock.symbol} holding"

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Cash Deposit'),
        ('WITHDRAWAL', 'Cash Withdrawal'),
        ('STOCK_BUY', 'Stock Purchase'),
        ('STOCK_SELL', 'Stock Sale'),
    ]
    
    wallet = models.ForeignKey(UserWallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']

class StockTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    
    wallet = models.ForeignKey(UserWallet, on_delete=models.CASCADE, related_name='stock_transactions')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    price_per_share = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.stock.symbol} @ ${self.price_per_share}"

class SimulationScenario(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.IntegerField()
    correct_action = models.CharField(max_length=100)
    reward = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scenario = models.ForeignKey(SimulationScenario, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
