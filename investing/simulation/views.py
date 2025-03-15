from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import UserWallet, SimulationScenario, UserProgress
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

# Create your views here.

@ensure_csrf_cookie
@login_required
def simulation_home(request):
    # Get or create user wallet
    wallet, created = UserWallet.objects.get_or_create(user=request.user)
    
    # Get user's current progress
    progress = UserProgress.objects.filter(user=request.user)
    current_scenario = SimulationScenario.objects.filter(
        userprogress__user=request.user,
        userprogress__completed=False
    ).order_by('order').first()
    
    if not current_scenario:
        # If no incomplete scenario exists, get the first scenario
        current_scenario = SimulationScenario.objects.order_by('order').first()
        if current_scenario:
            UserProgress.objects.create(user=request.user, scenario=current_scenario)
    
    return render(request, 'simulation/simulation_home.html', {
        'wallet': wallet,
        'current_scenario': current_scenario,
    })

@login_required
def handle_scenario(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    scenario_id = request.POST.get('scenario_id')
    action = request.POST.get('action')
    
    scenario = SimulationScenario.objects.get(id=scenario_id)
    user_progress = UserProgress.objects.get(user=request.user, scenario=scenario)
    wallet = UserWallet.objects.get(user=request.user)
    
    if action == scenario.correct_action:
        # Update wallet balance
        wallet.balance += scenario.reward
        wallet.save()
        
        # Mark scenario as completed
        user_progress.completed = True
        user_progress.completed_at = timezone.now()
        user_progress.save()
        
        # Get next scenario
        next_scenario = SimulationScenario.objects.filter(
            order__gt=scenario.order
        ).order_by('order').first()
        
        if next_scenario:
            UserProgress.objects.create(user=request.user, scenario=next_scenario)
            
        return JsonResponse({
            'success': True,
            'reward': scenario.reward,
            'new_balance': wallet.balance,
            'next_scenario': {
                'id': next_scenario.id,
                'title': next_scenario.title,
                'description': next_scenario.description
            } if next_scenario else None
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Incorrect action. Try again!'
        })
