# third party
import django_filters

# local
from .models import Company
from .models import CompanyUser
from .models import Sector


class CompanyFilter(django_filters.FilterSet):

    search = django_filters.CharFilter(
        field_name='name', lookup_expr='icontains')

    class Meta:
        model = Company
        fields = [
            'search']


class CompanyUserFilter(django_filters.FilterSet):

    search = django_filters.CharFilter(
        field_name='user__username', lookup_expr='icontains')

    created_gt = django_filters.DateFilter(
        field_name='user__profile__created', lookup_expr='gte')

    created_lt = django_filters.DateFilter(
        field_name='user__profile__created', lookup_expr='lte')

    class Meta:
        model = CompanyUser
        fields = [
            'search',
            'created_gt',
            'created_lt']


class SectorFilter(django_filters.FilterSet):

    class Meta:
        model = Sector
        fields = [
            'center']
