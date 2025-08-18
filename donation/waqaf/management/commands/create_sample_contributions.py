from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from waqaf.models import WaqafAsset, Contributor, Contribution
from django.db import models


class Command(BaseCommand):
    help = 'Create sample contributions with different dates and payment statuses for dashboard charts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing contributions before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            Contribution.objects.all().delete()
            self.stdout.write('Cleared existing contributions.')

        # Get or create assets
        assets = WaqafAsset.objects.all()
        if not assets.exists():
            self.stdout.write(
                self.style.ERROR('No waqaf assets found. Please create assets first.')
            )
            return

        # Get or create contributors
        contributors = []
        for i in range(5):
            contributor, created = Contributor.objects.get_or_create(
                email=f'sample{i+1}@example.com',
                defaults={
                    'name': f'Sample Contributor {i+1}',
                    'phone': f'012345678{i}',
                    'address': f'Sample Address {i+1}'
                }
            )
            contributors.append(contributor)
            if created:
                self.stdout.write(f'Created contributor: {contributor.name}')

        # Create sample contributions with different dates
        sample_data = [
            # Last 6 months of data
            {'months_ago': 5, 'amount': 150, 'slots': 3, 'status': 'COMPLETED'},
            {'months_ago': 4, 'amount': 200, 'slots': 4, 'status': 'COMPLETED'},
            {'months_ago': 3, 'amount': 100, 'slots': 2, 'status': 'COMPLETED'},
            {'months_ago': 2, 'amount': 300, 'slots': 6, 'status': 'COMPLETED'},
            {'months_ago': 1, 'amount': 250, 'slots': 5, 'status': 'COMPLETED'},
            {'months_ago': 0, 'amount': 400, 'slots': 8, 'status': 'COMPLETED'},
            # Some pending and failed for variety
            {'months_ago': 0, 'amount': 100, 'slots': 2, 'status': 'PENDING'},
            {'months_ago': 1, 'amount': 50, 'slots': 1, 'status': 'FAILED'},
        ]

        created_count = 0
        for i, data in enumerate(sample_data):
            # Calculate date
            contribution_date = timezone.now() - timedelta(days=30 * data['months_ago'])
            
            # Select asset and contributor
            asset = assets[i % len(assets)]
            contributor = contributors[i % len(contributors)]
            
            # Create contribution
            contribution = Contribution.objects.create(
                contributor=contributor,
                asset=asset,
                number_of_slots=data['slots'],
                amount=data['amount'],
                payment_status=data['status'],
                date_contributed=contribution_date,
                dedicated_for=f'Sample dedication {i+1}',
                payment_type='ONE_OFF'
            )
            
            created_count += 1
            self.stdout.write(
                f'Created contribution: {contribution.contributor.name} - '
                f'RM{contribution.amount} ({contribution.number_of_slots} slots) - '
                f'{contribution.payment_status} - {contribution.date_contributed.strftime("%Y-%m")}'
            )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample contributions!')
        )
        
        # Show summary
        total_contributions = Contribution.objects.count()
        total_amount = Contribution.objects.aggregate(total=models.Sum('amount'))['total'] or 0
        status_counts = Contribution.objects.values('payment_status').annotate(
            count=models.Count('id')
        )
        
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'Total Contributions: {total_contributions}')
        self.stdout.write(f'Total Amount: RM{total_amount:.2f}')
        self.stdout.write(f'Payment Status Distribution:')
        for status in status_counts:
            self.stdout.write(f'  {status["payment_status"]}: {status["count"]}')
