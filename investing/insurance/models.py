from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class InsurancePlan(models.Model):
    INSURANCE_TYPES = [
        ('LIFE', 'Life Insurance'),
        ('HEALTH', 'Health Insurance'),
        ('ASSET', 'Asset Insurance'),
    ]
    
    name = models.CharField(max_length=100)
    insurance_type = models.CharField(max_length=10, choices=INSURANCE_TYPES)
    provider = models.CharField(max_length=100)
    description = models.TextField()
    coverage_amount = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_premium = models.DecimalField(max_digits=10, decimal_places=2)
    term_years = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_insurance_type_display()}"

class UserInsurance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    insurance_plan = models.ForeignKey(InsurancePlan, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, default='ACTIVE')
    
    def __str__(self):
        return f"{self.user.username} - {self.insurance_plan.name}"
