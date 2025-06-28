from django.contrib import admin
from .models import WaqafAsset, Contributor, FundDistribution, Contribution



@admin.register(WaqafAsset)
class WaqafAssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_slots', 'slots_available', 'slot_price', 'current_value')
    search_fields = ('name', 'description')
    list_filter = ('total_slots', 'slots_available')
    readonly_fields = ('slots_available',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Financial Details', {
            'fields': ('current_value', 'total_slots', 'slot_price')
        }),
    )

    def save_model(self, request, obj, form, change):
        # Set initial slots_available equal to total_slots for new assets
        if not change:  # If this is a new asset
            obj.slots_available = obj.total_slots
        super().save_model(request, obj, form, change)

@admin.register(Contributor)
class ContributorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'amount_contributed')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('amount_contributed',)

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('contributor', 'asset', 'number_of_slots', 'amount', 'payment_status', 'date_contributed')
    list_filter = ('payment_status', 'date_contributed', 'asset')
    search_fields = ('contributor__name', 'payment_reference')
    readonly_fields = ('amount',)
    date_hierarchy = 'date_contributed'

@admin.register(FundDistribution)
class FundDistributionAdmin(admin.ModelAdmin):
    list_display = ('asset', 'purpose', 'amount', 'date_distributed')
    list_filter = ('date_distributed', 'purpose')
    search_fields = ('asset__name',)
    date_hierarchy = 'date_distributed'