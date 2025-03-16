from django.urls import path
from . import views

app_name = 'insurance'

urlpatterns = [
    path('', views.insurance, name='insurance'),
    path('apply/', views.apply_insurance, name='apply_insurance'),
] 

