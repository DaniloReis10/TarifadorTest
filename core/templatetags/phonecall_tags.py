from django.template import Library

from phonecalls.constants import CALLTYPE_CHOICES
from phonecalls.constants import PABX_CHOICES
from phonecalls.constants import SERVICE_CHOICES

register = Library()

CALLTYPE_MAP = dict(CALLTYPE_CHOICES)
PABX_MAP = dict(PABX_CHOICES)
SERVICE_MAP = dict(SERVICE_CHOICES)


@register.filter
def calltype_display(calltype):
    return CALLTYPE_MAP[calltype]


@register.filter
def pabx_display(pabx):
    return PABX_MAP[pabx] if pabx else ''


@register.filter
def service_display(service):
    return SERVICE_MAP[service] if service else ''


@register.filter
def multiple(value, amount):
    return value * amount
