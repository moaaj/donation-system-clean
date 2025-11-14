from django.core.management.base import BaseCommand
from django.db.models import Avg
from myapp.models import Student, FeeStructure, FeeCategory, Payment

class Command(BaseCommand):
    help = 'Create missing fee structures for forms that have students but no fee structures'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Setting up missing fee structures...")
        
        # Get all unique student forms
        student_forms = Student.objects.filter(is_active=True).values_list('level_custom', flat=True).distinct()
        self.stdout.write(f"Found student forms: {list(student_forms)}")
        
        # Get existing fee structure forms
        existing_forms = FeeStructure.objects.filter(is_active=True).values_list('form', flat=True).distinct()
        self.stdout.write(f"Existing fee structure forms: {list(existing_forms)}")
        
        # Get or create default category
        default_category, created = FeeCategory.objects.get_or_create(
            name='PTA',
            defaults={'description': 'Parent Teacher Association fees', 'is_active': True}
        )
        if created:
            self.stdout.write("Created default PTA category")
        
        # Calculate average payment amount to use as base fee
        avg_payment = Payment.objects.filter(status='completed').aggregate(Avg('amount'))['amount__avg'] or 976
        base_fee_amount = avg_payment if avg_payment and avg_payment > 0 else 976
        
        self.stdout.write(f"Using base fee amount: RM {base_fee_amount}")
        
        created_count = 0
        
        for form in student_forms:
            if not form:  # Skip empty forms
                continue
                
            # Check if fee structure exists for this form (with flexible matching)
            exists = False
            for existing_form in existing_forms:
                if (str(form) == str(existing_form) or 
                    f"Form {form}" == str(existing_form) or 
                    str(form) == str(existing_form).replace('Form', '').strip()):
                    exists = True
                    break
            
            if not exists:
                # Create fee structure for this form
                fee_structure = FeeStructure.objects.create(
                    category=default_category,
                    form=form,
                    amount=base_fee_amount,
                    frequency='yearly',  # Default frequency
                    is_active=True
                )
                created_count += 1
                self.stdout.write(f"✅ Created fee structure for Form {form}: RM {base_fee_amount}")
        
        if created_count == 0:
            self.stdout.write("✅ All forms already have fee structures")
        else:
            self.stdout.write(f"✅ Created {created_count} new fee structures")
        
        # Verify the setup
        self.stdout.write("\n🔍 Verification:")
        for form in student_forms:
            if not form:
                continue
            student_count = Student.objects.filter(level_custom=form, is_active=True).count()
            
            # Try to find matching fee structure
            fee_structures = FeeStructure.objects.filter(form=form, is_active=True)
            if not fee_structures.exists():
                fee_structures = FeeStructure.objects.filter(form=f"Form {form}", is_active=True)
            
            if fee_structures.exists():
                total_amount = sum(fs.amount for fs in fee_structures) * student_count
                self.stdout.write(f"   Form {form}: {student_count} students × RM {sum(fs.amount for fs in fee_structures)} = RM {total_amount}")
            else:
                self.stdout.write(f"   ⚠️  Form {form}: {student_count} students - NO FEE STRUCTURE FOUND")
        
        self.stdout.write("\n✨ Fee structure setup completed!")
