# Student Discount & Scholarship Functionality

## Overview

This document describes the comprehensive discount and scholarship functionality implemented in the MOAAJ system. When admins approve scholarships or discounts for students, the students can see their discounted fees and pay only the reduced amount.

## Key Features

### 1. **Automatic Discount Calculation**
- Students see discounted amounts automatically when waivers are approved
- Support for both percentage-based and fixed amount discounts
- Multiple waivers can be combined for cumulative discounts
- Only approved and active waivers are applied

### 2. **Student Fee Display**
- Clear display of original vs discounted amounts
- Visual indicators showing applied discounts
- Detailed breakdown of waiver types and reasons
- Real-time calculation of final payment amounts

### 3. **Payment Processing**
- Students pay only the discounted amount
- Payment records reflect the actual amount paid
- Fee statuses are updated to reflect payment completion
- Receipts show the discounted amount paid

## How It Works

### 1. **Admin Creates and Approves Waivers**

Admins can create fee waivers through the admin interface:

```python
# Example: Creating a 25% scholarship
waiver = FeeWaiver.objects.create(
    student=student,
    category=tuition_category,
    waiver_type='scholarship',
    amount=Decimal('0.00'),
    percentage=Decimal('25.00'),  # 25% discount
    reason='Academic excellence scholarship',
    start_date=date.today(),
    end_date=date.today() + timedelta(days=365),
    status='approved',
    approved_date=timezone.now()
)

# Example: Creating a fixed amount discount
waiver = FeeWaiver.objects.create(
    student=student,
    category=tuition_category,
    waiver_type='discount',
    amount=Decimal('500.00'),  # RM 500 discount
    percentage=None,
    reason='Merit-based discount',
    start_date=date.today(),
    end_date=date.today() + timedelta(days=365),
    status='approved',
    approved_date=timezone.now()
)
```

### 2. **Student Views Discounted Fees**

Students see their fees with discount information:

```
Original Amount: RM 3,000.00 (crossed out)
Discount: -RM 750.00 (Scholarship)
Amount to Pay: RM 2,250.00 (highlighted)
```

### 3. **Payment Processing**

When students add fees to cart and checkout:
- Only the discounted amount is charged
- Payment records show the actual amount paid
- Fee statuses are marked as paid

## Implementation Details

### 1. **Enhanced FeeStatus Model**

The `FeeStatus` model includes discount calculation methods:

```python
class FeeStatus(models.Model):
    # ... existing fields ...
    
    def get_original_amount(self):
        """Get the original fee amount before any discounts"""
        return self.amount
    
    def get_discounted_amount(self):
        """Calculate the discounted amount based on approved waivers"""
        from django.utils import timezone
        today = timezone.now().date()
        
        # Get all active approved waivers for this student and fee category
        active_waivers = FeeWaiver.objects.filter(
            student=self.student,
            category=self.fee_structure.category,
            status='approved',
            start_date__lte=today,
            end_date__gte=today
        )
        
        if not active_waivers.exists():
            return self.amount
        
        # Calculate total discount
        total_discount = 0
        original_amount = self.amount
        
        for waiver in active_waivers:
            if waiver.percentage:
                # Percentage-based discount
                discount_amount = (original_amount * waiver.percentage) / 100
                total_discount += discount_amount
            else:
                # Fixed amount discount
                total_discount += waiver.amount
        
        # Ensure discount doesn't exceed original amount
        discounted_amount = max(0, original_amount - total_discount)
        return discounted_amount
    
    def get_discount_info(self):
        """Get detailed information about applied discounts"""
        # ... implementation details ...
```

### 2. **Enhanced Student Views**

The student fee display shows:

```html
<!-- Original Amount -->
<td>
    {% if fee_status.discount_info.has_discount %}
        <span class="text-decoration-line-through text-muted">
            RM {{ fee_status.discount_info.original_amount|floatformat:2 }}
        </span>
    {% else %}
        RM {{ fee_status.amount|floatformat:2 }}
    {% endif %}
</td>

<!-- Discount Information -->
<td>
    {% if fee_status.discount_info.has_discount %}
        <span class="badge bg-success">
            -RM {{ fee_status.discount_info.total_discount|floatformat:2 }}
        </span>
        <br><small class="text-muted">
            {% for waiver in fee_status.discount_info.waivers %}
                {{ waiver.type }}{% if not forloop.last %}, {% endif %}
            {% endfor %}
        </small>
    {% else %}
        <span class="text-muted">-</span>
    {% endif %}
</td>

<!-- Final Amount to Pay -->
<td>
    <strong class="text-primary">
        RM {{ fee_status.discount_info.discounted_amount|floatformat:2 }}
    </strong>
</td>
```

### 3. **Enhanced Cart and Payment Processing**

The cart system handles discounted amounts:

