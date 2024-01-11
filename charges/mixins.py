# third party
from organizations.views.mixins import MembershipRequiredMixin

# project
from accounts.mixins import OrganizationMixin

# local
from . import constants


class CallPriceTableMixin(OrganizationMixin, MembershipRequiredMixin):

    def get_queryset(self):
        queryset = super().get_queryset() \
            .filter(organization=self.organization, servicetype=constants.COMMUNICATION_SERVICE)
        user = self.request.user
        if user.is_superuser or self.organization.is_admin(user):
            return queryset
        return queryset.filter(call_company_set__in=user.company_set.only('id'))


class ServicePriceTableMixin(OrganizationMixin, MembershipRequiredMixin):

    def get_queryset(self):
        queryset = super().get_queryset() \
            .filter(organization=self.organization, servicetype=constants.BASIC_SERVICE)
        user = self.request.user
        if user.is_superuser or self.organization.is_admin(user):
            return queryset
        return queryset.filter(service_company_set__in=user.company_set.only('id'))
