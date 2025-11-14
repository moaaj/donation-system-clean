from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import FeeCategory, FeeStructure, Student, FeeStatus
from decimal import Decimal
from django.db import models


class Command(BaseCommand):
    help = 'Set up fee structures for different forms and ensure all students in the same form pay the same amount'

    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            type=str,
            help='Fee category name (e.g., "Tuition Fees", "Examination Fees")'
        )
        parser.add_argument(
            '--form',
            type=str,
            help='Form level (e.g., "Form 1", "Form 2", "Form 3")'
        )
        parser.add_argument(
            '--amount',
            type=Decimal,
            help='Fee amount for the form'
        )
        parser.add_argument(
            '--frequency',
            type=str,
            choices=['monthly', 'termly', 'yearly'],
            default='yearly',
            help='Payment frequency'
        )
        parser.add_argument(
            '--monthly-duration',
            type=int,
            choices=[10, 11, 12],
            help='Number of months for monthly payment plan'
        )
        parser.add_argument(
            '--total-amount',
            type=Decimal,
            help='Total amount for monthly payment plan'
        )
        parser.add_argument(
            '--auto-generate',
            action='store_true',
            help='Automatically generate payment records for students'
        )
        parser.add_argument(
            '--list-forms',
            action='store_true',
            help='List all available forms and student counts'
        )
        parser.add_argument(
            '--list-categories',
            action='store_true',
            help='List all available fee categories'
        )
        parser.add_argument(
            '--show-current-fees',
            action='store_true',
            help='Show current fee structures for all forms'
        )

    def handle(self, *args, **options):
        if options['list_forms']:
            self.list_forms()
            return
        
        if options['list_categories']:
            self.list_categories()
            return
        
        if options['show_current_fees']:
            self.show_current_fees()
            return
        
        if not all([options['category'], options['form'], options['amount']]):
            self.stdout.write(
                self.style.ERROR(
                    'Please provide --category, --form, and --amount arguments. '
                    'Use --help for more information.'
                )
            )
            return
        
        self.setup_fee_structure(
            category_name=options['category'],
            form=options['form'],
            amount=options['amount'],
            frequency=options['frequency'],
            monthly_duration=options['monthly_duration'],
            total_amount=options['total_amount'],
            auto_generate=options['auto_generate']
        )

    def list_forms(self):
        """List all available forms and student counts"""
        self.stdout.write(self.style.SUCCESS('Available Forms and Student Counts:'))
        self.stdout.write('=' * 50)
        
        # Get all unique form levels from students
        students = Student.objects.filter(is_active=True)
        form_counts = {}
        
        for student in students:
            level = student.get_level_display_value()
            form_counts[level] = form_counts.get(level, 0) + 1
        
        for form, count in sorted(form_counts.items()):
            self.stdout.write(f'{form}: {count} students')
        
        self.stdout.write('')

    def list_categories(self):
        """List all available fee categories"""
        self.stdout.write(self.style.SUCCESS('Available Fee Categories:'))
        self.stdout.write('=' * 40)
        
        categories = FeeCategory.objects.filter(is_active=True)
        for category in categories:
            self.stdout.write(f'- {category.name} ({category.get_category_type_display()})')
        
        self.stdout.write('')

    def show_current_fees(self):
        """Show current fee structures for all forms"""
        self.stdout.write(self.style.SUCCESS('Current Fee Structures:'))
        self.stdout.write('=' * 50)
        
        fee_structures = FeeStructure.objects.filter(is_active=True).select_related('category')
        
        if not fee_structures.exists():
            self.stdout.write('No fee structures found.')
            return
        
        current_form = None
        for fs in fee_structures.order_by('form', 'category__name'):
            if current_form != fs.form:
                current_form = fs.form
                self.stdout.write(f'\n{current_form}:')
                self.stdout.write('-' * len(current_form))
            
            amount_display = f"RM {fs.amount}" if fs.amount else "Not set"
            if fs.frequency == 'monthly' and fs.total_amount and fs.monthly_duration:
                amount_display = f"RM {fs.total_amount} over {fs.monthly_duration} months"
            
            self.stdout.write(f'  {fs.category.name}: {amount_display} ({fs.frequency})')
        
        self.stdout.write('')

    def setup_fee_structure(self, category_name, form, amount, frequency='yearly', 
                           monthly_duration=None, total_amount=None, auto_generate=False):
        """Set up a fee structure for a specific form"""
        try:
            # Get or create the fee category
            category, created = FeeCategory.objects.get_or_create(
                name=category_name,
                defaults={
                    'description': f'{category_name} for {form}',
                    'category_type': 'general'
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created new fee category: {category_name}')
                )
            
            # Check if fee structure already exists for this category and form
            existing_fee = FeeStructure.objects.filter(
                category=category,
                form=form
            ).first()
            
            if existing_fee:
                # Update existing fee structure
                existing_fee.amount = amount
                existing_fee.frequency = frequency
                existing_fee.monthly_duration = monthly_duration
                existing_fee.total_amount = total_amount
                existing_fee.auto_generate_payments = auto_generate
                existing_fee.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Updated fee structure for {category_name} - {form}')
                )
                fee_structure = existing_fee
            else:
                # Create new fee structure
                fee_structure = FeeStructure.objects.create(
                    category=category,
                    form=form,
                    amount=amount,
                    frequency=frequency,
                    monthly_duration=monthly_duration,
                    total_amount=total_amount,
                    auto_generate_payments=auto_generate
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Created fee structure for {category_name} - {form}')
                )
            
            # Show fee structure details
            self.stdout.write(f'Fee Structure Details:')
            self.stdout.write(f'  Category: {category_name}')
            self.stdout.write(f'  Form: {form}')
            self.stdout.write(f'  Amount: RM {amount}')
            self.stdout.write(f'  Frequency: {frequency}')
            
            if monthly_duration and total_amount:
                self.stdout.write(f'  Monthly Duration: {monthly_duration} months')
                self.stdout.write(f'  Total Amount: RM {total_amount}')
                monthly_amount = fee_structure.get_monthly_amount()
                self.stdout.write(f'  Monthly Amount: RM {monthly_amount}')
            
            # Count students in this form
            students_in_form = Student.objects.filter(
                is_active=True
            ).filter(
                models.Q(level='form', level_custom__iexact=form) |
                models.Q(level='others', level_custom__iexact=form)
            )
            
            student_count = students_in_form.count()
            self.stdout.write(f'  Students in {form}: {student_count}')
            
            if auto_generate and frequency == 'monthly':
                self.stdout.write('  Auto-generating monthly payments...')
                generated_count = 0
                
                for student in students_in_form:
                    payments = fee_structure.generate_monthly_payments_for_student(student)
                    generated_count += len(payments)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Generated {generated_count} monthly payment records')
                )
            
            self.stdout.write('')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting up fee structure: {str(e)}')
            )
