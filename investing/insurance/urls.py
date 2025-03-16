from django.urls import path
from . import views

app_name = 'insurance'

urlpatterns = [
    path('', views.insurance, name='insurance'),
    path('apply/', views.apply_insurance, name='apply_insurance'),
    path('compare/', views.compare_insurance, name='compare_insurance'),
    path('comparison-page/', views.comparison_page, name='comparison_page'),
    path('my-policies/', views.my_policies, name='my_policies'),
] 

