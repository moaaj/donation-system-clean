from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import UserProfile, Student

class Command(BaseCommand):
    help = 'Check Form 1 admin setup'

    def handle(self, *args, **options):
        self.stdout.write("=== Checking Form 1 Admin Setup ===\n")
        
        # Check Form 1 students
        form1_students = Student.objects.filter(level_custom__in=['1', 'Form 1'])
        self.stdout.write(f"Total Form 1 students: {form1_students.count()}")
        
        # Check with current filter
        current_filter_students = Student.objects.filter(
            level='form',
            level_custom__iexact='Form 1',
            is_active=True
        )
        self.stdout.write(f"Form 1 students with current filter: {current_filter_students.count()}")
        
        # Check form1_admin user
        try:
            form1_admin = User.objects.get(username='form1_admin')
            profile = form1_admin.myapp_profile
            self.stdout.write(f"✅ Form 1 Admin User: {form1_admin.username}")
            self.stdout.write(f"   Role: {profile.role}")
            
            # Check if is_form1_admin method exists
            if hasattr(profile, 'is_form1_admin'):
                self.stdout.write(f"   Is Form 1 Admin: {profile.is_form1_admin()}")
            else:
                self.stdout.write("   ⚠️ is_form1_admin method not found")
                
        except User.DoesNotExist:
            self.stdout.write("❌ Form 1 admin user not found")
        
        # Show first 5 Form 1 students
        self.stdout.write(f"\nFirst 5 Form 1 students:")
        for i, student in enumerate(form1_students[:5], 1):
            self.stdout.write(f"{i}. {student.student_id}: {student.first_name} {student.last_name} (level: {student.level_custom})")
        
        self.stdout.write(f"\n=== Check Complete ===")
