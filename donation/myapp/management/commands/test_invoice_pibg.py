from django.core.management.base import BaseCommand
from myapp.models import PibgDonation, Student, Payment, Invoice
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Test PIBG donations in invoice generation'

    def add_arguments(self, parser):
        parser.add_argument('--student-id', type=str, help='Student ID to test')

    def handle(self, *args, **options):
        if options['student_id']:
            try:
                student = Student.objects.get(student_id=options['student_id'])
                self.stdout.write(f"Testing invoice generation for student: {student.first_name} {student.last_name} ({student.student_id})")
                
                # Get PIBG donations using the same logic as the invoice view
                recent_donations = []
                
                # Strategy 1: Get today's donations
                today = timezone.now().date()
                today_donations = PibgDonation.objects.filter(
                    student=student,
                    created_at__date=today
                ).order_by('-created_at')
                if today_donations.exists():
                    recent_donations = list(today_donations)
                    self.stdout.write(f"Found {len(recent_donations)} PIBG donations from today")
                
                # Strategy 2: If no donations today, get last 24 hours
                if not recent_donations:
                    yesterday = timezone.now() - timedelta(hours=24)
                    recent_donations = list(PibgDonation.objects.filter(
                        student=student,
                        created_at__gte=yesterday
                    ).order_by('-created_at'))
                    if recent_donations:
                        self.stdout.write(f"Found {len(recent_donations)} PIBG donations from last 24 hours")
                
                # Strategy 3: If still no donations, get recent ones
                if not recent_donations:
                    recent_donations = list(PibgDonation.objects.filter(
                        student=student
                    ).order_by('-created_at')[:5])
                    if recent_donations:
                        self.stdout.write(f"Found {len(recent_donations)} recent PIBG donations")
                
                # Show what would be displayed
                if recent_donations:
                    self.stdout.write("PIBG donations that would be shown in invoice:")
                    total_donation_amount = 0
                    for donation in recent_donations:
                        self.stdout.write(f"  - {donation.receipt_number}: RM{donation.amount} ({donation.created_at.strftime('%Y-%m-%d %H:%M')})")
                        total_donation_amount += float(donation.amount)
                    self.stdout.write(f"Total PIBG donation amount: RM{total_donation_amount:.2f}")
                else:
                    self.stdout.write("No PIBG donations would be shown in invoice")
                
                # Check recent payments
                recent_payments = Payment.objects.filter(student=student).order_by('-created_at')[:3]
                if recent_payments.exists():
                    self.stdout.write(f"Recent payments: {recent_payments.count()}")
                    for payment in recent_payments:
                        self.stdout.write(f"  - Payment {payment.id}: RM{payment.amount} ({payment.created_at.strftime('%Y-%m-%d %H:%M')})")
                
            except Student.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Student with ID {options['student_id']} not found"))
        else:
            self.stdout.write("Please provide --student-id parameter")
