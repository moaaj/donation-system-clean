from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import (
    Student, Parent, FeeCategory, FeeStructure, Payment,
    PaymentReceipt, Invoice, FeeDiscount, PaymentReminder, SchoolBankAccount, DonationEvent, DonationCategory, IndividualStudentFee,
    PibgDonationSettings, PibgDonation, PredefinedDonationAmount, UserProfile, ModulePermission, SchoolFeesLevelAdmin
)


class PibgDonationSettingsForm(forms.ModelForm):
    """Custom form for PIBG donation settings with better amount management"""
    
    # Individual amount fields for easier management
    amount_1 = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        help_text="Preset amount 1 (RM) - Leave empty to disable"
    )
    amount_2 = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        help_text="Preset amount 2 (RM) - Leave empty to disable"
    )
    amount_3 = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        help_text="Preset amount 3 (RM) - Leave empty to disable"
    )
    amount_4 = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        help_text="Preset amount 4 (RM) - Leave empty to disable"
    )
    amount_5 = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        help_text="Preset amount 5 (RM) - Leave empty to disable"
    )
    amount_6 = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        help_text="Preset amount 6 (RM) - Leave empty to disable"
    )
    amount_7 = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        help_text="Preset amount 7 (RM) - Leave empty to disable"
    )
    amount_8 = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        help_text="Preset amount 8 (RM) - Leave empty to disable"
    )
    
    class Meta:
        model = PibgDonationSettings
        exclude = ['preset_amounts']  # Exclude the original field since we use individual fields
        widgets = {
            'donation_message': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate individual amount fields from preset_amounts
        if self.instance and self.instance.pk and self.instance.preset_amounts:
            amounts = self.instance.preset_amounts
            for i in range(1, 9):
                if i <= len(amounts):
                    self.fields[f'amount_{i}'].initial = amounts[i-1]
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Collect non-empty amounts
        amounts = []
        for i in range(1, 9):
            amount = cleaned_data.get(f'amount_{i}')
            if amount is not None and amount > 0:
                amounts.append(float(amount))
        
        # Update preset_amounts
        cleaned_data['preset_amounts'] = amounts
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Collect non-empty amounts from individual fields
        amounts = []
        for i in range(1, 9):
            amount = self.cleaned_data.get(f'amount_{i}')
            if amount is not None and amount > 0:
                amounts.append(float(amount))
        
        # Set the preset_amounts field
        instance.preset_amounts = amounts
        
        if commit:
            instance.save()
        return instance

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'first_name', 'last_name', 'phone_number', 'class_name', 'program', 'level_display', 'year_batch', 'is_active')
    list_filter = ('class_name', 'program', 'level', 'year_batch', 'is_active')
    search_fields = ('student_id', 'first_name', 'last_name', 'nric', 'phone_number', 'class_name', 'program')
    actions = ['delete_selected_students']
    fieldsets = (
        ('Basic Information', {
            'fields': ('student_id', 'nric', 'first_name', 'last_name', 'phone_number', 'year_batch')
        }),
        ('Academic Information', {
            'fields': ('class_name', 'program', 'level', 'level_custom')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def level_display(self, obj):
        return obj.get_level_display_value()
    level_display.short_description = 'Level'
    
    def delete_selected_students(self, request, queryset):
        """Custom delete action that properly cleans up user accounts and relationships"""
        deleted_count = 0
        deleted_users = []
        
        for student in queryset:
            try:
                # Get student information for logging
                student_name = f"{student.first_name} {student.last_name}"
                student_id = student.student_id
                
                # Delete associated user accounts and profiles
                user_profiles = student.user_profile.all()
                for user_profile in user_profiles:
                    if user_profile.user:
                        deleted_users.append(user_profile.user.username)
                        user_profile.user.delete()
                
                # Remove from parent relationships
                student.parents.clear()
                
                # Delete the student
                student.delete()
                deleted_count += 1
                
            except Exception as e:
                self.message_user(request, f'Error deleting student {student_name}: {str(e)}', level='ERROR')
        
        if deleted_count > 0:
            self.message_user(request, f'Successfully deleted {deleted_count} student(s). Deleted user accounts: {", ".join(deleted_users) if deleted_users else "None"}')
    
    delete_selected_students.short_description = "Delete selected students and their user accounts"

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('user', 'nric', 'phone_number')
    search_fields = ('user__username', 'nric', 'phone_number')

@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'is_active')
    list_filter = ('category_type', 'is_active')
    search_fields = ('name', 'description')

@admin.register(IndividualStudentFee)
class IndividualStudentFeeAdmin(admin.ModelAdmin):
    list_display = ('student', 'name', 'category', 'amount', 'due_date', 'status_display', 'is_active')
    list_filter = ('category', 'is_paid', 'is_active', 'due_date')
    search_fields = ('student__first_name', 'student__last_name', 'name', 'description')
    date_hierarchy = 'due_date'
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'category')
        }),
        ('Fee Details', {
            'fields': ('name', 'description', 'amount', 'due_date')
        }),
        ('Status', {
            'fields': ('is_paid', 'is_active')
        }),
        ('Administrative', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        return obj.get_status_display()
    status_display.short_description = 'Status'

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('category', 'form', 'amount', 'frequency', 'is_active')
    list_filter = ('category', 'form', 'frequency', 'is_active')
    search_fields = ('category__name', 'form')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_structure', 'amount', 'payment_method', 'status', 'payment_date')
    list_filter = ('payment_method', 'status', 'payment_date')
    search_fields = ('student__first_name', 'student__last_name', 'receipt_number')
    date_hierarchy = 'payment_date'

@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(admin.ModelAdmin):
    list_display = ('payment', 'generated_at', 'sent_at')
    list_filter = ('generated_at', 'sent_at')
    search_fields = ('payment__receipt_number',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'student', 'amount', 'total_amount', 'status', 'issue_date', 'due_date')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('invoice_number', 'student__first_name', 'student__last_name', 'student__student_id')
    date_hierarchy = 'issue_date'
    readonly_fields = ('invoice_number', 'total_amount')
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'student', 'payment', 'amount', 'tax_amount', 'total_amount')
        }),
        ('Dates', {
            'fields': ('issue_date', 'due_date')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Additional Information', {
            'fields': ('notes', 'terms_conditions'),
            'classes': ('collapse',)
        }),
    )

