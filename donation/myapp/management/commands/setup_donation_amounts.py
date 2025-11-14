from django.core.management.base import BaseCommand
from myapp.models import PredefinedDonationAmount
from decimal import Decimal

class Command(BaseCommand):
    help = 'Setup or update predefined donation amounts for admin management'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all amounts to default values',
        )
        parser.add_argument(
            '--amounts',
            nargs='+',
            type=float,
            help='Custom amounts to set (e.g., --amounts 10 25 50 100 250 500)',
        )

    def handle(self, *args, **options):
        if options['reset']:
            # Clear existing amounts
            PredefinedDonationAmount.objects.all().delete()
            self.stdout.write(self.style.WARNING('All existing amounts cleared.'))
        
        if options['amounts']:
            # Use custom amounts
            amounts = options['amounts']
        else:
            # Use default amounts
            amounts = [10, 25, 50, 100, 250, 500, 1000]
        
        created_count = 0
        updated_count = 0
        
        for i, amount_value in enumerate(amounts, 1):
            amount_decimal = Decimal(str(amount_value))
            amount, created = PredefinedDonationAmount.objects.get_or_create(
                amount=amount_decimal,
                defaults={
                    'is_active': True,
                    'display_order': i
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created: RM{amount.amount}')
                )
            else:
                # Update existing amount
                amount.is_active = True
                amount.display_order = i
                amount.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated: RM{amount.amount}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Setup complete! Created {created_count} new amounts, '
                f'updated {updated_count} existing amounts.'
            )
        )
        
        # Show current amounts
        self.stdout.write('\nCurrent predefined amounts:')
        for amount in PredefinedDonationAmount.objects.filter(is_active=True).order_by('display_order'):
            status = '✓' if amount.is_active else '✗'
            self.stdout.write(f'  {status} RM{amount.amount} (Order: {amount.display_order})')
