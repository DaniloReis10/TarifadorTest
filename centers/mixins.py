# python
import urllib

from datetime import date

# django
from django.http import Http404
from django.shortcuts import get_object_or_404

# third party
from organizations.views.mixins import MembershipRequiredMixin

# project
from accounts.mixins import OrganizationMixin
from core.utils import get_range_date
from phonecalls.constants import CALLTYPE_CHOICES
from phonecalls.constants import DDD_CHOICES
from phonecalls.constants import PABX_CHOICES
from phonecalls.constants import SERVICE_CHOICES

# local
from .models import Company
from .utils import get_center_choices
from .utils import get_sector_choices


class CompanyMixin(OrganizationMixin, MembershipRequiredMixin):

    def dispatch(self, request, company_slug, *args, **kwargs):
        self.company = get_object_or_404(Company, slug=company_slug)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs.update({'company': self.company})
        return super().get_context_data(**kwargs)


class CompanyContextMixin(object):

    def dispatch(self, request, *args, **kwargs):
        self.params = {key: value for key, value in self.request.GET.items() if key != 'page' and value}
        self.date_gt, self.date_lt = get_range_date(self.request.GET)
        if self.date_gt is None or self.date_lt is None:
            self.date_lt = date.today()
            self.date_gt = date(self.date_lt.year, self.date_lt.month, 1)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        proportionality = self.params.get('proportionality')
        center = self.company.center_set.filter(id=self.params.get('center')).first()
        sector = self.company.sector_set.filter(id=self.params.get('sector')).first()

        if sector:
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
            'center_choices': get_center_choices(self.company),
            'sector_choices': get_sector_choices(center)})
        return super().get_context_data(**kwargs)


class CompanyMembershipRequiredMixin(object):

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(self, 'company'):
            self.company = self.get_object()

        if not self.company.is_member(request.user) and \
           not self.organization.is_admin(request.user) and \
           not request.user.is_superuser:
            raise Http404
        return super().dispatch(request, *args, **kwargs)
