from django.core.management.base import BaseCommand
from django.db.models import Sum
from myapp.models import Student, Payment, FeeStatus, FeeStructure, FeeCategory

class Command(BaseCommand):
    help = 'Verify dashboard calculation accuracy and show detailed breakdown'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Dashboard Accuracy Verification Report")
        self.stdout.write("=" * 50)
        
        # 1. Check Active Fee Structures
        active_fs = FeeStructure.objects.filter(is_active=True)
        self.stdout.write(f"\n📋 Active Fee Structures: {active_fs.count()}")
        
        if active_fs.count() == 0:
            self.stdout.write(self.style.WARNING("⚠️  No active fee structures found!"))
            return
        
        # 2. Calculate Expected Amount with detailed breakdown
        self.stdout.write("\n💰 Expected Amount Calculation:")
        expected_amount = 0
        
        for fee_structure in active_fs:
            form_value = fee_structure.form
            
            # Try different matching strategies
            student_count = Student.objects.filter(
                level_custom=form_value,
                is_active=True
            ).count()
            
            if student_count == 0 and 'Form' in str(form_value):
                form_number = str(form_value).replace('Form', '').strip()
                student_count = Student.objects.filter(
                    level_custom=form_number,
                    is_active=True
                ).count()
            
            if student_count == 0 and str(form_value).isdigit():
                form_name = f"Form {form_value}"
                student_count = Student.objects.filter(
                    level_custom=form_name,
                    is_active=True
                ).count()
            
            contribution = fee_structure.amount * student_count
            expected_amount += contribution
            
            self.stdout.write(f"   {fee_structure.category.name} - Form {form_value}: {student_count} students × RM {fee_structure.amount} = RM {contribution:,.2f}")
        
        # 3. Calculate Actual Collection
        actual_collection = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        
        # 4. Calculate Outstanding
        outstanding_amount = FeeStatus.objects.filter(
            status__in=['pending', 'overdue']
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # 5. Calculate Achievement Percentage
        if expected_amount > 0:
            achievement = min((actual_collection / expected_amount * 100), 100.0)
            achievement = round(achievement, 1)
        else:
            achievement = 0.0
        
        # 6. Display Results
        self.stdout.write("\n📊 FINAL CALCULATIONS:")
        self.stdout.write(f"   Expected Amount: RM {expected_amount:,.2f}")
        self.stdout.write(f"   Actual Collection: RM {actual_collection:,.2f}")
        self.stdout.write(f"   Outstanding Amount: RM {outstanding_amount:,.2f}")
        self.stdout.write(f"   Achievement Percentage: {achievement}%")
        
        # 7. Validation Checks
        self.stdout.write("\n✅ VALIDATION CHECKS:")
        
        # Check if achievement is reasonable
        if achievement > 100:
            self.stdout.write(self.style.ERROR(f"❌ Achievement percentage is over 100%: {achievement}%"))
        elif achievement < 0:
            self.stdout.write(self.style.ERROR(f"❌ Achievement percentage is negative: {achievement}%"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Achievement percentage is valid: {achievement}%"))
        
        # Check if expected amount makes sense
        total_students = Student.objects.filter(is_active=True).count()
        if expected_amount == 0:
            self.stdout.write(self.style.WARNING("⚠️  Expected amount is zero - check fee structures and student matching"))
        elif expected_amount < total_students * 10:  # Less than RM 10 per student seems low
            self.stdout.write(self.style.WARNING(f"⚠️  Expected amount seems low: RM {expected_amount/total_students:.2f} per student"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Expected amount seems reasonable: RM {expected_amount/total_students:.2f} per student"))
        
        # Check data consistency
        calculated_total = actual_collection + outstanding_amount
        if abs(calculated_total - expected_amount) > 1:  # Allow for small rounding differences
            difference = calculated_total - expected_amount
            self.stdout.write(self.style.WARNING(f"⚠️  Data inconsistency detected: Actual + Outstanding (RM {calculated_total:,.2f}) vs Expected (RM {expected_amount:,.2f}) = Difference: RM {difference:,.2f}"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ Data consistency check passed"))
        
        self.stdout.write("\n🎯 RECOMMENDATIONS:")
        if achievement > 100:
            self.stdout.write("   • Check for duplicate payments or incorrect fee structure amounts")
        if expected_amount == 0:
            self.stdout.write("   • Activate fee structures or check student level_custom field matching")
        if outstanding_amount < 0:
            self.stdout.write("   • Check for negative fee status amounts")
        
        self.stdout.write("\n✨ Dashboard accuracy verification completed!")
