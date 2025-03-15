from django.urls import path
from . import views

app_name = 'simulation'

urlpatterns = [
    path('', views.simulation_home, name='home'),
    path('handle-scenario/', views.handle_scenario, name='handle_scenario'),
] 