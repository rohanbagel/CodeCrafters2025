from django import forms
from .models import RiskProfile

class RiskProfileForm(forms.ModelForm):
    class Meta:
        model = RiskProfile
        fields = [
            'risk_tolerance', 
            'volatility_threshold', 
            'price_drop_threshold',
            'rsi_lower_threshold', 
            'rsi_upper_threshold',
            'email_alerts', 
            'in_app_alerts',
            'use_ai_exit_strategy', 
            'ai_confidence_threshold'
        ]
        widgets = {
            'risk_tolerance': forms.NumberInput(attrs={'class': 'form-range', 'min': '1', 'max': '10'}),
            'volatility_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'price_drop_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'rsi_lower_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'rsi_upper_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'ai_confidence_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        } 