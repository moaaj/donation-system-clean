from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.donate, name='donate'),
    path('thank-you/', views.thank_you, name='thank_you'),
    path('report/', views.donation_report, name='donation_report'),
    path('analytics/', views.donation_analytics, name='donation_analytics'),
    path('api/analytics/', views.donation_analytics_api, name='donation_analytics_api'),
    path('receipt-old/<int:donation_id>/', views.donation_receipt, name='donation_receipt'),
    path('chat/', views.chat_message, name='chat_message'),
    path('api/chat/', views.chat_message, name='api_chat_message'),
    path('events/', views.donation_events, name='donation_events'),
    path('events/<int:event_id>/', views.donation_event_detail, name='donation_event_detail'),
    path('events/add/', views.add_donation_event, name='add_donation_event'),
    path('events/<int:event_id>/edit/', views.edit_donation_event, name='edit_donation_event'),
    path('events/<int:event_id>/delete/', views.delete_donation_event, name='delete_donation_event'),
    path('categories/', views.donation_categories, name='donation_categories'),
    path('categories/add/', views.add_donation_category, name='add_donation_category'),
    path('categories/<int:category_id>/edit/', views.edit_donation_category, name='edit_donation_category'),
    path('categories/<int:category_id>/delete/', views.delete_donation_category, name='delete_donation_category'),
    path('events/<int:event_id>/generate-messages/', views.generate_donor_engagement_messages, name='generate_donor_messages'),
    path('donor/messages/', views.get_donor_messages, name='get_donor_messages'),
    
    # Cart functionality
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:event_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('cart/checkout/', views.checkout_cart, name='checkout_cart'),
    path('cart/success/<str:donation_ids>/', views.donation_success, name='donation_success'),
    path('api/cart/count/', views.get_cart_count, name='get_cart_count'),
    
    # Donation History and Receipts
    path('history/', views.donation_history, name='donation_history'),
    path('receipt/<int:donation_id>/', views.donation_receipt_detail, name='donation_receipt_detail'),
    path('receipt/<int:donation_id>/download/', views.download_receipt_pdf, name='download_receipt_pdf'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
