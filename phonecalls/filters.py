# django
from django.db.models import Q
from django.db.models.functions import Reverse
from django.db.models.functions import Substr
from django.db.models.functions import Trim

# third party
import django_filters
import phonenumbers

from phonenumbers.phonenumberutil import NumberParseException

# project
from centers.models import Company
from extensions.utils import make_extension_list
from organizations.models import Organization

# local
from .constants import ALL
from .constants import BOUND_CHOICES
from .constants import DDD_CHOICES
from .constants import INBOUND
from .constants import OUTBOUND
from .constants import OUTBOUND_CHARGED
from .constants import LOCAL, VC1, VC2, VC3, LDN, LDI
from .models import Phonecall


class PhonecallFilter(django_filters.FilterSet):

    organization = django_filters.ModelChoiceFilter(
        queryset=Organization.objects.all(), to_field_name='slug')

    company = django_filters.ModelChoiceFilter(
        queryset=Company.objects.all(), to_field_name='slug')

    unknown = django_filters.BooleanFilter(
        field_name='extension', lookup_expr='isnull')

    unidentified = django_filters.BooleanFilter(
        field_name='company', lookup_expr='isnull')

    date_gt = django_filters.DateFilter(
        field_name='startdate', lookup_expr='gte')

    date_lt = django_filters.DateFilter(
        field_name='startdate', lookup_expr='lte')

    bound = django_filters.ChoiceFilter(
        choices=BOUND_CHOICES, method='bound_filter')

    ddd = django_filters.ChoiceFilter(
        choices=DDD_CHOICES, method='ddd_filter')

    extension = django_filters.CharFilter(
        method='extension_filter')

    search = django_filters.CharFilter(
        method='search_filter')

    class Meta:
        model = Phonecall
        fields = [
            'calltype',
            'organization',
            'company',
            'center',
            'sector',
            'chargednumber',
            'date_gt',
            'date_lt',
            'dialednumber',
            'extension',
            'bound',
            'internal',
            'pabx',
            'service',
            'unknown']

    def bound_filter(self, queryset, name, value):
        if value == OUTBOUND:
            return queryset.filter(inbound=False)
        elif value == OUTBOUND_CHARGED:
            return queryset.filter(inbound=False, calltype__in=[LOCAL, VC1, VC2, VC3, LDN, LDI])
        elif value == INBOUND:
            return queryset.filter(inbound=True)
        return queryset

    def ddd_filter(self, queryset, name, value):
        return queryset \
            .annotate(cnumber=Reverse(Substr(Reverse(Trim('chargednumber')), 10, 2)),
                      dnumber=Reverse(Substr(Reverse(Trim('dialednumber')), 10, 2)),
                      extnumber=Substr('extension__extension', 1, 2)) \
            .filter(Q(extnumber=value) | Q(cnumber=value) | Q(dnumber=value))

    def extension_filter(self, queryset, name, value):
        extension_list = make_extension_list(value)
        return queryset.filter(extension__extension__in=extension_list)

    def search_filter(self, queryset, name, value):
        try:
            value = phonenumbers.parse(value, 'BR').national_number
        except NumberParseException:
            pass

        return queryset \
            .annotate(cnumber=Trim('chargednumber'), dnumber=Trim('dialednumber')) \
            .filter(Q(extension__extension__icontains=value) |
                    Q(cnumber__icontains=value) |
                    Q(dnumber__icontains=value))
