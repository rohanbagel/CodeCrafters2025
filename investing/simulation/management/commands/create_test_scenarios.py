from django.core.management.base import BaseCommand
from simulation.models import SimulationScenario

class Command(BaseCommand):
    help = 'Creates test scenarios for the simulation'

    def handle(self, *args, **kwargs):
        scenarios = [
            {
                'title': 'Market Dip Opportunity',
                'description': 'The market has dropped 5% today due to temporary fears. Technical indicators suggest this is a short-term overreaction. What would you do?',
                'order': 1,
                'correct_action': 'buy',
                'reward': 500.00
            },
            {
                'title': 'Sudden Market Rally',
                'description': 'Your stock has increased 25% in the last two days due to speculation. The fundamentals haven\'t changed. What\'s your move?',
                'order': 2,
                'correct_action': 'sell',
                'reward': 750.00
            },
            {
                'title': 'Economic News Impact',
                'description': 'The Fed announced interest rates will remain unchanged. The market is currently stable. What\'s your strategy?',
                'order': 3,
                'correct_action': 'hold',
                'reward': 250.00
            }
        ]

        for scenario in scenarios:
            SimulationScenario.objects.get_or_create(
                title=scenario['title'],
                defaults=scenario
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully created test scenarios')) 