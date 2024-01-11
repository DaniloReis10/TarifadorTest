# django
from django.db.models import Q

# third party
import django_filters

# project
from centers.models import Company
from phonecalls.models import PriceTable


class PriceTableFilter(django_filters.FilterSet):

    search = django_filters.CharFilter(
        field_name='name', lookup_expr='icontains')

    company = django_filters.ModelChoiceFilter(
        queryset=Company.objects.all(), to_field_name='slug', method='company_filter')

    class Meta:
        model = PriceTable
        fields = [
            'organization',
            'search',
            'status']

    def company_filter(self, queryset, name, value):
        if value:
            return queryset.filter(Q(service_company_set=value) | Q(call_company_set=value))
        return queryset
