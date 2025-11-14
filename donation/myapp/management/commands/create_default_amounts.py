from django.core.management.base import BaseCommand
from myapp.models import PredefinedDonationAmount

class Command(BaseCommand):
    help = 'Create default predefined donation amounts'

    def handle(self, *args, **options):
        # Default amounts based on the image (10, 50, 100, 300, 500, 1000)
        default_amounts = [
            {'amount': 10, 'display_order': 1},
            {'amount': 50, 'display_order': 2},
            {'amount': 100, 'display_order': 3},
            {'amount': 300, 'display_order': 4},
            {'amount': 500, 'display_order': 5},
            {'amount': 1000, 'display_order': 6},
        ]
        
        created_count = 0
        for amount_data in default_amounts:
            amount_obj, created = PredefinedDonationAmount.objects.get_or_create(
                amount=amount_data['amount'],
                defaults={
                    'is_active': True,
                    'display_order': amount_data['display_order']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created predefined amount: RM{amount_data["amount"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Predefined amount RM{amount_data["amount"]} already exists')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} predefined amounts')
        )
