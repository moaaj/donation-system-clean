from django.urls import path, include
from . import views
from .waqaf_admin import waqaf_admin_site

app_name = 'waqaf'  # Add namespace for the app

urlpatterns = [
    path('dashboard/', views.waqaf_dashboard, name='waqaf_dashboard'),
    path('', views.waqaf, name='waqaf'),
    path('contribute_waqaf/', views.contribute_waqaf, name='contribute_waqaf'),
    path('asset/<int:asset_id>/', views.asset_detail, name='asset_detail'),
    path('certificate/<int:contribution_id>/', views.download_certificate, name='download_certificate'),
    path('ai-analytics/', views.waqaf_ai_analytics, name='waqaf_ai_analytics'),
    path('add-asset/', views.add_waqaf_asset, name='add_waqaf_asset'),
    path('delete-asset/<int:asset_id>/', views.delete_waqaf_asset, name='delete_waqaf_asset'),
    path('archive-asset/<int:asset_id>/', views.archive_asset, name='archive_asset'),
    path('unarchive-asset/<int:asset_id>/', views.unarchive_asset, name='unarchive_asset'),
    path('archived-assets/', views.view_archived_assets, name='view_archived_assets'),
    
    # Cart URLs
    path('cart/', views.view_waqaf_cart, name='view_waqaf_cart'),
    path('cart/add/<int:asset_id>/', views.add_to_waqaf_cart, name='add_to_waqaf_cart'),
    path('cart/update/<int:item_id>/', views.update_waqaf_cart_item, name='update_waqaf_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_waqaf_cart, name='remove_from_waqaf_cart'),
    path('cart/clear/', views.clear_waqaf_cart, name='clear_waqaf_cart'),
    path('cart/checkout/', views.checkout_waqaf_cart, name='checkout_waqaf_cart'),
    path('cart/success/', views.waqaf_success, name='waqaf_success'),
    path('cart/count/', views.get_waqaf_cart_count, name='get_waqaf_cart_count'),
    
    # Waqaf Admin URLs
    path('admin/', waqaf_admin_site.urls),
]