```python
# In checkout_cart view
for fee_status in fee_statuses:
    # Get discounted amount
    discounted_amount = fee_status.get_discounted_amount()
    
    # Create payment record with discounted amount
    payment = Payment.objects.create(
        student=student,
        fee_structure=fee_status.fee_structure,
        amount=discounted_amount,  # Use discounted amount
        payment_date=timezone.now().date(),
        payment_method='online',
        status='completed'
    )
    
    # Update fee status to paid
    fee_status.status = 'paid'
    fee_status.save()
```

## Waiver Types

### 1. **Scholarship**
- Typically percentage-based discounts
- Based on academic performance
- Example: 25% scholarship for academic excellence

### 2. **Discount**
- Fixed amount reductions
- Based on merit, need, or special circumstances
- Example: RM 500 discount for merit students

### 3. **Fee Waiver**
- Complete fee exemption
- Usually 100% discount
- Example: Full waiver for special circumstances

## Waiver Status

### 1. **Pending**
- Waiver is created but not yet approved
- Does not affect student fees
- Students cannot see pending waivers

### 2. **Approved**
- Waiver is active and applied to fees
- Students see discounted amounts
- Affects payment calculations

### 3. **Rejected**
- Waiver is denied
- Does not affect student fees
- Students cannot see rejected waivers

### 4. **Expired**
- Waiver is past its end date
- No longer applied to fees
- Students see original amounts

## Admin Interface

### 1. **Creating Waivers**
1. Navigate to Fee Waivers & Scholarships
2. Click "+ Add New Waiver"
3. Fill in student details and waiver information
4. Set waiver type, amount/percentage, and validity period
5. Save the waiver

### 2. **Approving Waivers**
1. View pending waivers in the list
2. Click "Approve" button for the waiver
3. Waiver status changes to "Approved"
4. Students immediately see discounted amounts

### 3. **Managing Waivers**
- View all waivers with their status
- Edit waiver details
- Reject pending waivers
- View waiver letters

## Student Experience

### 1. **Viewing Fees**
- Students see their fees with discount information
- Original amounts are crossed out if discounts apply
- Discount amounts are clearly shown
- Final amounts to pay are highlighted

### 2. **Adding to Cart**
- Students add discounted fees to cart
- Cart shows the discounted amounts
- Total calculation reflects discounts

### 3. **Making Payments**
- Students pay only the discounted amount
- Receipts show the actual amount paid
- Payment history reflects discounted payments

## Testing

A comprehensive test script (`test_discount_functionality.py`) verifies:

1. ✅ Original amount calculation
2. ✅ Percentage discount calculation
3. ✅ Fixed amount discount calculation
4. ✅ Combined discount calculation
5. ✅ Expired waiver handling
6. ✅ Pending waiver handling
7. ✅ Student fee display

### Running the Test

```bash
cd donation
python test_discount_functionality.py
```

## Example Scenarios

### Scenario 1: Academic Scholarship
- **Student**: Form 3 student with RM 3,000 tuition
- **Waiver**: 25% academic scholarship
- **Result**: Student pays RM 2,250 instead of RM 3,000

### Scenario 2: Multiple Discounts
- **Student**: Form 4 student with RM 3,500 tuition
- **Waiver 1**: 20% scholarship
- **Waiver 2**: RM 300 merit discount
- **Calculation**: RM 3,500 - (RM 700 + RM 300) = RM 2,500
- **Result**: Student pays RM 2,500 instead of RM 3,500

### Scenario 3: Full Waiver
- **Student**: Form 5 student with RM 4,000 tuition
- **Waiver**: 100% fee waiver for special circumstances
- **Result**: Student pays RM 0 instead of RM 4,000

## Best Practices

### 1. **For Admins**
- Always verify student eligibility before approving waivers
- Set appropriate validity periods for waivers
- Use descriptive reasons for waivers
- Monitor waiver usage and effectiveness

### 2. **For Students**
- Check fee status regularly for new discounts
- Understand the terms and conditions of waivers
- Keep track of waiver expiration dates
- Contact admin if waiver issues arise

### 3. **System Management**
- Regular cleanup of expired waivers
- Monitor waiver approval workflows
- Backup waiver data regularly
- Audit waiver usage for compliance

## Troubleshooting

### Common Issues

1. **Discount not showing**
   - Check if waiver is approved
   - Verify waiver dates are current
   - Ensure waiver category matches fee category

2. **Incorrect discount calculation**
   - Verify waiver amounts and percentages
   - Check for multiple conflicting waivers
   - Ensure fee amounts are correct

3. **Payment issues**
   - Verify discounted amounts in cart
   - Check payment processing logs
   - Ensure fee status updates correctly

### Debugging

Use the test script to verify discount functionality:

```bash
python test_discount_functionality.py
```

The test will show detailed information about discount calculations and verify that all functionality works correctly.

## Future Enhancements

1. **Automatic Waiver Application** - Automatically apply waivers based on criteria
2. **Waiver Templates** - Predefined waiver templates for common scenarios
3. **Bulk Waiver Management** - Apply waivers to multiple students at once
4. **Waiver Analytics** - Track waiver usage and effectiveness
5. **Notification System** - Notify students when waivers are approved/expired
