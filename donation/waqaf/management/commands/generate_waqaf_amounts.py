from django.core.management.base import BaseCommand
from django.db import transaction
from waqaf.models import Contribution
from decimal import Decimal


class Command(BaseCommand):
    help = 'Generate amounts for waqaf contributions based on slots and asset prices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recalculate all amounts, even if they already have values',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        # Get contributions that need amount calculation
        if force:
            contributions = Contribution.objects.exclude(asset__isnull=True)
            self.stdout.write(f"Found {contributions.count()} total contributions to process...")
        else:
            contributions = Contribution.objects.filter(amount=0).exclude(asset__isnull=True)
            self.stdout.write(f"Found {contributions.count()} contributions without amounts...")
        
        if not contributions.exists():
            self.stdout.write(
                self.style.SUCCESS('No contributions need amount generation.')
            )
            return
        
        updated_count = 0
        total_amount = Decimal('0.00')
        
        for contribution in contributions:
            if contribution.asset and contribution.number_of_slots:
                old_amount = contribution.amount
                new_amount = contribution.number_of_slots * contribution.asset.slot_price
                
                if old_amount != new_amount:
                    if dry_run:
                        self.stdout.write(
                            f"Would update: {contribution.contributor.name} - "
                            f"{contribution.asset.name} - "
                            f"{contribution.number_of_slots} slots × RM{contribution.asset.slot_price} = "
                            f"RM{old_amount} → RM{new_amount}"
                        )
                    else:
                        contribution.amount = new_amount
                        contribution.save()
                        self.stdout.write(
                            f"Updated: {contribution.contributor.name} - "
                            f"{contribution.asset.name} - "
                            f"RM{old_amount} → RM{new_amount}"
                        )
                    
                    updated_count += 1
                    total_amount += new_amount - old_amount
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would update {updated_count} contributions with total amount change of RM{total_amount:.2f}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {updated_count} contributions with total amount change of RM{total_amount:.2f}'
                )
            )
