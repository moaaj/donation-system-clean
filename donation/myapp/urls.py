from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import PaymentViewSet
from django.utils import timezone

router = DefaultRouter()
router.register(r'payments', PaymentViewSet)

urlpatterns = [
    # Main URLs (login required)
    path('', views.school_fees, name='school_fees'),
    path('dashboard/', views.school_fees_dashboard, name='school_fees_dashboard'),
    path('home/', views.home, name='home'),
    
    # API URLs
    path('api/', include(router.urls)),
    
    # Student URLs
    path('students/', views.student_list, name='student_list'),
    path('students/<int:id>/', views.student_detail, name='student_detail'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/<int:id>/edit/', views.edit_student, name='edit_student'),
    path('students/bulk-upload/', views.bulk_upload_students, name='bulk_upload_students'),
    path('students/download-template/', views.download_student_template, name='download_student_template'),
    
    # Fee Structure URLs
    path('fee-structure/', views.fee_structure_list, name='fee_structure_list'),
    path('fee-structure/add/', views.add_fee_structure, name='add_fee_structure'),
    path('fee-structure/<int:structure_id>/edit/', views.edit_fee_structure, name='edit_fee_structure'),
    path('fee-structure/<int:structure_id>/delete/', views.delete_fee_structure, name='delete_fee_structure'),
    
    # Payment URLs
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/add/', views.add_payment, name='add_payment'),
    path('payments/<int:pk>/edit/', views.edit_payment, name='edit_payment'),
    path('payments/<int:pk>/delete/', views.delete_payment, name='delete_payment'),
    path('payments/receipt/<int:payment_id>/', views.payment_receipt, name='payment_receipt'),
    path('payments/email-receipt/<int:payment_id>/', views.email_receipt, name='email_receipt'),
    path('payments/receipts/', views.payment_receipts, name='payment_receipts'),
    path('payments/print-receipts/<int:payment_id>/', views.print_receipts, name='print_receipts'),
    
    # Fee Category URLs
    path('categories/', views.fee_categories, name='fee_categories'),
    path('categories/add/', views.add_fee_category, name='add_fee_category'),
    path('categories/<int:category_id>/edit/', views.edit_fee_category, name='edit_fee_category'),
    path('categories/<int:category_id>/delete/', views.delete_fee_category, name='delete_fee_category'),
    
    # Pending Fees URLs
    path('pending-fees/', views.pending_fees, name='pending_fees'),
    path('pending-fees/add/', views.add_fee_status, name='add_fee_status'),
    path('pending-fees/<int:fee_status_id>/update/', views.update_fee_status, name='update_fee_status'),
    
    # Fee Waiver URLs
    path('waivers/', views.fee_waivers, name='fee_waivers'),
    path('waivers/add/', views.add_fee_waiver, name='add_fee_waiver'),
    path('waivers/<int:waiver_id>/approve/', views.approve_fee_waiver, name='approve_fee_waiver'),
    path('waivers/<int:waiver_id>/reject/', views.reject_fee_waiver, name='reject_fee_waiver'),
    path('waivers/<int:waiver_id>/letter/', views.view_fee_waiver_letter, name='view_fee_waiver_letter'),
    
    # Report URLs
    path('reports/', views.fee_reports, name='fee_reports'),
    path('reports/export/', views.export_fee_report, name='export_fee_report'),
    
    # AI Analytics URLs
    path('ai-analytics/', views.ai_fee_analytics, name='ai_fee_analytics'),
    path('ai/donation-prediction/', views.donation_prediction, name='donation_prediction'),
    path('ai/donor-insights/', views.donor_insights, name='donor_insights'),
    path('ai/settings/', views.ai_settings, name='ai_settings'),
    
    # Other URLs
    path('fpx/payment/', views.fpx_payment_request, name='fpx_payment_request'),
    path('discounts/add/', views.add_discount, name='add_discount'),
    path('bank-accounts/', views.bank_accounts, name='bank_accounts'),
    path('bank-accounts/add/', views.add_bank_account, name='add_bank_account'),
    path('reminders/', views.payment_reminders, name='payment_reminders'),
    path('reminders/<int:payment_id>/send/', views.send_payment_reminder, name='send_payment_reminder'),
    path('reminders/<int:payment_id>/letter/', views.generate_reminder_letter, name='generate_reminder_letter'),
    path('email-preferences/', views.email_preferences, name='email_preferences'),
    path('fee-settings/', views.fee_settings, name='fee_settings'),
    
    # Chatbot URLs
    path('chatbot/', views.chatbot_interface, name='chatbot_interface'),
    path('api/chatbot/query/', views.chatbot_query, name='chatbot_query'),
    path('donation/success/<int:donation_id>/', views.donation_success, name='donation_success'),
    path('donation/receipt/<int:donation_id>/', views.donation_receipt, name='donation_receipt'),
]
