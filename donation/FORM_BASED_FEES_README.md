# Form-Based Fee System

## Overview

The school fees module now implements a **form-based payment structure** where all students enrolled in the same form/grade level pay exactly the same amount for each fee category. This ensures fairness and consistency across the student body.

## How It Works

### 1. **Standardized Pricing by Form Level**
- **Form 1 students**: All pay the same amount for tuition, examination fees, etc.
- **Form 2 students**: All pay the same amount for their respective fees  
- **Form 3 students**: All pay the same amount for their respective fees
- **Form 4 students**: All pay the same amount for their respective fees
- **Form 5 students**: All pay the same amount for their respective fees

### 2. **Fee Structure Model**
The `FeeStructure` model now includes:
- `form` field: Specifies the form/grade level (e.g., "Form 1", "Form 2")
- `category`: Links to fee categories (Tuition, Examination, etc.)
- `amount`: Standard amount for all students in that form
- `frequency`: Payment frequency (monthly, termly, yearly)
- `monthly_duration` & `total_amount`: For monthly payment plans

### 3. **Automatic Student Matching**
When creating fee structures, the system automatically:
- Identifies students in the specified form level
- Applies the same fee amount to all students in that form
- Generates payment records for monthly payment plans

## Setting Up Fee Structures

### Using the Management Command

The easiest way to set up fee structures is using the provided management command:

```bash
# List all available forms and student counts
python manage.py setup_form_based_fees --list-forms

# List all available fee categories
python manage.py setup_form_based_fees --list-categories

# Show current fee structures
python manage.py setup_form_based_fees --show-current-fees

# Set up tuition fees for Form 3 (RM 3000 yearly)
python manage.py setup_form_based_fees --category "Tuition Fees" --form "Form 3" --amount 3000 --frequency yearly

# Set up monthly payment plan for Form 4 (RM 4000 over 10 months)
python manage.py setup_form_based_fees --category "Tuition Fees" --form "Form 4" --amount 400 --frequency monthly --monthly-duration 10 --total-amount 4000 --auto-generate

# Set up examination fees for Form 5 (RM 500 termly)
python manage.py setup_form_based_fees --category "Examination Fees" --form "Form 5" --amount 500 --frequency termly
```

### Using the Admin Interface

1. Go to **Fee Structure** in the admin panel
2. Click **Add Fee Structure**
3. Fill in the details:
   - **Category**: Select or create a fee category
   - **Form**: Enter the form level (e.g., "Form 1", "Form 2")
   - **Amount**: Set the standard amount for all students in that form
   - **Frequency**: Choose payment frequency
   - **Monthly Duration**: For monthly plans (10, 11, or 12 months)
   - **Total Amount**: For monthly payment plans
   - **Auto Generate Payments**: Check to automatically create payment records

## Student Experience

### What Students See
- Students only see fees relevant to their form level
- All students in the same form see identical fee amounts
- Individual fees (overtime, demerit penalties) are shown separately
- Payment history and status are personalized per student

### Fee Display Example
```
Form 3 Student View:
├── Tuition Fees: RM 3000 (Yearly)
├── Examination Fees: RM 500 (Termly)  
├── Library Fees: RM 100 (Yearly)
└── Individual Fees:
    └── Overtime Fee: RM 50 (Specific to this student)
```

## Technical Implementation

### Key Models

#### FeeStructure
```python
class FeeStructure(models.Model):
    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE)
    form = models.CharField(max_length=10)  # e.g., "Form 1", "Form 2"
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=[...])
    # ... other fields
```

#### FeeStatus  
```python
class FeeStatus(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # ... other fields
```

### Key Methods

#### FeeStructure.get_for_student()
```python
@classmethod
def get_for_student(cls, student, category=None):
    """Get fee structure for a student based on their form level"""
    student_level = student.get_level_display_value()
    return cls.objects.filter(
        form__iexact=student_level,
        is_active=True
    ).first()
```

#### FeeStatus.save()
```python
def save(self, *args, **kwargs):
    """Ensure amount is consistent with fee structure"""
    if self.fee_structure:
        student_level = self.student.get_level_display_value()
        if self.fee_structure.form.lower() == student_level.lower():
            # Use fee structure amount for consistency
            self.amount = self.fee_structure.get_monthly_amount() or self.fee_structure.amount
    super().save(*args, **kwargs)
```

## Benefits

### 1. **Fairness & Consistency**
- All students in the same form pay identical amounts
- No favoritism or price discrimination
- Transparent pricing structure

### 2. **Administrative Efficiency**
- Set fees once per form level
- Automatic student matching
- Easy to update fees for entire form levels

### 3. **Student Experience**
- Clear understanding of fee obligations
- Predictable payment amounts
- Easy comparison with peers

### 4. **Financial Planning**
- Consistent revenue streams
- Easy budgeting and forecasting
- Simplified payment tracking

## Migration from Old System

If you have existing fee structures:

1. **Review current fees**: Use `--show-current-fees` to see existing structures
2. **Standardize by form**: Update existing fees to use form-based structure
3. **Verify student levels**: Ensure students have correct form levels set
4. **Test with sample students**: Verify fees display correctly for different forms

## Troubleshooting

### Common Issues

1. **Students not seeing fees**
   - Check student's form level (`level` and `level_custom` fields)
   - Verify fee structure is active and matches student's form

2. **Incorrect fee amounts**
   - Ensure FeeStatus records use fee structure amounts
   - Check for individual fee overrides

3. **Missing fee categories**
   - Create fee categories with `category_type = 'general'`
   - Ensure categories are active

### Debug Commands

```bash
# Check student form levels
python manage.py shell
>>> from myapp.models import Student
>>> for s in Student.objects.filter(is_active=True):
...     print(f"{s.first_name}: {s.get_level_display_value()}")

# Check fee structures for specific form
>>> from myapp.models import FeeStructure
>>> FeeStructure.objects.filter(form__icontains="Form 3")
```

## Best Practices

1. **Naming Convention**: Use consistent form names (e.g., "Form 1", "Form 2")
2. **Fee Categories**: Group related fees logically (Tuition, Examination, etc.)
3. **Payment Plans**: Use monthly plans for large amounts, yearly for smaller fees
4. **Regular Review**: Periodically review and update fee structures
5. **Student Communication**: Clearly communicate fee changes to students and parents

## Support

For technical support or questions about the form-based fee system:
- Check the Django admin logs for errors
- Use the management commands for debugging
- Review the model relationships and database constraints
- Ensure all required fields are properly populated
