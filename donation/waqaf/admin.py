from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path
from django.template.response import TemplateResponse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import WaqafAsset, Contributor, FundDistribution, Contribution, Payment


@admin.register(WaqafAsset)
class WaqafAssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'target_amount', 'total_slots', 'slots_available', 'slot_price', 'current_value', 'status_display', 'contribution_count', 'total_contributed', 'funding_progress', 'is_archived', 'archived_at')
    search_fields = ('name', 'description')
    list_filter = ('total_slots', 'slots_available', 'is_archived')
    readonly_fields = ('slots_available', 'slot_price', 'status_display', 'contribution_count', 'total_contributed', 'funding_progress', 'is_archived', 'archived_at', 'archived_by')
    actions = ['calculate_slot_prices', 'archive_assets', 'unarchive_assets', 'delete_archived_assets', 'bulk_archive_completed', 'bulk_unarchive_all']
    change_form_template = 'admin/waqaf/waqafasset/change_form.html'
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Financial Details', {
            'fields': ('current_value', 'target_amount', 'total_slots', 'slot_price'),
            'description': 'Set target_amount and total_slots to auto-calculate slot_price'
        }),
        ('Status & Progress', {
            'fields': ('status_display', 'contribution_count', 'total_contributed', 'funding_progress'),
            'classes': ('collapse',)
        }),
        ('Archive Status', {
            'fields': ('is_archived', 'archived_at', 'archived_by'),
            'classes': ('collapse',)
        }),
    )

    def status_display(self, obj):
        """Display status with color coding"""
        status = obj.get_status_display()
        if status == "Archived":
            return f'<span style="color: #dc3545; font-weight: bold;">{status}</span>'
        elif status == "Completed":
            return f'<span style="color: #28a745; font-weight: bold;">{status}</span>'
        elif status == "In Progress":
            return f'<span style="color: #ffc107; font-weight: bold;">{status}</span>'
        else:
            return f'<span style="color: #17a2b8; font-weight: bold;">{status}</span>'
    status_display.short_description = "Status"
    status_display.allow_tags = True

    def contribution_count(self, obj):
        """Display contribution count"""
        return obj.get_contribution_count()
    contribution_count.short_description = "Contributions"

    def total_contributed(self, obj):
        """Display total contributed amount"""
        return f"RM {obj.get_total_contributed():,.2f}"
    total_contributed.short_description = "Total Contributed"

    def funding_progress(self, obj):
        """Display funding progress as percentage"""
        progress = obj.get_funding_progress()
        return f"{progress:.1f}%"
    funding_progress.short_description = "Funding Progress"

    def get_queryset(self, request):
        """Show all assets by default, but allow filtering by archive status"""
        qs = super().get_queryset(request)
        return qs

    def get_list_display(self, request):
        """Customize list display based on archive filter"""
        list_display = list(super().get_list_display(request))
        
        # If viewing archived assets, show archive-related fields more prominently
        if request.GET.get('is_archived') == '1':
            # Move archive fields to the front for better visibility
            archive_fields = ['is_archived', 'archived_at', 'archived_by']
            for field in reversed(archive_fields):
                if field in list_display:
                    list_display.remove(field)
                    list_display.insert(0, field)
        
        return list_display

    def get_actions(self, request):
        """Customize actions based on archive status"""
        actions = super().get_actions(request)
        
        # If viewing archived assets, show unarchive and delete actions more prominently
        if request.GET.get('is_archived') == '1':
            # Reorder actions to prioritize archive-related ones
            if 'unarchive_assets' in actions:
                del actions['unarchive_assets']
                actions['unarchive_assets'] = actions.pop('unarchive_assets')
            if 'delete_archived_assets' in actions:
                del actions['delete_archived_assets']
                actions['delete_archived_assets'] = actions.pop('delete_archived_assets')
        
        return actions

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('archived/', self.admin_site.admin_view(self.archived_assets_view), name='waqaf_waqafasset_archived'),
        ]
        return custom_urls + urls

    def archived_assets_view(self, request):
        """Custom admin view for archived assets"""
        archived_assets = WaqafAsset.objects.filter(is_archived=True).order_by('-archived_at')
        
        context = {
            'title': 'Archived Waqaf Assets',
            'assets': archived_assets,
            'opts': self.model._meta,
            'total_archived': archived_assets.count(),
            'total_assets': WaqafAsset.objects.count(),
        }
        
        return TemplateResponse(request, 'admin/waqaf/waqafasset/archived_assets.html', context)

    def calculate_slot_prices(self, request, queryset):
        """Calculate slot prices for selected assets based on target amount and total slots"""
        updated_count = 0
        error_count = 0
        
        for asset in queryset:
            try:
                if asset.target_amount > 0 and asset.total_slots > 0:
                    old_price = asset.slot_price
                    new_price = asset.target_amount / asset.total_slots
                    asset.slot_price = new_price
                    asset.save(update_fields=['slot_price'])
                    updated_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
        
        if updated_count > 0:
            self.message_user(
                request, 
                f'Successfully calculated slot prices for {updated_count} assets. '
                f'({error_count} assets had errors or missing data.)'
            )
        else:
            self.message_user(
                request, 
                'No slot prices were calculated. Please ensure target_amount and total_slots are set.',
                level=messages.WARNING
            )
    
    calculate_slot_prices.short_description = "Calculate slot prices for selected assets"

    def archive_assets(self, request, queryset):
        """Archive selected assets"""
        updated_count = 0
        for asset in queryset:
            if not asset.is_archived:
                asset.archive(user=request.user)
                updated_count += 1
        
        if updated_count > 0:
            self.message_user(
                request, 
                f'Successfully archived {updated_count} assets.'
            )
        else:
            self.message_user(
                request, 
                f'No assets needed archiving.',
                level=messages.WARNING
            )
    
    archive_assets.short_description = "Archive selected assets"

    def unarchive_assets(self, request, queryset):
        """Unarchive selected assets"""
        updated_count = 0
        for asset in queryset:
            if asset.is_archived:
                asset.unarchive()
                updated_count += 1
        
        if updated_count > 0:
            self.message_user(
                request, 
                f'Successfully unarchived {updated_count} assets.'
            )
        else:
            self.message_user(
                request, 
                f'No assets needed unarchiving.',
                level=messages.WARNING
            )
    
    unarchive_assets.short_description = "Unarchive selected assets"

    def delete_archived_assets(self, request, queryset):
        """Delete only archived assets"""
        archived_assets = queryset.filter(is_archived=True)
        if not archived_assets.exists():
            self.message_user(
                request, 
                f'No archived assets selected for deletion.',
                level=messages.WARNING
            )
            return
        
        # Show confirmation page
        if 'apply' in request.POST:
            deleted_count = 0
            for asset in archived_assets:
                try:
                    asset.delete()
                    deleted_count += 1
                except Exception as e:
                    self.message_user(
                        request, 
                        f'Error deleting asset {asset.name}: {str(e)}',
                        level=messages.ERROR
                    )
            
            self.message_user(
                request, 
                f'Successfully deleted {deleted_count} archived assets.'
            )
            return HttpResponseRedirect('../')
        
        # Show confirmation template
        context = {
            'title': 'Delete Archived Assets',
            'assets': archived_assets,
            'opts': self.model._meta,
            'action': 'delete_archived_assets',
        }
        return TemplateResponse(request, 'admin/waqaf/waqafasset/delete_archived_assets.html', context)
    
    delete_archived_assets.short_description = "Delete selected archived assets"

    def bulk_archive_completed(self, request, queryset):
        """Archive assets that are fully funded (all slots filled)"""
        completed_assets = queryset.filter(slots_available=0, is_archived=False)
        archived_count = 0
        
        for asset in completed_assets:
            asset.archive(user=request.user)
            archived_count += 1
        
        if archived_count > 0:
            self.message_user(
                request, 
                f'Successfully archived {archived_count} completed assets.'
            )
        else:
            self.message_user(
                request, 
                f'No completed assets found to archive.',
                level=messages.WARNING
            )
    
    bulk_archive_completed.short_description = "Archive completed assets (fully funded)"

    def bulk_unarchive_all(self, request, queryset):
        """Unarchive all selected assets"""
        archived_assets = queryset.filter(is_archived=True)
        unarchived_count = 0
        
        for asset in archived_assets:
            asset.unarchive()
            unarchived_count += 1
        
        if unarchived_count > 0:
            self.message_user(
                request, 
                f'Successfully unarchived {unarchived_count} assets.'
            )
        else:
            self.message_user(
                request, 
                f'No archived assets found to unarchive.',
                level=messages.WARNING
            )
    
    bulk_unarchive_all.short_description = "Unarchive all selected assets"

    def save_model(self, request, obj, form, change):
        # Set initial slots_available equal to total_slots for new assets
        if not change:  # If this is a new asset
            obj.slots_available = obj.total_slots
        
        # Auto-calculate slot price if target_amount and total_slots are set
        if obj.target_amount > 0 and obj.total_slots > 0:
            obj.slot_price = obj.target_amount / obj.total_slots
        
        super().save_model(request, obj, form, change)


