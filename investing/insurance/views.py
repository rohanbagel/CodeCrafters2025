from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import finnhub
from decimal import Decimal
from .models import InsurancePlan, UserInsurance
import logging
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)

@login_required
def insurance(request):
    try:
        # Initialize Finnhub client
        finnhub_client = finnhub.Client(api_key=settings.FINNHUB_INSURANCE_API_KEY)
        
        # List of major insurance companies' symbols
        insurance_symbols = [
            'PRU',  # Prudential
            'MET',  # MetLife
            'AIG',  # American International Group
            'AFL',  # Aflac
            'UNM',  # Unum Group
            'CNO',  # CNO Financial
            'RGA',  # Reinsurance Group
            'GL',   # Globe Life
            'LNC',  # Lincoln National
            'PFG'   # Principal Financial
        ]
        
        companies_data = []
        
        for symbol in insurance_symbols:
            try:
                company_profile = finnhub_client.company_profile2(symbol=symbol)
                company_quote = finnhub_client.quote(symbol)
                
                if company_profile and company_quote:
                    # Calculate premiums based on market cap and current stock price
                    market_cap = company_profile.get('marketCapitalization', 0)
                    current_price = company_quote.get('c', 0)
                    base_premium = round((market_cap * current_price) / 10000000, 2)
                    
                    # Generate varied plans with realistic values
                    companies_data.append({
                        'symbol': symbol,
                        'name': company_profile.get('name', ''),
                        'logo': company_profile.get('logo', ''),
                        'plans': {
                            'life': {
                                'name': f"{company_profile.get('name')} Life Shield",
                                'coverage': round(market_cap * 0.001, 2),
                                'premium': base_premium,
                                'term': 20
                            },
                            'health': {
                                'name': f"{company_profile.get('name')} Health Care Plus",
                                'coverage': round(market_cap * 0.0005, 2),
                                'premium': round(base_premium * 0.8, 2),
                                'term': 1
                            },
                            'asset': {
                                'name': f"{company_profile.get('name')} Asset Protect",
                                'coverage': round(market_cap * 0.0008, 2),
                                'premium': round(base_premium * 0.6, 2),
                                'term': 5
                            }
                        },
                        'metrics': {
                            'market_cap': market_cap,
                            'price': current_price,
                            'change': company_quote.get('dp', 0),
                            'rating': company_profile.get('finnhubIndustry', '')
                        }
                    })
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {str(e)}")
                continue

        # Sort companies by market cap for better presentation
        companies_data = sorted(companies_data, key=lambda x: x['metrics']['market_cap'], reverse=True)
        
        context = {
            'companies': companies_data[:8],  # Take top 8 companies
            'insurance_types': InsurancePlan.INSURANCE_TYPES,
            'total_companies': len(companies_data)
        }
        return render(request, 'insurance/insurance.html', context)
        
    except Exception as e:
        logger.error(f"Error in insurance view: {str(e)}")
        context = {
            'error': 'Unable to load insurance plans at this time.'
        }
        return render(request, 'insurance/insurance.html', context)

@login_required
def apply_insurance(request):
    if request.method == 'POST':
        try:
            plan_data = {
                'company': request.POST.get('company'),
                'plan_type': request.POST.get('plan_type'),
                'plan_name': request.POST.get('plan_name'),
                'coverage': request.POST.get('coverage'),
                'premium': request.POST.get('premium'),
                'term': request.POST.get('term')
            }
            
            # Create InsurancePlan instance
            insurance_plan = InsurancePlan.objects.create(
                name=plan_data['plan_name'],
                insurance_type=plan_data['plan_type'],
                provider=plan_data['company'],
                description=f"Applied for {plan_data['plan_name']} from {plan_data['company']}",
                coverage_amount=Decimal(plan_data['coverage']),
                monthly_premium=Decimal(plan_data['premium']),
                term_years=int(plan_data['term'])
            )
            
            # Create UserInsurance instance
            from datetime import date, timedelta
            start_date = date.today()
            end_date = start_date + timedelta(days=365 * int(plan_data['term']))
            
            UserInsurance.objects.create(
                user=request.user,
                insurance_plan=insurance_plan,
                start_date=start_date,
                end_date=end_date
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Insurance application submitted successfully!'
            })
            
        except Exception as e:
            logger.error(f"Error in apply_insurance: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Failed to submit insurance application.'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    }, status=405)

@login_required
def compare_insurance(request):
    if request.method == 'POST':
        try:
            plan_ids = request.POST.getlist('plan_ids[]')
            plans = []
            
            for plan_id in plan_ids:
                plan_data = {
                    'company': request.POST.get(f'company_{plan_id}'),
                    'plan_name': request.POST.get(f'plan_name_{plan_id}'),
                    'coverage': request.POST.get(f'coverage_{plan_id}'),
                    'premium': request.POST.get(f'premium_{plan_id}'),
                    'term': request.POST.get(f'term_{plan_id}'),
                    'type': request.POST.get(f'type_{plan_id}')
                }
                plans.append(plan_data)
            
            return JsonResponse({
                'success': True,
                'plans': plans
            })
            
        except Exception as e:
            logger.error(f"Error in compare_insurance: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Failed to compare insurance plans.'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    }, status=405)

@login_required
def comparison_page(request):
    try:
        # Get plans from session storage
        selected_plans = request.session.get('selected_plans', [])
        if not selected_plans:
            # If not in Django session, template will handle sessionStorage
            return render(request, 'insurance/comparison_page.html', {'selected_plans': []})
        
        context = {
            'selected_plans': selected_plans,
            'insurance_types': InsurancePlan.INSURANCE_TYPES
        }
        return render(request, 'insurance/comparison_page.html', context)
    except Exception as e:
        logger.error(f"Error in comparison page: {str(e)}")
        return redirect('insurance:insurance')

@login_required
def my_policies(request):
    try:
        # Get user's insurance policies
        user_policies = UserInsurance.objects.filter(user=request.user).select_related('insurance_plan').order_by('-start_date')
        
        context = {
            'policies': user_policies,
            'active_policies': user_policies.filter(status='ACTIVE').count(),
            'total_premium': sum(policy.insurance_plan.monthly_premium for policy in user_policies.filter(status='ACTIVE')),
            'total_coverage': sum(policy.insurance_plan.coverage_amount for policy in user_policies.filter(status='ACTIVE'))
        }
        return render(request, 'insurance/my_policies.html', context)
    except Exception as e:
        logger.error(f"Error in my policies view: {str(e)}")
        return render(request, 'insurance/my_policies.html', {'error': 'Unable to load policies at this time.'})