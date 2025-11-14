from django.core.management.base import BaseCommand
from myapp.models import PibgDonationSettings
from decimal import Decimal

class Command(BaseCommand):
    help = 'Sets up default PIBG donation amounts and settings.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset to default amounts.',
        )
        parser.add_argument(
            '--amounts',
            nargs='*',
            type=Decimal,
            help='Specify custom amounts (e.g., --amounts 10 20 30 50 100).',
        )

    def handle(self, *args, **options):
        # Get or create PIBG settings
        settings, created = PibgDonationSettings.objects.get_or_create(
            pk=1,
            defaults={
                'banner_text': 'PIBG Muafakat Fund Donation',
                'donation_message': 'Support our school\'s PIBG Muafakat fund to help improve facilities and student programs.',
                'preset_amounts': [10, 20, 30, 50, 100],
                'is_mandatory': False,
                'is_enabled': True,
                'minimum_custom_amount': Decimal('5.00'),
                'maximum_custom_amount': Decimal('1000.00'),
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Created new PIBG donation settings.'))
        else:
            self.stdout.write(self.style.SUCCESS('Using existing PIBG donation settings.'))

        # Update amounts if specified
        if options['amounts']:
            settings.preset_amounts = [float(amount) for amount in options['amounts']]
            settings.save()
            self.stdout.write(self.style.SUCCESS(f'Updated preset amounts to: {settings.preset_amounts}'))
        elif options['reset']:
            settings.preset_amounts = [10, 20, 30, 50, 100]
            settings.save()
            self.stdout.write(self.style.SUCCESS('Reset to default amounts: [10, 20, 30, 50, 100]'))

        # Display current settings
        self.stdout.write(self.style.HTTP_INFO('\nCurrent PIBG Donation Settings:'))
        self.stdout.write(f'  Banner Text: {settings.banner_text}')
        self.stdout.write(f'  Message: {settings.donation_message}')
        self.stdout.write(f'  Preset Amounts: {settings.preset_amounts}')
        self.stdout.write(f'  Is Mandatory: {settings.is_mandatory}')
        self.stdout.write(f'  Is Enabled: {settings.is_enabled}')
        self.stdout.write(f'  Min Custom Amount: RM{settings.minimum_custom_amount}')
        self.stdout.write(f'  Max Custom Amount: RM{settings.maximum_custom_amount}')

        self.stdout.write(self.style.SUCCESS('\nPIBG donation settings setup complete!'))
