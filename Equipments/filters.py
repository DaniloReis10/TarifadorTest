# third party
import django_filters

# project

from organizations.models import Organization
from .models import ContractBasicServices, typeofphone

class ContractFilter(django_filters.FilterSet):

#    organization = django_filters.ModelChoiceFilter(
#        queryset=Organization.objects.all(), to_field_name='slug')

    class Meta:
        model = ContractBasicServices
        fields = [
            'contractID']

