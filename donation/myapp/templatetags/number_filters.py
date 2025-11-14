from django import template
from django.utils.html import format_html

register = template.Library()

@register.filter
def format_currency(value):
    """Format a number as currency with proper thousands separators"""
    try:
        if value is None:
            return "RM 0.00"
        
        # Convert to float and format with 2 decimal places
        num = float(value)
        
        # Format with thousands separators
        formatted = "{:,.2f}".format(num)
        
        return f"RM {formatted}"
    except (ValueError, TypeError):
        return "RM 0.00"

@register.filter
def format_number(value):
    """Format a number with proper thousands separators"""
    try:
        if value is None:
            return "0"
        
        # Convert to int for whole numbers
        num = int(value)
        
        # Format with thousands separators
        formatted = "{:,}".format(num)
        
        return formatted
    except (ValueError, TypeError):
        return "0"

@register.filter
def format_large_number(value):
    """Format large numbers with K, M, B suffixes"""
    try:
        if value is None:
            return "0"
        
        num = float(value)
        
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.1f}B"
        elif num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        else:
            return f"{num:.0f}"
    except (ValueError, TypeError):
        return "0"
