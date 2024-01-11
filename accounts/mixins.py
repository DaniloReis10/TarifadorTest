# python
import urllib

from datetime import date

# django
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404

# third party
from organizations.models import Organization

# project
from centers.utils import get_center_choices
from centers.utils import get_company_choices
from centers.utils import get_sector_choices
from core.utils import get_range_date
from phonecalls.constants import CALLTYPE_CHOICES
from phonecalls.constants import DDD_CHOICES
from phonecalls.constants import PABX_CHOICES
from phonecalls.constants import SERVICE_CHOICES


class OrganizationMixin(LoginRequiredMixin):

    def dispatch(self, request, *args, **kwargs):
        self.organization = get_object_or_404(Organization, slug=kwargs.get('org_slug'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs.update({'organization': self.organization})
        return super().get_context_data(**kwargs)

    def get_organization(self):
        return self.organization


class OrganizationContextMixin(object):

    def dispatch(self, request, *args, **kwargs):
        self.params = {key: value for key, value in self.request.GET.items() if key != 'page' and value}
        self.date_gt, self.date_lt = get_range_date(self.request.GET)
        if self.date_gt is None or self.date_lt is None:
            self.date_lt = date.today()
            self.date_gt = date(self.date_lt.year, self.date_lt.month, 1)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        proportionality = self.params.get('proportionality')
        company = self.organization.company_set.filter(slug=self.params.get('company')).first()
        center = self.organization.center_set.filter(id=self.params.get('center')).first()
        sector = self.organization.sector_set.filter(id=self.params.get('sector')).first()

        if center:
            company = center.company
        if sector:
            company = sector.company
            center = sector.center

        kwargs.update({
            'urlencode': urllib.parse.urlencode(self.params),
            'date_gt': self.date_gt.strftime('%Y-%m-%d'),
            'date_lt': self.date_lt.strftime('%Y-%m-%d'),
            'proportionality': proportionality == "true",
            'calltype_choices': CALLTYPE_CHOICES,
            'service_choices': SERVICE_CHOICES,
            'pabx_choices': PABX_CHOICES,
            'ddd_choices': DDD_CHOICES,
            'company_choices': get_company_choices(self.organization),
            'center_choices': get_center_choices(company),
            'sector_choices': get_sector_choices(center)})
        return super().get_context_data(**kwargs)
