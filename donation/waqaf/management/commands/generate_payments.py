from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction, models
from waqaf.models import Contribution, Payment
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Auto-generate payments for recurring contributions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be generated without creating payments',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration of all payment schedules',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write("Starting payment generation process...")
        
        # Get recurring contributions that need payment generation
        if force:
            contributions = Contribution.objects.filter(payment_type='RECURRING')
            self.stdout.write(f"Found {contributions.count()} recurring contributions to process...")
        else:
            contributions = Contribution.objects.filter(
                payment_type='RECURRING',
                auto_generate_payments=True
            ).exclude(payments__isnull=False)
            self.stdout.write(f"Found {contributions.count()} contributions without payment schedules...")
        
        generated_count = 0
        
        for contribution in contributions:
            try:
                if dry_run:
                    self.stdout.write(
                        f"Would generate {contribution.total_payments} payments for "
                        f"{contribution.contributor.name} - RM{contribution.amount}"
                    )
                else:
                    # Generate payment schedule
                    contribution.generate_payment_schedule()
                    generated_count += 1
                    
                    # Get generated payments
                    payments = contribution.payments.all()
                    self.stdout.write(
                        f"Generated {payments.count()} payments for "
                        f"{contribution.contributor.name} - RM{contribution.amount}"
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error generating payments for {contribution.contributor.name}: {str(e)}"
                    )
                )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would generate payment schedules for {generated_count} contributions'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully generated payment schedules for {generated_count} contributions'
                )
            )
        
        # Check for overdue payments
        overdue_payments = Payment.objects.filter(
            status='PENDING',
            due_date__lt=timezone.now()
        )
        
        if overdue_payments.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Found {overdue_payments.count()} overdue payments'
                )
            )
            
            # Update overdue payment statuses
            if not dry_run:
                overdue_payments.update(status='OVERDUE')
                self.stdout.write("Updated overdue payment statuses")
        
        # Generate next payments for ongoing schedules
        self.generate_next_payments(dry_run)

    def generate_next_payments(self, dry_run=False):
        """Generate next payments for ongoing recurring contributions"""
        self.stdout.write("Checking for next payments to generate...")
        
        # Find contributions that need next payments
        contributions_needing_payments = Contribution.objects.filter(
            payment_type='RECURRING',
            auto_generate_payments=True,
            payments_made__lt=models.F('total_payments'),
            next_payment_date__lte=timezone.now()
        )
        
        generated_next_count = 0
        
        for contribution in contributions_needing_payments:
            try:
                # Calculate next payment details
                last_payment = contribution.payments.order_by('-payment_number').first()
                if not last_payment:
                    continue
                
                next_payment_number = last_payment.payment_number + 1
                
                # Calculate next due date
                if contribution.payment_schedule == 'WEEKLY':
                    interval = timedelta(weeks=1)
                elif contribution.payment_schedule == 'MONTHLY':
                    interval = timedelta(days=30)
                elif contribution.payment_schedule == 'QUARTERLY':
                    interval = timedelta(days=90)
                elif contribution.payment_schedule == 'YEARLY':
                    interval = timedelta(days=365)
                else:
                    continue
                
                next_due_date = last_payment.due_date + interval
                payment_amount = contribution.amount / contribution.total_payments
                
                if dry_run:
                    self.stdout.write(
                        f"Would generate next payment {next_payment_number} for "
                        f"{contribution.contributor.name} due {next_due_date.strftime('%Y-%m-%d')}"
                    )
                else:
                    # Create next payment
                    Payment.objects.create(
                        contribution=contribution,
                        amount=payment_amount,
                        due_date=next_due_date,
                        payment_number=next_payment_number,
                        status='PENDING'
                    )
                    
                    # Update next payment date
                    contribution.next_payment_date = next_due_date + interval
                    contribution.save(update_fields=['next_payment_date'])
                    
                    generated_next_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error generating next payment for {contribution.contributor.name}: {str(e)}"
                    )
                )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would generate {generated_next_count} next payments'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully generated {generated_next_count} next payments'
                )
            )
