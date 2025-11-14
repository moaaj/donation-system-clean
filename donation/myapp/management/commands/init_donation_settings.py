from django.core.management.base import BaseCommand
from myapp.models import PibgDonationSettings
from decimal import Decimal

class Command(BaseCommand):
    help = 'Initialize PIBG donation settings with default values'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reset even if settings already exist',
        )
        parser.add_argument(
            '--amounts',
            nargs='*',
            type=float,
            help='Specify custom amounts (e.g., --amounts 10 20 30 50 100)',
        )

    def handle(self, *args, **options):
        # Check if settings already exist
        settings_exist = PibgDonationSettings.objects.exists()
        
        if settings_exist and not options['force']:
            self.stdout.write(
                self.style.WARNING('PIBG donation settings already exist. Use --force to reset.')
            )
            settings = PibgDonationSettings.objects.first()
            self.display_current_settings(settings)
            return

        # Determine amounts to use
        if options['amounts']:
            amounts = options['amounts']
            self.stdout.write(f'Using custom amounts: {amounts}')
        else:
            amounts = [10.0, 20.0, 30.0, 50.0, 100.0, 150.0, 200.0, 250.0]
            self.stdout.write('Using default amounts')

        # Create or update settings
        settings, created = PibgDonationSettings.objects.get_or_create(
            pk=1,
            defaults={
                'banner_text': 'PIBG Muafakat Fund Donation',
                'donation_message': 'Support our school\'s PIBG Muafakat fund to help improve facilities and student programs.',
                'preset_amounts': amounts,
                'is_mandatory': False,
                'is_enabled': True,
                'minimum_custom_amount': Decimal('5.00'),
                'maximum_custom_amount': Decimal('1000.00'),
            }
        )

        if not created:
            # Update existing settings
            settings.preset_amounts = amounts
            settings.save()

        action = 'Created' if created else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(f'{action} PIBG donation settings successfully!')
        )
        
        self.display_current_settings(settings)

    def display_current_settings(self, settings):
        """Display current settings in a formatted way"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('Current PIBG Donation Settings:'))
        self.stdout.write('='*50)
        
        self.stdout.write(f'Banner Text: {settings.banner_text}')
        self.stdout.write(f'Is Enabled: {settings.is_enabled}')
        self.stdout.write(f'Is Mandatory: {settings.is_mandatory}')
        
        if settings.preset_amounts:
            amounts_str = ', '.join([f'RM{amount}' for amount in settings.preset_amounts])
            self.stdout.write(f'Preset Amounts: {amounts_str}')
            self.stdout.write(f'Total Amounts: {len(settings.preset_amounts)}')
        else:
            self.stdout.write(self.style.WARNING('No preset amounts configured'))
        
        self.stdout.write(f'Custom Amount Range: RM{settings.minimum_custom_amount} - RM{settings.maximum_custom_amount}')
        self.stdout.write(f'Last Updated: {settings.updated_at}')
        
        self.stdout.write('\n' + self.style.SUCCESS('Settings are ready for use!'))
        self.stdout.write('Access the admin interface at: /admin/myapp/pibgdonationsettings/')
        self.stdout.write('='*50)
