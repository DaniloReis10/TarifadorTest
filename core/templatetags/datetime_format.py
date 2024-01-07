from django.template import Library

from core.utils import time_format

register = Library()


@register.filter
def timeformat(seconds):
    return time_format(seconds) if seconds else '00:00:00'
