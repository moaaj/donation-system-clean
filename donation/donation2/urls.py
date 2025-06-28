from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.donate, name='donate'),
    path('thank-you/', views.thank_you, name='thank_you'),
    path('report/', views.donation_report, name='donation_report'),
    path('receipt/<int:donation_id>/', views.donation_receipt, name='donation_receipt'),
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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
