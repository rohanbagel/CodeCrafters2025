from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserWallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=10000.00)
    created_at = models.DateTimeField(auto_now_add=True)
    
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
