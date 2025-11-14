#!/usr/bin/env python
"""
Test search functionality
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donation.settings')
django.setup()

from myapp.models import Student, Payment
from django.db.models import Q

def test_search():
    print("=== Testing Search Functionality ===")
    
    # Get Form 3 students
    form3_students = Student.objects.filter(
        level='form',
        level_custom__iexact='Form 3',
        is_active=True
    )
    print(f"Form 3 students: {form3_students.count()}")
    
    # Get Form 3 payments
    payments = Payment.objects.filter(student__in=form3_students)
    print(f"Total Form 3 payments: {payments.count()}")
    
    # Test search for "Omar"
    search_query = "Omar"
    filtered_payments = payments.filter(
        Q(student__first_name__icontains=search_query) |
        Q(student__last_name__icontains=search_query) |
        Q(student__student_id__icontains=search_query) |
        Q(payment_id__icontains=search_query)
    )
    print(f"\nSearch for '{search_query}': {filtered_payments.count()} results")
    for p in filtered_payments[:3]:
        print(f"  - {p.student.first_name} {p.student.last_name} (Payment ID: {p.id})")
    
    # Test search for "Tamim"
    search_query = "Tamim"
    filtered_payments = payments.filter(
        Q(student__first_name__icontains=search_query) |
        Q(student__last_name__icontains=search_query) |
        Q(student__student_id__icontains=search_query) |
        Q(payment_id__icontains=search_query)
    )
    print(f"\nSearch for '{search_query}': {filtered_payments.count()} results")
    for p in filtered_payments[:3]:
        print(f"  - {p.student.first_name} {p.student.last_name} (Payment ID: {p.id})")

if __name__ == '__main__':
    test_search()
