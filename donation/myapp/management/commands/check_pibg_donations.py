from django.core.management.base import BaseCommand
from myapp.models import PibgDonation, Student
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Check PIBG donations for debugging'

    def add_arguments(self, parser):
        parser.add_argument('--student-id', type=str, help='Student ID to check')
        parser.add_argument('--all', action='store_true', help='Show all PIBG donations')

    def handle(self, *args, **options):
        if options['student_id']:
            try:
                student = Student.objects.get(student_id=options['student_id'])
                self.stdout.write(f"Checking PIBG donations for student: {student.first_name} {student.last_name} ({student.student_id})")
                
                donations = PibgDonation.objects.filter(student=student).order_by('-created_at')
                self.stdout.write(f"Total donations found: {donations.count()}")
                
                for donation in donations:
                    self.stdout.write(f"  - {donation.receipt_number}: RM{donation.amount} at {donation.created_at}")
                    self.stdout.write(f"    Status: {donation.status}, Method: {donation.payment_method}")
                
            except Student.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Student with ID {options['student_id']} not found"))
        
        elif options['all']:
            self.stdout.write("All PIBG donations:")
            donations = PibgDonation.objects.all().order_by('-created_at')[:20]  # Last 20
            
            for donation in donations:
                self.stdout.write(f"  - {donation.student.student_id}: {donation.receipt_number} RM{donation.amount} at {donation.created_at}")
        
        else:
            # Show recent donations (last 24 hours)
            yesterday = timezone.now() - timedelta(hours=24)
            recent_donations = PibgDonation.objects.filter(created_at__gte=yesterday).order_by('-created_at')
            
            self.stdout.write(f"PIBG donations in last 24 hours: {recent_donations.count()}")
            for donation in recent_donations:
                self.stdout.write(f"  - {donation.student.student_id}: {donation.receipt_number} RM{donation.amount} at {donation.created_at}")
