from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, InvalidOperation):
        return 0 