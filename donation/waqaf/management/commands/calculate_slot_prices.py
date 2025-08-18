from django.core.management.base import BaseCommand
from django.db import transaction
from waqaf.models import WaqafAsset


class Command(BaseCommand):
    help = 'Calculate slot prices for waqaf assets based on target amount and total slots'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--asset-id',
            type=int,
            help='Update specific asset by ID',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if slot_price is already set',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        asset_id = options['asset_id']
        force = options['force']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )

        # Get assets to update
        if asset_id:
            assets = WaqafAsset.objects.filter(id=asset_id)
            if not assets.exists():
                self.stdout.write(
                    self.style.ERROR(f'Asset with ID {asset_id} not found')
                )
                return
        else:
            assets = WaqafAsset.objects.all()

        updated_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write('\n=== Slot Price Calculation Report ===\n')

        for asset in assets:
            try:
                # Check if we should update this asset
                if not force and asset.slot_price > 0 and asset.target_amount > 0 and asset.total_slots > 0:
                    calculated_price = asset.target_amount / asset.total_slots
                    if abs(asset.slot_price - calculated_price) < 0.01:  # Within 1 cent
                        self.stdout.write(
                            f'⏭️  SKIPPED: {asset.name} - Slot price already correct (RM{asset.slot_price:.2f})'
                        )
                        skipped_count += 1
                        continue

                # Validate required fields
                if asset.target_amount <= 0:
                    self.stdout.write(
                        f'❌ ERROR: {asset.name} - Target amount not set (RM{asset.target_amount})'
                    )
                    error_count += 1
                    continue

                if asset.total_slots <= 0:
                    self.stdout.write(
                        f'❌ ERROR: {asset.name} - Total slots not set ({asset.total_slots})'
                    )
                    error_count += 1
                    continue

                # Calculate new slot price
                old_price = asset.slot_price
                new_price = asset.target_amount / asset.total_slots

                if dry_run:
                    self.stdout.write(
                        f'📋 WOULD UPDATE: {asset.name}\n'
                        f'   Target Amount: RM{asset.target_amount:,.2f}\n'
                        f'   Total Slots: {asset.total_slots}\n'
                        f'   Old Slot Price: RM{old_price:.2f}\n'
                        f'   New Slot Price: RM{new_price:.2f}\n'
                        f'   Available Slots: {asset.slots_available}\n'
                    )
                else:
                    with transaction.atomic():
                        asset.slot_price = new_price
                        asset.save(update_fields=['slot_price'])
                        
                        self.stdout.write(
                            f'✅ UPDATED: {asset.name}\n'
                            f'   Target Amount: RM{asset.target_amount:,.2f}\n'
                            f'   Total Slots: {asset.total_slots}\n'
                            f'   Old Slot Price: RM{old_price:.2f}\n'
                            f'   New Slot Price: RM{new_price:.2f}\n'
                            f'   Available Slots: {asset.slots_available}\n'
                        )

                updated_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ ERROR updating {asset.name}: {str(e)}')
                )
                error_count += 1

        # Summary
        self.stdout.write('\n=== Summary ===')
        self.stdout.write(f'✅ Updated: {updated_count}')
        self.stdout.write(f'⏭️  Skipped: {skipped_count}')
        self.stdout.write(f'❌ Errors: {error_count}')
        self.stdout.write(f'📊 Total Assets: {assets.count()}')

        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nThis was a dry run. Use --force to apply changes.')
            )
        elif updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully updated {updated_count} assets!')
            )
