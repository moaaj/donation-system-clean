from django.core.management.base import BaseCommand
from django.db import transaction
from waqaf.models import WaqafAsset


class Command(BaseCommand):
    help = 'Fix waqaf assets that have target_amount of 0 but have slot prices set'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--asset-id',
            type=int,
            help='Fix specific asset by ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        asset_id = options['asset_id']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )

        # Get assets to fix
        if asset_id:
            assets = WaqafAsset.objects.filter(id=asset_id)
            if not assets.exists():
                self.stdout.write(
                    self.style.ERROR(f'Asset with ID {asset_id} not found')
                )
                return
        else:
            # Find assets with target_amount = 0 but have slot_price and total_slots
            assets = WaqafAsset.objects.filter(
                target_amount=0,
                slot_price__gt=0,
                total_slots__gt=0
            )

        if not assets.exists():
            self.stdout.write(
                self.style.WARNING('No assets found that need fixing.')
            )
            return

        updated_count = 0
        error_count = 0

        self.stdout.write('\n=== Asset Target Amount Fix Report ===\n')

        for asset in assets:
            try:
                # Calculate target amount based on current slot_price and total_slots
                calculated_target = asset.slot_price * asset.total_slots
                
                if dry_run:
                    self.stdout.write(
                        f'📋 WOULD FIX: {asset.name}\n'
                        f'   Current Target Amount: RM{asset.target_amount:.2f}\n'
                        f'   Current Slot Price: RM{asset.slot_price:.2f}\n'
                        f'   Total Slots: {asset.total_slots}\n'
                        f'   Calculated Target Amount: RM{calculated_target:.2f}\n'
                        f'   Available Slots: {asset.slots_available}\n'
                    )
                else:
                    with transaction.atomic():
                        old_target = asset.target_amount
                        asset.target_amount = calculated_target
                        asset.save(update_fields=['target_amount'])
                        
                        self.stdout.write(
                            f'✅ FIXED: {asset.name}\n'
                            f'   Old Target Amount: RM{old_target:.2f}\n'
                            f'   New Target Amount: RM{asset.target_amount:.2f}\n'
                            f'   Slot Price: RM{asset.slot_price:.2f}\n'
                            f'   Total Slots: {asset.total_slots}\n'
                            f'   Available Slots: {asset.slots_available}\n'
                        )

                updated_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ ERROR fixing {asset.name}: {str(e)}')
                )
                error_count += 1

        # Summary
        self.stdout.write('\n=== Summary ===')
        self.stdout.write(f'✅ Fixed: {updated_count}')
        self.stdout.write(f'❌ Errors: {error_count}')
        self.stdout.write(f'📊 Total Assets Processed: {assets.count()}')

        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nThis was a dry run. Run without --dry-run to apply changes.')
            )
        elif updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully fixed {updated_count} assets!')
            )
