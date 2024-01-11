# django
from django import template

# project
from core.constants import STATUS_CHOICES
from extensions.constants import SOLICITATION_STATUS_CHOICES

register = template.Library()

SOLICITATION_STATUS_MAP = dict(SOLICITATION_STATUS_CHOICES)
PRICETABLE_STATUS_MAP = dict(STATUS_CHOICES)


@register.filter(name='statussolicitation')
def statussolicitation(value):
    return SOLICITATION_STATUS_MAP[value]


@register.filter(name='statuspricetable')
def statuspricetable(value):
    return PRICETABLE_STATUS_MAP[value]


@register.filter(name='organization_count')
def organization_count(value):
    return value.organizationsetting_set.all().count()


@register.filter(name='is_empty')
def is_empty(value):
    if value:
        return value
    else:
        return '-'
