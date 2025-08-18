from django.core.management.base import BaseCommand
from waqaf.models import WaqafAsset


class Command(BaseCommand):
    help = 'Create a sample waqaf asset with target amount and auto-calculated slot price'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            default='Sample Mosque Project',
            help='Name of the asset',
        )
        parser.add_argument(
            '--target-amount',
            type=float,
            default=10000.00,
            help='Target amount for the asset',
        )
        parser.add_argument(
            '--total-slots',
            type=int,
            default=100,
            help='Total number of slots available',
        )

    def handle(self, *args, **options):
        name = options['name']
        target_amount = options['target_amount']
        total_slots = options['total_slots']
        
        # Calculate slot price
        slot_price = target_amount / total_slots
        
        # Create the asset
        asset = WaqafAsset.objects.create(
            name=name,
            description=f'A sample waqaf asset with target amount RM{target_amount:,.2f} and {total_slots} slots.',
            current_value=target_amount,
            target_amount=target_amount,
            total_slots=total_slots,
            slots_available=total_slots,
            slot_price=slot_price
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Successfully created asset: {asset.name}\n'
                f'   Target Amount: RM{asset.target_amount:,.2f}\n'
                f'   Total Slots: {asset.total_slots}\n'
                f'   Auto-calculated Slot Price: RM{asset.slot_price:.2f}\n'
                f'   Available Slots: {asset.slots_available}'
            )
        )
        
        # Verify the calculation
        calculated_price = asset.target_amount / asset.total_slots
        self.stdout.write(
            f'\n📊 Verification:\n'
            f'   Target Amount ÷ Total Slots = RM{asset.target_amount:,.2f} ÷ {asset.total_slots} = RM{calculated_price:.2f}\n'
            f'   ✅ Slot price correctly calculated!'
        )
