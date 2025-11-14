from django.core.management.base import BaseCommand
from myapp.models import PibgDonation, Student
from django.utils import timezone

class Command(BaseCommand):
    help = 'Test PIBG donation session tracking'

    def add_arguments(self, parser):
        parser.add_argument('--student-id', type=str, help='Student ID to test')

    def handle(self, *args, **options):
        if options['student_id']:
            try:
                student = Student.objects.get(student_id=options['student_id'])
                self.stdout.write(f"Testing PIBG donations for student: {student.first_name} {student.last_name} ({student.student_id})")
                
                # Get all donations for this student
                donations = PibgDonation.objects.filter(student=student).order_by('-created_at')
                self.stdout.write(f"Total donations found: {donations.count()}")
                
                if donations.exists():
                    self.stdout.write("Recent donations:")
                    for donation in donations[:5]:  # Show last 5
                        self.stdout.write(f"  - ID: {donation.id}, Receipt: {donation.receipt_number}, Amount: RM{donation.amount}, Date: {donation.created_at}")
                    
                    # Show what would be stored in session
                    donation_ids = [d.id for d in donations[:3]]  # Last 3 donations
                    self.stdout.write(f"Session would store: last_cart_pibg_donation_ids = {donation_ids}")
                
            except Student.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Student with ID {options['student_id']} not found"))
        else:
            self.stdout.write("Please provide --student-id parameter")
