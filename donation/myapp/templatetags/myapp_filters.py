from django import template

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
