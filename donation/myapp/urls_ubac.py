from django.urls import path
from . import views_ubac

app_name = 'myapp'

urlpatterns = [
    # ============================================================================
    # ADMIN-ONLY URLS
    # ============================================================================
    path('admin/dashboard/', views_ubac.admin_dashboard, name='admin_dashboard'),
    path('admin/students/', views_ubac.student_management, name='student_management'),
    path('admin/fee-structures/', views_ubac.fee_structure_management, name='fee_structure_management'),
    path('admin/payment-reports/', views_ubac.payment_reports, name='payment_reports'),
    
    # ============================================================================
    # STUDENT-ONLY URLS
    # ============================================================================
    path('student/dashboard/', views_ubac.student_dashboard, name='student_dashboard'),
    path('student/payments/', views_ubac.student_payment_history, name='student_payment_history'),
    path('student/make-payment/', views_ubac.make_payment, name='make_payment'),
    path('student/add-to-cart/', views_ubac.add_to_cart, name='add_to_cart'),
    path('student/view-cart/', views_ubac.view_cart, name='view_cart'),
    path('student/remove-from-cart/', views_ubac.remove_from_cart, name='remove_from_cart'),
    path('student/checkout-cart/', views_ubac.checkout_cart, name='checkout_cart'),
    
    # ============================================================================
    # ROLE-BASED URLS (Multiple roles can access)
    # ============================================================================
    path('payment/<int:payment_id>/', views_ubac.payment_detail, name='payment_detail'),
    path('student/<int:student_id>/', views_ubac.student_detail, name='student_detail'),
    
    # ============================================================================
    # MODULE-BASED URLS (Different content for different roles)
    # ============================================================================
    path('school-fees/', views_ubac.school_fees_home, name='school_fees_home'),
    path('donations/', views_ubac.donation_home, name='donation_home'),
    
    # ============================================================================
    # UTILITY URLS
    # ============================================================================
    path('profile/', views_ubac.profile_view, name='profile'),
    path('access-denied/', views_ubac.access_denied, name='access_denied'),
] 