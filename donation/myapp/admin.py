from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Student, Parent, FeeCategory, FeeStructure, Payment,
    PaymentReceipt, FeeDiscount, PaymentReminder, SchoolBankAccount, DonationEvent, DonationCategory
)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'first_name', 'last_name', 'year_batch', 'is_active')
    list_filter = ('year_batch', 'is_active')
    search_fields = ('student_id', 'first_name', 'last_name', 'nric')

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('user', 'nric', 'phone_number')
    search_fields = ('user__username', 'nric', 'phone_number')

@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name', 'description')

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
    readonly_fields = ('qr_code_display',)

    def qr_code_display(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="150" height="150" />', obj.qr_code.url)
        return "No QR code"
    qr_code_display.short_description = "QR Code"

admin.site.register(DonationCategory)

