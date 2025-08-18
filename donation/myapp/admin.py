from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Student, Parent, FeeCategory, FeeStructure, Payment,
    PaymentReceipt, Invoice, FeeDiscount, PaymentReminder, SchoolBankAccount, DonationEvent, DonationCategory, IndividualStudentFee
)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'first_name', 'last_name', 'class_name', 'program', 'level_display', 'year_batch', 'is_active')
    list_filter = ('class_name', 'program', 'level', 'year_batch', 'is_active')
    search_fields = ('student_id', 'first_name', 'last_name', 'nric', 'class_name', 'program')
    fieldsets = (
        ('Basic Information', {
            'fields': ('student_id', 'nric', 'first_name', 'last_name', 'year_batch')
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