@admin.register(FeeDiscount)
class FeeDiscountAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_structure', 'discount_type', 'value', 'is_active')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('student__first_name', 'student__last_name', 'reason')

@admin.register(PaymentReminder)
class PaymentReminderAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_structure', 'due_date', 'status', 'reminder_count')
    list_filter = ('status', 'due_date')
    search_fields = ('student__first_name', 'student__last_name')

@admin.register(SchoolBankAccount)
class SchoolBankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'account_number', 'bank_name', 'branch', 'is_active')
    list_filter = ('bank_name', 'is_active')
    search_fields = ('account_name', 'account_number', 'bank_name')

@admin.register(DonationEvent)
class DonationEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'target_amount', 'start_date', 'end_date', 'is_active', 'qr_code_display')
    list_filter = ('category', 'start_date', 'end_date', 'is_active')
    search_fields = ('title', 'category')
    readonly_fields = ('qr_code_display', 'picture_display', 'e_poster_display')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'target_amount', 'current_amount')
        }),
        ('Event Dates', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
        ('Event Files', {
            'fields': ('picture', 'picture_display', 'formal_letter', 'e_poster', 'e_poster_display'),
            'classes': ('collapse',)
        }),
        ('QR Code', {
            'fields': ('qr_code', 'qr_code_display'),
            'classes': ('collapse',)
        }),
        ('AI Analytics', {
            'fields': ('sentiment_score', 'sentiment_subjectivity', 'predicted_completion_rate', 'predicted_final_amount', 'estimated_days_to_completion'),
            'classes': ('collapse',)
        }),
    )

    def qr_code_display(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="150" height="150" />', obj.qr_code.url)
        return "No QR code"
    qr_code_display.short_description = "QR Code"
    
    def picture_display(self, obj):
        if obj.picture:
            return format_html('<img src="{}" width="200" height="150" style="object-fit: cover;" />', obj.picture.url)
        return "No picture uploaded"
    picture_display.short_description = "Picture Preview"
    
    def e_poster_display(self, obj):
        if obj.e_poster:
            return format_html('<img src="{}" width="200" height="150" style="object-fit: cover;" />', obj.e_poster.url)
        return "No e-poster uploaded"
    e_poster_display.short_description = "E-Poster Preview"

admin.site.register(DonationCategory)

@admin.register(PredefinedDonationAmount)
class PredefinedDonationAmountAdmin(admin.ModelAdmin):
    list_display = ('formatted_amount', 'is_active', 'display_order', 'created_at')
    list_filter = ('is_active', 'created_at')
    list_editable = ('is_active', 'display_order')
    ordering = ['display_order', 'amount']
    search_fields = ('amount',)
    actions = ['activate_amounts', 'deactivate_amounts', 'reset_display_order']
    
    fieldsets = (
        ('Amount Settings', {
            'fields': ('amount', 'is_active', 'display_order'),
            'description': 'Configure predefined donation amounts that appear as quick-select buttons on the donation page.'
        }),
    )
    
    def formatted_amount(self, obj):
        return obj.formatted_amount()
    formatted_amount.short_description = 'Amount'
    
    def has_add_permission(self, request):
        # Allow superusers and staff to add predefined amounts
        return request.user.is_staff
    
    def has_change_permission(self, request, obj=None):
        # Allow superusers and staff to change predefined amounts
        return request.user.is_staff
    
    def has_delete_permission(self, request, obj=None):
        # Allow superusers and staff to delete predefined amounts
        return request.user.is_staff
    
    def activate_amounts(self, request, queryset):
        """Activate selected amounts"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} amounts activated successfully.')
    activate_amounts.short_description = "Activate selected amounts"
    
    def deactivate_amounts(self, request, queryset):
        """Deactivate selected amounts"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} amounts deactivated successfully.')
    deactivate_amounts.short_description = "Deactivate selected amounts"
    
    def reset_display_order(self, request, queryset):
        """Reset display order for selected amounts"""
        for i, amount in enumerate(queryset.order_by('amount'), 1):
            amount.display_order = i
            amount.save()
        self.message_user(request, f'Display order reset for {queryset.count()} amounts.')
    reset_display_order.short_description = "Reset display order"

@admin.register(PibgDonationSettings)
class PibgDonationSettingsAdmin(admin.ModelAdmin):
    form = PibgDonationSettingsForm
    list_display = ('banner_text', 'is_enabled', 'is_mandatory', 'preset_amounts_display', 'updated_at')
    list_editable = ('is_enabled', 'is_mandatory')
    readonly_fields = ('created_at', 'updated_at', 'preset_amounts_preview')
    actions = ['set_default_amounts', 'clear_all_amounts', 'quick_set_common_amounts']
    fieldsets = (
        ('General Settings', {
            'fields': ('is_enabled', 'is_mandatory'),
            'description': 'Configure whether PIBG donations are enabled and mandatory'
        }),
        ('Display Settings', {
            'fields': ('banner_text', 'donation_message'),
            'description': 'Customize the text displayed to users'
        }),
        ('Preset Donation Amounts', {
            'fields': ('amount_1', 'amount_2', 'amount_3', 'amount_4', 'amount_5', 'amount_6', 'amount_7', 'amount_8', 'preset_amounts_preview'),
            'description': 'Set up to 8 preset donation amounts (leave empty to disable an amount). Changes are applied immediately upon saving.'
        }),
        ('Custom Amount Settings', {
            'fields': ('minimum_custom_amount', 'maximum_custom_amount'),
            'description': 'Configure limits for custom donation amounts'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    class Media:
        js = ('admin/js/donation_amounts_admin.js',)
        css = {
            'all': ('admin/css/donation_amounts_admin.css',)
        }
    
    def preset_amounts_display(self, obj):
        """Display preset amounts in a readable format"""
        if obj.preset_amounts:
            amounts = [f"RM{amount}" for amount in obj.preset_amounts]
            return ", ".join(amounts)
        return "No amounts set"
    preset_amounts_display.short_description = 'Preset Amounts'
    
    def donation_message_preview(self, obj):
        return obj.donation_message[:50] + "..." if len(obj.donation_message) > 50 else obj.donation_message
    donation_message_preview.short_description = 'Message Preview'
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not PibgDonationSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False
    
    def set_default_amounts(self, request, queryset):
        """Set default preset amounts"""
        for settings in queryset:
            settings.preset_amounts = [10, 20, 30, 50, 100]
            settings.save()
        self.message_user(request, f'Default amounts set for {queryset.count()} settings.')
    set_default_amounts.short_description = "Set default amounts (RM10, RM20, RM30, RM50, RM100)"
    
    def clear_all_amounts(self, request, queryset):
        """Clear all preset amounts"""
        for settings in queryset:
            settings.preset_amounts = []
            settings.save()
        self.message_user(request, f'All amounts cleared for {queryset.count()} settings.')
    clear_all_amounts.short_description = "Clear all preset amounts"
    
    def quick_set_common_amounts(self, request, queryset):
        """Set commonly used preset amounts"""
        for settings in queryset:
            settings.preset_amounts = [10, 20, 30, 50, 100, 150, 200, 250]
            settings.save()
        self.message_user(request, f'Common amounts set for {queryset.count()} settings.')
    quick_set_common_amounts.short_description = "Set common amounts (RM10-RM250)"
    
    def preset_amounts_preview(self, obj):
        """Show a preview of how the amounts will appear to users"""
        if obj.preset_amounts:
            preview_html = '<div style="margin: 10px 0;">'
            preview_html += '<strong>Preview (as shown to users):</strong><br>'
            for i, amount in enumerate(obj.preset_amounts, 1):
                preview_html += f'<span style="display: inline-block; margin: 2px; padding: 5px 10px; border: 1px solid #007cba; border-radius: 3px; background: #f0f8ff;">RM {amount}</span>'
                if i % 4 == 0:  # New line every 4 amounts
                    preview_html += '<br>'
            preview_html += '</div>'
            return format_html(preview_html)
        return format_html('<em>No amounts configured</em>')
    preset_amounts_preview.short_description = 'Preview'
    
    def save_model(self, request, obj, form, change):
        """Custom save method to ensure preset amounts are properly updated"""
        # The form's save method should handle the preset_amounts update
        super().save_model(request, obj, form, change)
        
        # Add a success message with the updated amounts
        if obj.preset_amounts:
            amounts_str = ', '.join([f'RM{amount}' for amount in obj.preset_amounts])
            self.message_user(request, f'Preset amounts updated: {amounts_str}', level='SUCCESS')
        else:
            self.message_user(request, 'All preset amounts cleared. Users will only see custom amount input.', level='WARNING')

@admin.register(PibgDonation)
class PibgDonationAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'student_name', 'parent_name', 'amount', 'payment_method', 'status', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('receipt_number', 'student__first_name', 'student__last_name', 'parent__first_name', 'parent__last_name')
    readonly_fields = ('receipt_number', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Donation Information', {
            'fields': ('student', 'parent', 'amount', 'receipt_number')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'status', 'transaction_id', 'related_payment')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def student_name(self, obj):
        if obj.student:
            return f"{obj.student.first_name} {obj.student.last_name} ({obj.student.student_id})"
        return "-"
    student_name.short_description = 'Student'
    
    def parent_name(self, obj):
        if obj.parent:
            return f"{obj.parent.user.first_name} {obj.parent.user.last_name}" if obj.parent.user.first_name or obj.parent.user.last_name else obj.parent.user.username
        return "-"
    parent_name.short_description = 'Parent'
    
    def has_add_permission(self, request):
        # Donations should be created through the checkout process
        return False


# Enhanced User Profile Admin with Module Permissions
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_module_admin', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'phone_number', 'address')
        }),
        ('Student Association', {
            'fields': ('student',),
            'description': 'Link to student record if applicable'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_module_admin(self, obj):
        return obj.is_module_admin()
    is_module_admin.boolean = True
    is_module_admin.short_description = 'Module Admin'


@admin.register(ModulePermission)
class ModulePermissionAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'module', 'can_view', 'can_add', 'can_change', 'can_delete', 'can_manage_settings')
    list_filter = ('module', 'can_view', 'can_add', 'can_change', 'can_delete', 'can_manage_settings')
    search_fields = ('user_profile__user__username', 'user_profile__user__first_name', 'user_profile__user__last_name')
    list_editable = ('can_view', 'can_add', 'can_change', 'can_delete', 'can_manage_settings')
    
    fieldsets = (
        ('Permission Assignment', {
            'fields': ('user_profile', 'module'),
            'description': 'Assign module permissions to specific users'
        }),
        ('View Permissions', {
            'fields': ('can_view',),
            'description': 'Basic viewing permissions'
        }),
        ('Modification Permissions', {
            'fields': ('can_add', 'can_change', 'can_delete'),
            'description': 'Data modification permissions'
        }),
        ('Administrative Permissions', {
            'fields': ('can_manage_settings',),
            'description': 'Settings and configuration management'
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user_profile__user')


@admin.register(SchoolFeesLevelAdmin)
class SchoolFeesLevelAdminAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'level', 'can_view', 'can_add', 'can_change', 'can_manage_fees', 'can_manage_payments')
    list_filter = ('level', 'can_view', 'can_add', 'can_change', 'can_manage_fees', 'can_manage_payments')
    search_fields = ('user_profile__user__username', 'user_profile__user__first_name', 'user_profile__user__last_name')
    list_editable = ('can_view', 'can_add', 'can_change', 'can_manage_fees', 'can_manage_payments')
    
    fieldsets = (
        ('Level Assignment', {
            'fields': ('user_profile', 'level'),
            'description': 'Assign school fees level permissions to specific users'
        }),
        ('View Permissions', {
            'fields': ('can_view',),
            'description': 'Basic viewing permissions for the assigned level'
        }),
        ('Modification Permissions', {
            'fields': ('can_add', 'can_change', 'can_delete'),
            'description': 'Data modification permissions for the assigned level'
        }),
        ('Specialized Permissions', {
            'fields': ('can_manage_fees', 'can_manage_payments'),
            'description': 'Specialized school fees management permissions'
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user_profile__user')



