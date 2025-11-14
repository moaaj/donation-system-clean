from django.core.management.base import BaseCommand
from myapp.models import Student
from django.db import transaction

class Command(BaseCommand):
    help = 'Fix year_batch data issues by setting default values for invalid entries'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Fixing year_batch data issues...")
        
        # Find students with problematic year_batch values
        problematic_students = Student.objects.filter(year_batch__isnull=True)
        
        self.stdout.write(f"Found {problematic_students.count()} students with null year_batch")
        
        if problematic_students.exists():
            with transaction.atomic():
                # Set default year_batch to 2024 for null values
                updated_count = problematic_students.update(year_batch=2024)
                self.stdout.write(f"✅ Updated {updated_count} students with year_batch=2024")
        
        # Check for any remaining issues
        remaining_issues = Student.objects.filter(year_batch__isnull=True).count()
        if remaining_issues == 0:
            self.stdout.write("✅ All year_batch data fixed!")
        else:
            self.stdout.write(f"⚠️  {remaining_issues} students still have null year_batch")
        
        # Show current year_batch distribution
        batches = Student.objects.values_list('year_batch', flat=True).distinct().order_by('-year_batch')
        self.stdout.write(f"\n📊 Current year_batch values: {list(batches)}")
        
        self.stdout.write("\n🎉 Year batch data fix completed!")
