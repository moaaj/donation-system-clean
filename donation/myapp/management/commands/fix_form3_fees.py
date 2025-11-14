from django.core.management.base import BaseCommand
from django.db import models
from datetime import date, timedelta
from myapp.models import Student, FeeStructure, FeeStatus


class Command(BaseCommand):
    help = 'Fix Form 3 fees display by creating missing FeeStatus records'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Fixing Form 3 Fees Display Issue'))
        self.stdout.write('=' * 50)
        
        # Get all Form 3 students
        form3_students = Student.objects.filter(
            is_active=True,
            level='form',
            level_custom__iexact='Form 3'
        )
        
        self.stdout.write(f'Found {form3_students.count()} Form 3 students')
        
        if form3_students.count() == 0:
            self.stdout.write(self.style.ERROR('No Form 3 students found!'))
            return
        
        # Get all active Form 3 fee structures
        form3_fee_structures = FeeStructure.objects.filter(
            form__iexact='Form 3',
            is_active=True
        )
        
        self.stdout.write(f'Found {form3_fee_structures.count()} Form 3 fee structures')
        
        if form3_fee_structures.count() == 0:
            self.stdout.write(self.style.ERROR('No Form 3 fee structures found!'))
            return
        
        # Display existing fee structures
        self.stdout.write('\nForm 3 Fee Structures:')
        for fee_structure in form3_fee_structures:
            self.stdout.write(f'   - {fee_structure.category.name}: RM {fee_structure.amount} ({fee_structure.frequency})')
        
        total_created = 0
        students_processed = 0
        
        # Process each student
        for student in form3_students:
            self.stdout.write(f'\nProcessing student: {student.first_name} {student.last_name} ({student.student_id})')
            
            student_created = 0
            
            # Check existing fee status records
            existing_statuses = FeeStatus.objects.filter(student=student)
            self.stdout.write(f'   Existing fee status records: {existing_statuses.count()}')
            
            # Create missing fee status records
            for fee_structure in form3_fee_structures:
                # Check if fee status already exists
                existing_status = FeeStatus.objects.filter(
                    student=student,
                    fee_structure=fee_structure
                ).first()
                
                if existing_status:
                    self.stdout.write(f'   {fee_structure.category.name}: Already exists (Status: {existing_status.status})')
                else:
                    # Calculate due date based on frequency
                    if fee_structure.frequency == 'yearly':
                        due_date = date.today() + timedelta(days=30)
                    elif fee_structure.frequency == 'termly':
                        due_date = date.today() + timedelta(days=90)
                    elif fee_structure.frequency == 'monthly':
                        due_date = date.today() + timedelta(days=30)
                    else:
                        due_date = date.today() + timedelta(days=30)
                    
                    # Create fee status
                    fee_status = FeeStatus.objects.create(
                        student=student,
                        fee_structure=fee_structure,
                        amount=fee_structure.amount or 0,
                        due_date=due_date,
                        status='pending'
                    )
                    
                    self.stdout.write(f'   Created {fee_structure.category.name}: RM {fee_status.amount} (Due: {fee_status.due_date})')
                    student_created += 1
            
            if student_created > 0:
                self.stdout.write(f'   Created {student_created} fee status records for {student.first_name}')
                total_created += student_created
            
            students_processed += 1
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('SUMMARY')
        self.stdout.write('=' * 50)
        self.stdout.write(f'Students processed: {students_processed}')
        self.stdout.write(f'Fee status records created: {total_created}')
        
        if total_created > 0:
            self.stdout.write(self.style.SUCCESS(f'\nSUCCESS! Form 3 students can now see their fees in the student portal.'))
            self.stdout.write(f'   {total_created} fee status records were created')
            self.stdout.write(f'   All Form 3 students now have pending fees visible')
        else:
            self.stdout.write(self.style.SUCCESS(f'\nAll Form 3 students already have their fee status records.'))
        
        # Verify the fix
        self.stdout.write(f'\nVERIFICATION:')
        for student in form3_students:
            fee_statuses = FeeStatus.objects.filter(student=student)
            self.stdout.write(f'   {student.first_name} {student.last_name}: {fee_statuses.count()} fee status records')
            for status in fee_statuses:
                self.stdout.write(f'     - {status.fee_structure.category.name}: RM {status.amount} ({status.status})')
