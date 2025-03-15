from django.contrib import admin
from .models import StockPreference, UserProfile

# Register your models here.
admin.site.register(StockPreference)
admin.site.register(UserProfile)
