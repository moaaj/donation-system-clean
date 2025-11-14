"""
Form 1 Admin URL Patterns - STRICT DATA ISOLATION
"""

from django.urls import path
from . import views_form1_admin

app_name = 'form1_admin'

urlpatterns = [
    # Form 1 Admin Dashboard
    path('', views_form1_admin.form1_admin_dashboard, name='dashboard'),
    
    # Form 1 Student Management
    path('students/', views_form1_admin.form1_student_list, name='student_list'),
    path('students/<int:id>/', views_form1_admin.form1_student_detail, name='student_detail'),
    
    # Form 1 Fee Management
    path('fees/', views_form1_admin.form1_fee_management, name='fee_management'),
    path('fees/add-individual/', views_form1_admin.form1_add_individual_fee, name='add_individual_fee'),
    path('fees/add-structure/', views_form1_admin.form1_add_fee_structure, name='add_fee_structure'),
    path('fees/edit-structure/<int:structure_id>/', views_form1_admin.form1_edit_fee_structure, name='edit_fee_structure'),
    
    # Form 1 Payment Management
    path('payments/', views_form1_admin.form1_payment_management, name='payment_management'),
    path('payments/receipts/', views_form1_admin.form1_payment_receipts, name='payment_receipts'),
    path('payments/receipt/<int:payment_id>/', views_form1_admin.form1_payment_receipt, name='payment_receipt'),
    
    # Form 1 Analytics
    path('analytics/', views_form1_admin.form1_analytics, name='analytics'),
]
