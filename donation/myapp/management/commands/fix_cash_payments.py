from django.core.management.base import BaseCommand
from myapp.models import Payment

class Command(BaseCommand):
    help = 'Fix existing cash payments that may have incorrect status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find all cash payments
        cash_payments = Payment.objects.filter(payment_method='cash')
        
        self.stdout.write(f"Found {cash_payments.count()} cash payments")
        
        # Check for cash payments that might need status updates
        completed_cash = cash_payments.filter(status='completed')
        pending_cash = cash_payments.filter(status='pending')
        other_status_cash = cash_payments.exclude(status__in=['completed', 'pending'])
        
        self.stdout.write(f"  - Completed: {completed_cash.count()}")
        self.stdout.write(f"  - Pending: {pending_cash.count()}")
        self.stdout.write(f"  - Other status: {other_status_cash.count()}")
        
        if other_status_cash.exists():
            self.stdout.write("\nCash payments with unusual status:")
            for payment in other_status_cash:
                self.stdout.write(f"  - Payment {payment.id}: {payment.student.first_name} {payment.student.last_name} - Status: '{payment.status}'")
        
        # Show pending cash payments that might need admin attention
        if pending_cash.exists():
            self.stdout.write(f"\nPending cash payments (need admin confirmation):")
            for payment in pending_cash[:10]:  # Show first 10
                self.stdout.write(f"  - {payment.payment_date}: {payment.student.first_name} {payment.student.last_name} - RM {payment.amount}")
        
        # Option to update all cash payments to pending if they're not completed
        if not dry_run:
            # Ask for confirmation
            confirm = input("\nDo you want to set all non-completed cash payments to 'pending' status? (y/N): ")
            if confirm.lower() == 'y':
                updated = cash_payments.exclude(status='completed').update(status='pending')
                self.stdout.write(f"Updated {updated} cash payments to 'pending' status")
            else:
                self.stdout.write("No changes made")
        else:
            non_completed_cash = cash_payments.exclude(status='completed')
            self.stdout.write(f"\n[DRY RUN] Would update {non_completed_cash.count()} cash payments to 'pending' status")
        
        self.stdout.write("\nDone!")
