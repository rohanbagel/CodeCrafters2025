from django.db import models

# Create your models here.

class StockPreference(models.Model):
    symbol = models.CharField(max_length=10)
    company_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.company_name} ({self.symbol})"
