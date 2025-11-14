from django import template
from datetime import date

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key"""
    return dictionary.get(key)

@register.filter
def get_fee_status(fee_statuses, fee_id):
    """Get the status of a specific fee from a list of fee statuses"""
    for status in fee_statuses:
        if status.fee_structure_id == fee_id:
            return status.status
    return 'pending'

@register.filter
def days_since(due_date):
    """Calculate days since a date (for overdue payments)"""
    if not due_date:
        return 0
    today = date.today()
    delta = today - due_date
    return delta.days

@register.filter
def days_until(due_date):
    """Calculate days until a date (for upcoming payments)"""
    if not due_date:
        return 0
    today = date.today()
    delta = due_date - today
    return delta.days

@register.filter
def sum_amount(payments):
    """Calculate the sum of payment amounts"""
    try:
        total = sum(float(payment.amount) for payment in payments)
        return total
    except (AttributeError, TypeError, ValueError):
        return 0