@admin.register(Contributor)
class ContributorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'amount_contributed')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('amount_contributed',)


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('payment_id', 'created_at', 'updated_at')
    fields = ('payment_number', 'amount', 'due_date', 'status', 'payment_method', 'reference_number')
    can_delete = False


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('contributor', 'asset', 'number_of_slots', 'amount', 'payment_status', 'payment_type', 'payments_made', 'total_payments', 'date_contributed')
    list_filter = ('payment_status', 'payment_type', 'payment_schedule', 'date_contributed', 'asset')
    search_fields = ('contributor__name', 'payment_reference')
    readonly_fields = ('amount', 'payments_made', 'next_payment_date')
    date_hierarchy = 'date_contributed'
    inlines = [PaymentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('contributor', 'asset', 'number_of_slots', 'amount')
        }),
        ('Payment Details', {
            'fields': ('payment_type', 'payment_schedule', 'total_payments', 'payments_made', 'next_payment_date')
        }),
        ('Payment Settings', {
            'fields': ('auto_generate_payments', 'payment_status', 'payment_reference')
        }),
        ('Additional Information', {
            'fields': ('dedicated_for', 'date_contributed'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['auto_generate_amounts', 'recalculate_all_amounts', 'generate_payment_schedules', 'mark_as_paid']
    
    def auto_generate_amounts(self, request, queryset):
        """Auto-generate amounts for selected contributions based on slots and asset price"""
        updated_count = 0
        for contribution in queryset:
            if contribution.asset and contribution.number_of_slots:
                old_amount = contribution.amount
                contribution.amount = contribution.number_of_slots * contribution.asset.slot_price
                contribution.save()
                if old_amount != contribution.amount:
                    updated_count += 1
        
        if updated_count > 0:
            self.message_user(request, f'Successfully updated amounts for {updated_count} contributions.')
        else:
            self.message_user(request, 'No amounts needed updating.', level=messages.WARNING)
    
    auto_generate_amounts.short_description = "Auto-generate amounts for selected contributions"
    
    def recalculate_all_amounts(self, request, queryset):
        """Recalculate amounts for all contributions in the system"""
        all_contributions = Contribution.objects.all()
        updated_count = 0
        
        with transaction.atomic():
            for contribution in all_contributions:
                if contribution.asset and contribution.number_of_slots:
                    old_amount = contribution.amount
                    contribution.amount = contribution.number_of_slots * contribution.asset.slot_price
                    contribution.save()
                    if old_amount != contribution.amount:
                        updated_count += 1
        
        if updated_count > 0:
            self.message_user(request, f'Successfully recalculated amounts for {updated_count} contributions.')
        else:
            self.message_user(request, 'All amounts are already correctly calculated.', level=messages.INFO)
    
    recalculate_all_amounts.short_description = "Recalculate all contribution amounts"
    
    def generate_payment_schedules(self, request, queryset):
        """Generate payment schedules for selected recurring contributions"""
        generated_count = 0
        for contribution in queryset:
            if contribution.payment_type == 'RECURRING':
                try:
                    contribution.generate_payment_schedule()
                    generated_count += 1
                except Exception as e:
                    self.message_user(request, f'Error generating payments for {contribution.contributor.name}: {str(e)}', level=messages.ERROR)
        
        if generated_count > 0:
            self.message_user(request, f'Successfully generated payment schedules for {generated_count} contributions.')
        else:
            self.message_user(request, 'No payment schedules needed generation.', level=messages.WARNING)
    
    generate_payment_schedules.short_description = "Generate payment schedules for selected contributions"
    
    def mark_as_paid(self, request, queryset):
        """Mark selected contributions as paid"""
        updated_count = 0
        for contribution in queryset:
            if contribution.payment_status != 'COMPLETED':
                contribution.payment_status = 'COMPLETED'
                contribution.save()
                updated_count += 1
        
        if updated_count > 0:
            self.message_user(request, f'Successfully marked {updated_count} contributions as paid.')
        else:
            self.message_user(request, 'No contributions needed status update.', level=messages.INFO)
    
    mark_as_paid.short_description = "Mark selected contributions as paid"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-generate-amounts/', self.admin_site.admin_view(self.bulk_generate_amounts_view), name='waqaf_contribution_bulk_generate'),
            path('bulk-generate-payments/', self.admin_site.admin_view(self.bulk_generate_payments_view), name='waqaf_contribution_bulk_payments'),
        ]
        return custom_urls + urls
    
    def bulk_generate_amounts_view(self, request):
        """Custom admin view for bulk amount generation"""
        if request.method == 'POST':
            # Get all contributions that need amount calculation
            contributions = Contribution.objects.filter(amount=0).exclude(asset__isnull=True)
            updated_count = 0
            
            with transaction.atomic():
                for contribution in contributions:
                    if contribution.asset and contribution.number_of_slots:
                        contribution.amount = contribution.number_of_slots * contribution.asset.slot_price
                        contribution.save()
                        updated_count += 1
            
            self.message_user(request, f'Successfully generated amounts for {updated_count} contributions.')
            return HttpResponseRedirect('../')
        
        # Get statistics
        total_contributions = Contribution.objects.count()
        contributions_without_amount = Contribution.objects.filter(amount=0).count()
        contributions_with_amount = total_contributions - contributions_without_amount
        
        context = {
            'title': 'Bulk Generate Contribution Amounts',
            'total_contributions': total_contributions,
            'contributions_without_amount': contributions_without_amount,
            'contributions_with_amount': contributions_with_amount,
            'opts': self.model._meta,
        }
        
        return TemplateResponse(request, 'admin/waqaf/contribution/bulk_generate_amounts.html', context)
    
    def bulk_generate_payments_view(self, request):
        """Custom admin view for bulk payment generation"""
        if request.method == 'POST':
            # Get all recurring contributions that need payment schedules
            contributions = Contribution.objects.filter(
                payment_type='RECURRING',
                auto_generate_payments=True
            ).exclude(payments__isnull=False)
            generated_count = 0
            
            with transaction.atomic():
                for contribution in contributions:
                    try:
                        contribution.generate_payment_schedule()
                        generated_count += 1
                    except Exception as e:
                        self.message_user(request, f'Error generating payments for {contribution.contributor.name}: {str(e)}', level=messages.ERROR)
            
            self.message_user(request, f'Successfully generated payment schedules for {generated_count} contributions.')
            return HttpResponseRedirect('../')
        
        # Get statistics
        total_recurring = Contribution.objects.filter(payment_type='RECURRING').count()
        with_payment_schedules = Contribution.objects.filter(payment_type='RECURRING', payments__isnull=False).distinct().count()
        without_payment_schedules = total_recurring - with_payment_schedules
        
        context = {
            'title': 'Bulk Generate Payment Schedules',
            'total_recurring': total_recurring,
            'with_payment_schedules': with_payment_schedules,
            'without_payment_schedules': without_payment_schedules,
            'opts': self.model._meta,
        }
        
        return TemplateResponse(request, 'admin/waqaf/contribution/bulk_generate_payments.html', context)
    
    class Media:
        js = ('admin/js/waqaf_contribution_auto_calculate.js',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'contribution', 'payment_number', 'amount', 'due_date', 'status', 'payment_method', 'is_overdue_display')
    list_filter = ('status', 'payment_method', 'due_date', 'contribution__payment_type')
    search_fields = ('payment_id', 'contribution__contributor__name', 'reference_number')
    readonly_fields = ('payment_id', 'created_at', 'updated_at', 'is_overdue_display')
    date_hierarchy = 'due_date'
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_id', 'contribution', 'payment_number', 'amount')
        }),
        ('Payment Details', {
            'fields': ('due_date', 'payment_date', 'status', 'payment_method')
        }),
        ('Additional Information', {
            'fields': ('reference_number', 'notes', 'created_at', 'updated_at')
        }),
    )
    
    actions = ['mark_as_paid', 'mark_as_failed', 'mark_as_cancelled']
    
    def is_overdue_display(self, obj):
        if obj.is_overdue():
            days_overdue = obj.get_days_overdue()
            return f"Overdue ({days_overdue} days)"
        return "On time"
    is_overdue_display.short_description = "Overdue Status"
    
    def mark_as_paid(self, request, queryset):
        """Mark selected payments as paid"""
        updated_count = 0
        for payment in queryset:
            if payment.status != 'COMPLETED':
                payment.mark_as_paid()
                updated_count += 1
        
        if updated_count > 0:
            self.message_user(request, f'Successfully marked {updated_count} payments as paid.')
        else:
            self.message_user(request, 'No payments needed status update.', level=messages.INFO)
    
    mark_as_paid.short_description = "Mark selected payments as paid"
    
    def mark_as_failed(self, request, queryset):
        """Mark selected payments as failed"""
        updated_count = queryset.update(status='FAILED')
        if updated_count > 0:
            self.message_user(request, f'Successfully marked {updated_count} payments as failed.')
        else:
            self.message_user(request, 'No payments needed status update.', level=messages.INFO)
    
    mark_as_failed.short_description = "Mark selected payments as failed"
    
    def mark_as_cancelled(self, request, queryset):
        """Mark selected payments as cancelled"""
        updated_count = queryset.update(status='CANCELLED')
        if updated_count > 0:
            self.message_user(request, f'Successfully marked {updated_count} payments as cancelled.')
        else:
            self.message_user(request, 'No payments needed status update.', level=messages.INFO)
    
    mark_as_cancelled.short_description = "Mark selected payments as cancelled"


@admin.register(FundDistribution)
class FundDistributionAdmin(admin.ModelAdmin):
    list_display = ('asset', 'purpose', 'amount', 'date_distributed')
    list_filter = ('date_distributed', 'purpose')
    search_fields = ('asset__name',)
    date_hierarchy = 'date_distributed'