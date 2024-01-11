# third party
import django_filters

# project
from centers.models import Company

# local
from .models import ExtensionLine


class ExtensionFilter(django_filters.FilterSet):

    search = django_filters.CharFilter(
        field_name='extension', lookup_expr='icontains')

    company = django_filters.ModelChoiceFilter(
        queryset=Company.objects.all(), to_field_name='slug')

    class Meta:
        model = ExtensionLine
        fields = [
            'search', 'company', 'center', 'sector']
