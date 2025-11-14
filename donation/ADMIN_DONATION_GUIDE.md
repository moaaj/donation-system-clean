# Admin Guide: Configuring Donation Amounts

## Overview
The donation system provides flexible configuration options for administrators to customize preset donation amounts, validation rules, and display settings. This guide covers all available methods to manage donation amounts.

## Current Status ✅
- **Preset Amounts**: 8 configurable slots (all currently active)
- **Current Values**: RM 10, 20, 30, 50, 100, 150, 200, 250
- **Admin Interface**: Fully functional with individual amount fields
- **Template Integration**: Automatic updates without code changes

## Method 1: Django Admin Interface (Recommended)

### Accessing the Admin Interface
1. Navigate to `/admin/` in your web browser
2. Log in with administrator credentials
3. Go to **PIBG Donation Settings** under the appropriate section

### Configuring Amounts
The admin interface provides 8 individual fields:
- **Amount 1** through **Amount 8**
- Each field accepts decimal values (e.g., 10.50, 25.00)
- **Leave empty** to disable a specific amount slot
- Changes are **immediate** upon saving

### Example Configuration
```
Amount 1: 10.00    (displays as "RM 10")
Amount 2: 25.00    (displays as "RM 25") 
Amount 3: 50.00    (displays as "RM 50")
Amount 4: 100.00   (displays as "RM 100")
Amount 5: [empty]  (slot disabled)
Amount 6: [empty]  (slot disabled)
Amount 7: [empty]  (slot disabled)
Amount 8: [empty]  (slot disabled)
```

### Additional Settings Available
- **Banner Text**: Customize the donation section title
- **Donation Message**: Descriptive text shown to users
- **Is Mandatory**: Make donations required during checkout
- **Is Enabled**: Enable/disable the entire donation feature
- **Minimum Custom Amount**: Lower limit for custom donations
- **Maximum Custom Amount**: Upper limit for custom donations

## Method 2: Management Commands

### Setup Command
```bash
# Set specific amounts
python manage.py setup_pibg_donation_amounts --amounts 15 25 35 50 75 100 150 200

# Reset to default amounts
python manage.py setup_pibg_donation_amounts --reset

# View current settings (no changes)
python manage.py setup_pibg_donation_amounts
```

### Examples
```bash
# Configure 5 amounts
python manage.py setup_pibg_donation_amounts --amounts 10 20 50 100 200

# Configure 3 amounts only
python manage.py setup_pibg_donation_amounts --amounts 25 50 100

# Reset to system defaults
python manage.py setup_pibg_donation_amounts --reset
```

## Method 3: Programmatic Updates

### Using Django Shell
```python
# Access Django shell
python manage.py shell

# Update amounts programmatically
from myapp.models import PibgDonationSettings

# Get settings instance
settings = PibgDonationSettings.get_settings()

# Update preset amounts
settings.preset_amounts = [15, 30, 45, 60, 100, 150]
settings.save()

# Verify changes
print("Updated amounts:", settings.preset_amounts)
```

### In Django Views/Code
```python
from myapp.models import PibgDonationSettings

def update_donation_amounts(new_amounts):
    settings = PibgDonationSettings.get_settings()
    settings.preset_amounts = new_amounts
    settings.save()
    return settings

# Usage
update_donation_amounts([10, 25, 50, 75, 125])
```

## Template Integration

### Automatic Display
The templates automatically display amounts from the database:
```html
{% for amount in donation_settings.preset_amounts %}
<div class="col-6 col-md-4 mb-2">
    <div class="form-check">
        <input class="form-check-input" type="radio" 
               name="donation_amount" 
               id="preset_{{ amount }}" 
               value="{{ amount }}">
        <label class="form-check-label btn btn-outline-primary w-100 text-center" 
               for="preset_{{ amount }}">
            RM {{ amount }}
        </label>
    </div>
</div>
{% endfor %}
```

### Files Using Donation Settings
- `donation/templates/myapp/cart.html`
- `donation/myapp/templates/myapp/parent_checkout.html`
- `donation/donation2/templates/donation2/donate.html`

## Validation Rules

### Amount Constraints
- **Minimum Value**: 0.01 (system enforced)
- **Maximum Value**: No system limit (admin discretion)
- **Decimal Places**: Up to 2 decimal places supported
- **Empty Slots**: Automatically excluded from display

### Custom Amount Limits
- **Minimum Custom**: RM 5.00 (configurable)
- **Maximum Custom**: RM 1000.00 (configurable)
- **Validation**: Enforced during form submission

## Best Practices

### Amount Selection
1. **Use round numbers** for better user experience (10, 20, 50, 100)
2. **Progressive scaling** - start small, increase gradually
3. **Consider your audience** - school fees context suggests moderate amounts
4. **Leave room for growth** - don't use all 8 slots initially

### Configuration Management
1. **Test changes** in development environment first
2. **Document changes** for audit purposes
3. **Communicate updates** to relevant stakeholders
4. **Monitor usage patterns** to optimize amounts

### Maintenance
1. **Regular review** of amount effectiveness
2. **Seasonal adjustments** if applicable
3. **User feedback integration**
4. **Performance monitoring** (no impact expected)

## Troubleshooting

### Common Issues
1. **Amounts not displaying**: Check if `is_enabled = True`
2. **Empty amount list**: Verify at least one amount is configured
3. **Validation errors**: Ensure amounts are positive numbers
4. **Template errors**: Check for proper context passing in views

### Debugging Commands
```bash
# Check current settings
python manage.py shell -c "from myapp.models import PibgDonationSettings; print(PibgDonationSettings.get_settings().preset_amounts)"

# Verify admin access
python manage.py shell -c "from django.contrib.auth.models import User; print('Superusers:', User.objects.filter(is_superuser=True).count())"

# Test template context
python manage.py shell -c "from myapp.models import PibgDonationSettings; settings = PibgDonationSettings.get_settings(); print('Template will show:', len(settings.preset_amounts), 'amounts')"
```

## Security Considerations

### Admin Access
- Only superusers should modify donation settings
- Regular audit of admin user accounts
- Strong password requirements for admin accounts

### Data Validation
- All amounts validated on both client and server side
- SQL injection protection through Django ORM
- XSS protection in template rendering

## Recent Changes Log

### 2024-10-04
- ✅ Updated from 5 to 8 preset amounts
- ✅ Current amounts: [10, 20, 30, 50, 100, 150, 200, 250]
- ✅ Verified admin interface functionality
- ✅ Confirmed template integration working
- ✅ Management commands tested and working

## Support

For technical support or questions about donation configuration:
1. Check this documentation first
2. Test changes in development environment
3. Use management commands for bulk operations
4. Contact system administrator for access issues

---

**Note**: All changes to donation amounts are immediate and affect all users. Test thoroughly before applying to production systems.
