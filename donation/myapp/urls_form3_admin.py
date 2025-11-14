"""
Form 3 Admin URL patterns
"""

from django.urls import path
from . import views_form3_admin

app_name = 'form3_admin'

urlpatterns = [
    # Form 3 Admin Dashboard
    path('', views_form3_admin.form3_admin_dashboard, name='dashboard'),
    
    # Form 3 Student Management
    path('students/', views_form3_admin.form3_student_list, name='student_list'),
    path('students/<int:id>/', views_form3_admin.form3_student_detail, name='student_detail'),
    
    # Form 3 Fee Management
    path('fees/', views_form3_admin.form3_fee_management, name='fee_management'),
    path('fees/add-individual/', views_form3_admin.form3_add_individual_fee, name='add_individual_fee'),
    path('fees/add-structure/', views_form3_admin.form3_add_fee_structure, name='add_fee_structure'),
    path('fees/edit-structure/<int:structure_id>/', views_form3_admin.form3_edit_fee_structure, name='edit_fee_structure'),
    
    # Form 3 Fee Categories
    path('categories/', views_form3_admin.form3_fee_categories, name='fee_categories'),
    path('categories/add/', views_form3_admin.form3_add_fee_category, name='add_fee_category'),
    path('categories/<int:category_id>/edit/', views_form3_admin.form3_edit_fee_category, name='edit_fee_category'),
    
    # Form 3 Pending Fees
    path('pending-fees/', views_form3_admin.form3_pending_fees, name='pending_fees'),
    path('pending-fees/add/', views_form3_admin.form3_add_fee_status, name='add_fee_status'),
    
    # Form 3 Fee Waivers
    path('waivers/', views_form3_admin.form3_fee_waivers, name='fee_waivers'),
    path('waivers/add/', views_form3_admin.form3_add_fee_waiver, name='add_fee_waiver'),
    
    # Form 3 Payment Management
    path('payments/', views_form3_admin.form3_payment_management, name='payment_management'),
    path('payments/receipts/', views_form3_admin.form3_payment_receipts, name='payment_receipts'),
    path('payments/receipt/<int:payment_id>/', views_form3_admin.form3_payment_receipt, name='payment_receipt'),
    
    # Form 3 Bank Accounts
    path('bank-accounts/', views_form3_admin.form3_bank_accounts, name='bank_accounts'),
    path('bank-accounts/add/', views_form3_admin.form3_add_bank_account, name='add_bank_account'),
    
    # Form 3 Reports
    path('reports/', views_form3_admin.form3_fee_reports, name='fee_reports'),
    path('reports/export/', views_form3_admin.form3_export_fee_report, name='export_fee_report'),
    
    # Form 3 Analytics
    path('analytics/', views_form3_admin.form3_analytics, name='analytics'),
]
