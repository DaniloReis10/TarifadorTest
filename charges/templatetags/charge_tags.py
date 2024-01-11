# django
from django import template

register = template.Library()


@register.simple_tag(name='company_count')
def company_count(company_set, user, organization):
    if user.is_superuser or organization.is_admin(user):
        return company_set.count()
    return company_set.filter(id__in=user.company_set.only('id')).count()
