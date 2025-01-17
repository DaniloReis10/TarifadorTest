from django import template
from charges.constants import BASIC_SERVICE_CHOICES

register = template.Library()
basic_service_map = dict(BASIC_SERVICE_CHOICES)

@register.filter(name='servicename')
def servicename(value):
        return basic_service_map[value]

