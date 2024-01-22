# python
import csv
import urllib

from copy import copy
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta
# django
from django.conf import settings
from django.db.models import Count, Sum
from django.db.models import F, FloatField, ExpressionWrapper
from django.http import Http404
from django.http import HttpResponse
from django.http import StreamingHttpResponse
from django.views.generic import ListView
from django.views.generic.base import RedirectView

# third party
from django_filters.views import BaseFilterView
from organizations.views.mixins import AdminRequiredMixin
from organizations.models import Organization

# project
from accounts.mixins import OrganizationContextMixin
from accounts.mixins import OrganizationMixin
from centers.mixins import CompanyContextMixin
from centers.mixins import CompanyMixin
from centers.models import Center
from centers.models import Company
from centers.models import Sector
from centers.utils import get_center_choices
from centers.utils import get_company_choices
from centers.utils import get_sector_choices
from charges.constants import BASIC_SERVICE_CHOICES
from charges.constants import LEVEL_1_ACCESS_SERVICE
from charges.constants import LEVEL_2_ACCESS_SERVICE
from charges.constants import LEVEL_3_ACCESS_SERVICE
from charges.constants import LEVEL_4_ACCESS_SERVICE
from charges.constants import LEVEL_5_ACCESS_SERVICE
from charges.constants import LEVEL_6_ACCESS_SERVICE
from charges.constants import WIFI_ACCESS_SERVICE
from charges.constants import MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES
from charges.constants import MO_BASIC_CONTACT_CENTER_PLATFORM
from charges.constants import MO_BASIC_RECORDING_PLATFORM
from charges.constants import MO_REAL_TIME_TRACKING
from charges.constants import MO_RECORDING_POSITION
from charges.constants import MO_RECORDING_SUPERVISOR
from charges.constants import MO_SERVICE_POSITION
from charges.constants import MO_SUPERVISOR
from charges.constants import SOFTWARE_ACCESS_SERVICE
from charges.constants import SOFTWARE_EXTENSION_SERVICE
from charges.constants import WIRELESS_ACCESS_SERVICE
from core.reports.pdf.admin import SystemReportAdministrador
from core.reports.pdf.company import SystemReport
from core.reports.pdf.organization import SystemReportOrganization
from core.reports.xlsx.xlsx_company_report import XLSXCompanyReport
from core.reports.xlsx.xlsx_org_report import XLSXOrgReport
from core.utils import Echo
from core.utils import get_amount_ust
from core.utils import get_range_date
from core.utils import get_values_proportionality
from core.utils import time_format
from core.views import SuperuserRequiredMixin

# local
from .constants import CALLTYPE_CHOICES
from .constants import DDD_CHOICES
from .constants import PABX_CHOICES
from .constants import SERVICE_CHOICES
from .constants import VC1, VC2, VC3, LOCAL, LDN, LDI
from .filters import PhonecallFilter
from .models import Phonecall
from .constants import OLD_CONTRACT,  NEW_CONTRACT

from phonecalls.models import Price

CALLTYPE_MAP = dict(CALLTYPE_CHOICES)
PABX_MAP = dict(PABX_CHOICES)
SERVICE_MAP = dict(SERVICE_CHOICES)

BASIC_SERVICE_MAP = {
    LEVEL_1_ACCESS_SERVICE: 'LEVEL_1_ACCESS_SERVICE',
    LEVEL_2_ACCESS_SERVICE: 'LEVEL_2_ACCESS_SERVICE',
    LEVEL_3_ACCESS_SERVICE: 'LEVEL_3_ACCESS_SERVICE',
    LEVEL_4_ACCESS_SERVICE: 'LEVEL_4_ACCESS_SERVICE',
    LEVEL_5_ACCESS_SERVICE: 'LEVEL_5_ACCESS_SERVICE',
    LEVEL_6_ACCESS_SERVICE: 'LEVEL_6_ACCESS_SERVICE',
    WIRELESS_ACCESS_SERVICE: 'WIRELESS_ACCESS_SERVICE',
    SOFTWARE_ACCESS_SERVICE: 'SOFTWARE_ACCESS_SERVICE',
    SOFTWARE_EXTENSION_SERVICE: 'SOFTWARE_EXTENSION_SERVICE',
    MO_BASIC_CONTACT_CENTER_PLATFORM: 'MO_BASIC_CONTACT_CENTER_PLATFORM',
    MO_BASIC_RECORDING_PLATFORM: 'MO_BASIC_RECORDING_PLATFORM',
    MO_SERVICE_POSITION: 'MO_SERVICE_POSITION',
    MO_SUPERVISOR: 'MO_SUPERVISOR',
    MO_REAL_TIME_TRACKING: 'MO_REAL_TIME_TRACKING',
    MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES: 'MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES',
    MO_RECORDING_POSITION: 'MO_RECORDING_POSITION',
    MO_RECORDING_SUPERVISOR: 'MO_RECORDING_SUPERVISOR',
    WIFI_ACCESS_SERVICE: 'WIFI_ACCESS_SERVICE'
}

services_voip_communication = [
    LEVEL_1_ACCESS_SERVICE, LEVEL_2_ACCESS_SERVICE, LEVEL_3_ACCESS_SERVICE,
    LEVEL_4_ACCESS_SERVICE, LEVEL_5_ACCESS_SERVICE, LEVEL_6_ACCESS_SERVICE,
    WIRELESS_ACCESS_SERVICE, SOFTWARE_ACCESS_SERVICE, SOFTWARE_EXTENSION_SERVICE
]

contact_center_services = [
    MO_BASIC_CONTACT_CENTER_PLATFORM, MO_BASIC_RECORDING_PLATFORM, MO_SERVICE_POSITION,
    MO_SUPERVISOR, MO_REAL_TIME_TRACKING, MO_AUTO_ANSWER_CHANNEL_AND_MESSAGES,
    MO_RECORDING_POSITION, MO_RECORDING_SUPERVISOR
]


class BaseCompanyPhonecallView(CompanyMixin,
                               CompanyContextMixin,
                               BaseFilterView,
                               ListView):  # COMPANY
    """
    Classe base para lista de chamadas da empresa (cliente), com filtragem e formatação de dados
    """

    def get_filename(self, resume=False):
        date_gt = self.date_gt.strftime('%d-%m-%Y')
        date_lt = self.date_lt.strftime('%d-%m-%Y')
        return f"{self.company.code}-{date_gt}-{date_lt}{'-resumo' if resume else ''}"

    def get_queryset(self):
        queryset = super().get_queryset() \
            .filter(company=self.company, startdate__gte=self.date_gt) \
            .only('chargednumber', 'dialednumber', 'calltype', 'service', 'pabx',
                  'startdate', 'starttime', 'stopdate', 'stoptime', 'duration', 'billedamount')
        if self.params.get('bound', None) is None:
            return queryset.filter(inbound=False, calltype__in=[LOCAL, VC1, VC2, VC3, LDN, LDI])
        return queryset


class BaseOrgPhonecallView(OrganizationMixin,
                           AdminRequiredMixin,
                           OrganizationContextMixin,
                           BaseFilterView,
                           ListView):  # ORG
    """
    Classe base para lista de chamadas da organização, com filtragem e formatação de dados
    """

    def get_filename(self, resume=False):
        date_gt = self.date_gt.strftime('%d-%m-%Y')
        date_lt = self.date_lt.strftime('%d-%m-%Y')
        return f"{self.organization.slug}-{date_gt}-{date_lt}{'-resumo' if resume else ''}"

    def get_queryset(self):
       # self.date_gt = self.request.GET.get('date_gt')
        if self.request.GET.get('date_gt') is not None:
            self.date_gt = datetime.strptime( self.request.GET.get('date_gt'), '%Y-%m-%d').date()
            self.date_lt = datetime.strptime(self.request.GET.get('date_lt'), '%Y-%m-%d').date()
        queryset = super().get_queryset() \
            .select_related('extension') \
            .filter(organization=self.organization, startdate__gte=self.date_gt) \
            .only('extension__extension', 'chargednumber', 'dialednumber', 'calltype', 'service', 'pabx',
                  'startdate', 'starttime', 'stopdate', 'stoptime', 'duration', 'billedamount')
        count = 0
        for phonecall in queryset.filter(inbound=False, calltype__in=[LOCAL, VC1, VC2, VC3, LDN, LDI]):
            count += 1
        if self.params.get('bound', None) is None:
            return queryset.filter(inbound=False, calltype__in=[LOCAL, VC1, VC2, VC3, LDN, LDI])
        return queryset


class BaseAdmPhonecallView(SuperuserRequiredMixin,
                           BaseFilterView,
                           ListView):  # SUPERUSER
    """
    Classe base para lista de chamadas, com filtragem e formatação de dados
    """

    def get_filename(self, resume=False):
        date_gt = self.date_gt.strftime('%d-%m-%Y')
        date_lt = self.date_lt.strftime('%d-%m-%Y')
        return f"chamadas-{date_gt}-{date_lt}"

    def dispatch(self, request, *args, **kwargs):
        self.params = {key: value for key, value in self.request.GET.items() if key != 'page' and value}
        self.date_gt, self.date_lt = get_range_date(self.request.GET)
        if self.date_gt is None or self.date_lt is None:
            self.date_lt = date.today()
            self.date_gt = date(self.date_lt.year, self.date_lt.month, 1)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset() \
            .select_related('extension') \
            .filter(startdate__gte=self.date_gt) \
            .only('extension__extension', 'chargednumber', 'dialednumber', 'calltype', 'service', 'pabx',
                  'startdate', 'starttime', 'stopdate', 'stoptime', 'duration', 'billedtime', 'org_billedamount')
        if self.params.get('bound', None) is None:
            return queryset.filter(inbound=False, calltype__in=[LOCAL, VC1, VC2, VC3, LDN, LDI])
        return queryset

    def get_context_data(self, **kwargs):
        proportionality = self.params.get('proportionality')
        show_companies = self.params.get('showcompanies')
        kwargs.update({
            'urlencode': urllib.parse.urlencode(self.params),
            'date_gt': self.date_gt.strftime('%Y-%m-%d'),
            'date_lt': self.date_lt.strftime('%Y-%m-%d'),
            'proportionality': proportionality == "true",
            'showcompanies': show_companies == "true"})
        return super().get_context_data(**kwargs)


class CompanyPhonecallListView(BaseCompanyPhonecallView):  # COMPANY
    """
    Lista de chamadas da empresa (cliente)
    Permissão: Membro da empresa
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']

    def get_paginate_by(self, queryset):
        paginate_by = super().get_paginate_by(queryset)
        page_size = self.request.GET.get('page_size', 20)
        try:
            page_size = int(page_size)
            page_size = max(10, min(page_size, 100))
        except TypeError:
            page_size = paginate_by
        return page_size


class CompanyPhonecallResumeView(BaseCompanyPhonecallView):  # COMPANY
    """
    Página com dados do relatório resumido da empresa (cliente)
    Permissão: Membro da empresa
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']
    template_name = 'phonecalls/phonecall_resume.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        phonecall_data = self.object_list \
            .filter(inbound=False,
                    calltype__in=[VC1, VC2, VC3, LOCAL, LDN, LDI]) \
            .values('calltype') \
            .annotate(count=Count('id'),
                      billedtime_sum=Sum('billedtime'),
                      cost_sum=Sum('billedamount')) \
            .order_by('calltype')

        phonecall_total = 0
        duration_total = 0
        cost_total = 0.0
        phonecall_local = []
        phonecall_long_distance = []
        for phonecall in phonecall_data:
            if phonecall['calltype'] in (VC1, LOCAL):
                phonecall_local.append(phonecall)
            elif phonecall['calltype'] in (VC2, VC3, LDN):
                phonecall_long_distance.append(phonecall)
            else:
                continue
            phonecall_total += phonecall['count']
            duration_total += phonecall['billedtime_sum']
            cost_total += float(phonecall['cost_sum'])

        multiplier, divider = get_values_proportionality(
            date_lt=self.date_lt,
            date_gt=self.date_gt,
            proportionality=context['proportionality'])

        service_pricetable = self.company.service_pricetable
        service_price_list = {}
        if service_pricetable:
            service_price_list = service_pricetable.price_set.active()

        service_basic_amount = 0
        service_basic_cost = 0
        basicservice = {}
        for service in service_price_list:
            service_cost = service.basic_service_amount * service.value
            service_cost = (service_cost / divider) * multiplier
            basicservice.setdefault(
                BASIC_SERVICE_MAP[service.basic_service], {
                    'price': service.value,
                    'amount': service.basic_service_amount,
                    'cost': service_cost})
            service_basic_amount += service.basic_service_amount
            service_basic_cost += service_cost

        if service_basic_amount != 0 and service_basic_cost != 0:
            basicservice.update({'service_basic': {
                                     'amount': service_basic_amount,
                                     'cost': service_basic_cost}})

        context.update({
            'phonecall_local': phonecall_local,
            'phonecall_long_distance': phonecall_long_distance,
            'phonecall_total': phonecall_total,
            'cost_total': cost_total,
            'basic_service': basicservice,
            'duration_total': duration_total})
        return context


class CompanyPhonecallReportRedirectView(RedirectView):  # COMPANY
    """
    Classe base de redirecionamento de acordo com formatação do relatório
    """

    query_string = True

    def get(self, request, *args, **kwargs):
        response_format = request.GET.get('format')
        if response_format not in ('csv', 'xlsx', 'pdf'):
            raise Http404

        if response_format == 'csv':
            self.pattern_name = 'phonecalls:report_csv'
        elif response_format == 'xlsx':
            self.pattern_name = 'phonecalls:report_xlsx'
        elif response_format == 'pdf':
            self.pattern_name = 'phonecalls:report_pdf'

        return super().get(request, *args, **kwargs)


class CompanyPhonecallCSVReportView(BaseCompanyPhonecallView):  # COMPANY
    """
    Exportar em CSV relatório detalhado das chamadas da empresa (cliente)
    Permissão: Membro da empresa
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()
        filename = self.get_filename()

        pseudo_buffer = Echo()
        fieldnames = {
            'CENTRO DE CUSTO': 'company__name',
            'DATA DE INICIO':  'startdate',
            'HORA DE INICIO':  'starttime',
            'DATA DE TÉRMINO': 'stopdate',
            'HORA DE TÉRMINO': 'stoptime',
            'RAMAL':           'extension__extension',
            'NÚMERO DISCADO':  'dialednumber',
            'TIPO DE CHAMADA': 'calltype',
            'DURAÇÃO':         'duration',
            'PREÇO':           'price',
            'VALOR FATURADO':  'billedamount'
        }
        rows = [fieldnames.keys()]
        phonecall_data = self.object_list.values_list(*fieldnames.values())
        for data in phonecall_data.iterator():
            data = list(data)
            data[7] = CALLTYPE_MAP[data[7]]
            data[8] = time_format(data[8])
            rows.append(data)

        writer = csv.writer(pseudo_buffer)
        response = StreamingHttpResponse(
            (writer.writerow(row) for row in rows), content_type="text/csv")
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        return response


class CompanyPhonecallXLSXReportView(BaseCompanyPhonecallView):  # COMPANY
    """
    Exportar em XLSX relatório detalhado das chamadas da empresa (cliente)
    Permissão: Membro da empresa
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['extension__extension', '-startdate', '-starttime']

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()
        context = self.get_context_data(filter=self.filterset, object_list=self.object_list)

        report = XLSXCompanyReport(
            date_start=self.date_gt.strftime('%d/%m/%Y'),
            date_stop=self.date_lt.strftime('%d/%m/%Y'),
            title='Relatório de Ligações por Ramal',
            company=self.company)
        report.build_detail_report(context)

        filename = self.get_filename()
        response = HttpResponse(
            report.get_file(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachement; filename={filename}.xlsx'
        return response

    def get_context_data(self, object_list=None, **kwargs):
        phonecall_values = object_list \
            .filter(calltype__in=[VC1, VC2, VC3, LOCAL, LDN, LDI]) \
            .values('startdate', 'starttime', 'stopdate', 'stoptime', 'extension__extension',
                    'chargednumber', 'dialednumber', 'calltype', 'duration', 'billedamount')

        phonecall_data = {}
        for phonecall in phonecall_values:
            extension = phonecall['extension__extension']
            phonecall_data.setdefault(extension, {
                'phonecall_list': [],
                'count': 0,
                'billedtime_sum': 0,
                'cost_sum': 0.0})
            phonecall_data[extension]['phonecall_list'].append(phonecall)
            phonecall_data[extension]['count'] += 1
            phonecall_data[extension]['billedtime_sum'] += phonecall['duration']
            phonecall_data[extension]['cost_sum'] += float(phonecall['billedamount'])
        kwargs['phonecall_data'] = phonecall_data
        return super().get_context_data(**kwargs)


class CompanyPhonecallPDFReportView(BaseCompanyPhonecallView):  # COMPANY
    """
    Exportar em PDF relatório detalhado das chamadas da empresa (cliente)
    Permissão: Membro da empresa
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['extension__extension', '-startdate', '-starttime']

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()
        context = self.get_context_data(filter=self.filterset, object_list=self.object_list)

        filename = self.get_filename()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachement; filename={filename}.pdf'
        report = SystemReport(
            dateBegin=self.date_gt.strftime('%d/%m/%Y'),
            dateEnd=self.date_lt.strftime('%d/%m/%Y'),
            reportTitle='Relatório de Ligações por Ramal',
            company=self.company,
            formatPage=2)
        pdf = report.make_phonecall_table(context)
        response.write(pdf)
        return response

    def get_context_data(self, object_list=None, **kwargs):
        phonecall_values = object_list \
            .filter(calltype__in=[LOCAL, VC1, VC2, VC3, LDN, LDI]) \
            .values('startdate', 'starttime', 'stopdate', 'stoptime', 'extension__extension',
                    'chargednumber', 'dialednumber', 'calltype', 'duration', 'billedamount')

        phonecall_data = {}
        for phonecall in phonecall_values:
            extension = phonecall['extension__extension']
            phonecall_data.setdefault(extension, {
                'phonecall_list': [],
                'count': 0,
                'billedtime_sum': 0,
                'cost_sum': 0.0})
            phonecall_data[extension]['phonecall_list'].append(phonecall)
            phonecall_data[extension]['count'] += 1
            phonecall_data[extension]['billedtime_sum'] += phonecall['duration']
            phonecall_data[extension]['cost_sum'] += float(phonecall['billedamount'])
        kwargs['phonecall_data'] = phonecall_data
        return super().get_context_data(**kwargs)


class CompanyPhonecallResumeReportRedirectView(RedirectView):  # COMPANY
    """
    Classe base de redirecionamento de acordo com formatação do relatório
    """

    query_string = True

    def get(self, request, *args, **kwargs):
        response_format = request.GET.get('format')
        if response_format not in ('xlsx', 'pdf'):
            raise Http404

        if response_format == 'xlsx':
            self.pattern_name = 'phonecalls:resume_report_xlsx'
        elif response_format == 'pdf':
            self.pattern_name = 'phonecalls:resume_report_pdf'

        return super().get(request, *args, **kwargs)


class CompanyPhonecallResumeXLSXReportView(BaseCompanyPhonecallView):  # COMPANY
    """
    Exportar em XLSX relatório resumido das chamadas da empresa (cliente)
    Permissão: Membro da empresa
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()
        context = self.get_context_data(filter=self.filterset, object_list=self.object_list)

        report = XLSXCompanyReport(
            date_start=self.date_gt.strftime('%d/%m/%Y'),
            date_stop=self.date_lt.strftime('%d/%m/%Y'),
            title='Relatório de Resumo dos Serviços',
            company=self.company)
        report.build_resume_report(context)

        filename = self.get_filename(resume=True)
        response = HttpResponse(
            report.get_file(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachement; filename={filename}.xlsx'
        return response

    def get_context_data(self, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        phonecall_data = object_list \
            .filter(inbound=False,
                    calltype__in=[LOCAL, VC1, VC2, VC3, LDN, LDI]) \
            .values('calltype') \
            .annotate(count=Count('id'),
                      billedtime_sum=Sum('billedtime'),
                      cost_sum=Sum('billedamount')) \
            .values('calltype', 'price', 'count', 'billedtime_sum', 'cost_sum') \
            .order_by('calltype')

        multiplier, divider = get_values_proportionality(
            date_lt=self.date_lt,
            date_gt=self.date_gt,
            proportionality=context['proportionality'])

        # basic service
        service_pricetable = self.company.service_pricetable
        service_price_list = {}
        if service_pricetable:
            service_price_list = service_pricetable.price_set.active()

        bs_data = {}
        for service in service_price_list:
            cost = service.basic_service_amount * service.value
            cost = (cost / divider) * multiplier
            bs_data.setdefault(BASIC_SERVICE_MAP[service.basic_service], {
                'price': service.value,
                'amount': service.basic_service_amount,
                'cost': cost})

        # communication service
        cs_data = {}
        for call_data in phonecall_data:
            calltype = call_data['calltype']
            cs_data[calltype] = call_data

        context.update({
            'basic_service': bs_data,
            'communication_service': cs_data})
        return context


class CompanyPhonecallResumePDFReportView(BaseCompanyPhonecallView):  # COMPANY
    """
    Exportar em PDF relatório resumido das chamadas da empresa (cliente)
    Permissão: Membro da empresa
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()
        context = self.get_context_data(filter=self.filterset, object_list=self.object_list)

        filename = self.get_filename(resume=True)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachement; filename={filename}.pdf'
        report = SystemReport(
            dateBegin=self.date_gt.strftime('%d/%m/%Y'),
            dateEnd=self.date_lt.strftime('%d/%m/%Y'),
            reportTitle='Resumo dos Serviços',
            company=self.company)
        pdf = report.make_phonecall_resume_table(context)
        response.write(pdf)
        return response

    def get_context_data(self, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        phonecall_data = object_list \
            .filter(inbound=False,
                    calltype__in=[VC1, VC2, VC3, LOCAL, LDN, LDI]) \
            .values('calltype') \
            .annotate(count=Count('id'),
                      billedtime_sum=Sum('billedtime'),
                      cost_sum=Sum('billedamount')) \
            .values('calltype', 'price', 'count', 'billedtime_sum', 'cost_sum') \
            .order_by('calltype')

        phonecall_total = 0
        duration_total = 0
        cost_total = 0.0
        phonecall_local = []
        phonecall_long_distance = []
        for phonecall in phonecall_data:
            if phonecall['calltype'] in (VC1, LOCAL):
                phonecall_local.append(phonecall)
            elif phonecall['calltype'] in (VC2, VC3, LDN):
                phonecall_long_distance.append(phonecall)
            else:
                continue
            phonecall_total += phonecall['count']
            duration_total += phonecall['billedtime_sum']
            cost_total += float(phonecall['cost_sum'])

        multiplier, divider = get_values_proportionality(
            date_lt=self.date_lt,
            date_gt=self.date_gt,
            proportionality=context['proportionality'])

        service_pricetable = self.company.service_pricetable
        service_price_list = {}
        if service_pricetable:
            service_price_list = service_pricetable.price_set.active()

        service_basic_amount = 0
        service_basic_cost = 0
        basicservice = {}
        for service in service_price_list:
            service_cost = service.basic_service_amount * service.value
            service_cost = (service_cost / divider) * multiplier
            basicservice.setdefault(
                BASIC_SERVICE_MAP[service.basic_service], {
                    'price': service.value,
                    'amount': service.basic_service_amount,
                    'cost': service_cost})
            service_basic_amount += service.basic_service_amount
            service_basic_cost += service_cost

        if service_basic_amount != 0 and service_basic_cost != 0:
            basicservice.update({'service_basic': {
                                     'amount': service_basic_amount,
                                     'cost': service_basic_cost}})

        context.update({
            'phonecall_local': phonecall_local,
            'phonecall_long_distance': phonecall_long_distance,
            'phonecall_total': phonecall_total,
            'basic_service': basicservice,
            'cost_total': cost_total + float(service_basic_cost),
            'duration_total': duration_total})
        return context


class OrgPhonecallListView(BaseOrgPhonecallView):  # ORG
    """
    Lista de chamadas da organização
    Permissão: Administrador da organização
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']
    template_name = 'phonecalls/org_phonecall_list.html'

    def get_paginate_by(self, queryset):
        paginate_by = super().get_paginate_by(queryset)
        page_size = self.request.GET.get('page_size', 20)
        try:
            page_size = int(page_size)
            page_size = max(10, min(page_size, 100))
        except TypeError:
            page_size = paginate_by
        return page_size


class OrgPhonecallResumeView(BaseOrgPhonecallView):  # ORG
    """
    Página com dados do relatório resumido da organização
    Permissão: Adiministrador da organização
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']
    template_name = 'phonecalls/org_phonecall_resume.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        phonecall_data = self.object_list \
            .filter(company__isnull=False,
                    inbound=False,
                    calltype__in=[VC1, VC2, VC3, LOCAL, LDN, LDI]) \
            .values('company__name', 'calltype') \
            .annotate(count=Count('id'),
                      billedtime_sum=Sum('billedtime'),
                      cost_sum=Sum('billedamount') )\
            .values('company__name', 'calltype', 'price', 'company__call_pricetable',
                    'count', 'billedtime_sum', 'cost_sum') \
            .order_by('company__name', 'calltype')


        # constants
        SERVICE = 'SERVIÇOS DE COMUNICAÇÃO'
        CALL_LOCAL = 'local'
        CALL_NATIONAL = 'national'
        CALL_INTERNATIONAL = 'international'
        TOTAL_DICT = {
            'count': 0,
            'cost_sum': 0.0,
            'billedtime_sum': 0}

        phonecall_map = {}
        service_data = copy(TOTAL_DICT)
        multiplier, divider = get_values_proportionality(
            date_lt=self.date_lt,
            date_gt=self.date_gt,
            proportionality=context['proportionality'])

        for phonecall in phonecall_data:
            company_name = phonecall['company__name']
          #  price = Price.objects.all().filter(table_id = phonecall['price_table'], calltype = phonecall['calltype']).active().values('value')
            price = Price.objects.all().filter(table_id=phonecall['company__call_pricetable'],
                                               calltype=phonecall['calltype']).active().values('value')
            phonecall['price'] = price.first()['value']
            phonecall['cost_sum'] = phonecall['billedtime_sum'] * phonecall['price'] / 60
            phonecall_map.setdefault(company_name, copy(TOTAL_DICT))
            phonecall_map[company_name][phonecall['calltype']] = phonecall
            service_data.setdefault(phonecall['calltype'], {
                'cost_sum': 0.0,
                'count': 0,
                'billedtime_sum': 0,
                'price': phonecall['price']})
            service_data[phonecall['calltype']]['cost_sum'] += float(phonecall['cost_sum'])
            service_data[phonecall['calltype']]['count'] += phonecall['count']
            service_data[phonecall['calltype']]['billedtime_sum'] += phonecall['billedtime_sum']

            phonecall_map[company_name].setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            phonecall_map[company_name].setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            phonecall_map[company_name].setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            if phonecall['calltype'] in (LOCAL, VC1, VC2, VC3):
                phonecall_map[company_name][CALL_LOCAL]['count'] += \
                    phonecall['count']
                phonecall_map[company_name][CALL_LOCAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[company_name][CALL_LOCAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']
                service_data[CALL_LOCAL]['count'] += phonecall['count']
                service_data[CALL_LOCAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_LOCAL]['billedtime_sum'] += phonecall['billedtime_sum']
            elif phonecall['calltype'] in (LDN,):
                phonecall_map[company_name][CALL_NATIONAL]['count'] += \
                    phonecall['count']
                phonecall_map[company_name][CALL_NATIONAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[company_name][CALL_NATIONAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']
                service_data[CALL_NATIONAL]['count'] += phonecall['count']
                service_data[CALL_NATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_NATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']
            else:
                phonecall_map[company_name][CALL_INTERNATIONAL]['count'] += \
                    phonecall['count']
                phonecall_map[company_name][CALL_INTERNATIONAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[company_name][CALL_INTERNATIONAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']
                service_data[CALL_INTERNATIONAL]['count'] += phonecall['count']
                service_data[CALL_INTERNATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_INTERNATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']

            phonecall_map[company_name]['count'] += phonecall['count']
            phonecall_map[company_name]['cost_sum'] += float(phonecall['cost_sum'])
            phonecall_map[company_name]['billedtime_sum'] += phonecall['billedtime_sum']
            service_data['count'] += phonecall['count']
            service_data['cost_sum'] += float(phonecall['cost_sum'])
            service_data['billedtime_sum'] += phonecall['billedtime_sum']

        company_list = self.organization.company_set.all()
        for company in company_list:
            service_pricetable = company.service_pricetable
            service_price_list = {}
            if service_pricetable:
                service_price_list = service_pricetable.price_set.active()
            phonecall_map.setdefault(company.name, copy(TOTAL_DICT))
            phonecall_map[company.name].update({'contract_version': company.is_new_contract})
            service_basic_amount = 0
            service_basic_cost = 0
            for service in service_price_list:
                service_cost = service.basic_service_amount * service.value
                service_cost = (service_cost / divider) * multiplier

                phonecall_map[company.name].update({
                    BASIC_SERVICE_MAP[service.basic_service]: {
                        'price': service.value,
                        'amount': service.basic_service_amount,
                        'cost': service_cost
                    }
                })
                service_basic_amount += service.basic_service_amount
                service_basic_cost += service_cost

            if service_basic_amount != 0 and service_basic_cost != 0:
                phonecall_map[company.name].update({
                    'service_basic': {
                        'amount': service_basic_amount,
                        'cost': service_basic_cost
                    }
                })

        phonecall_map[SERVICE] = service_data
        context['phonecall_map'] = phonecall_map
        context['new_contract'] = NEW_CONTRACT
        context['old_contract'] = OLD_CONTRACT
        return context


class OrgPhonecallUSTView(BaseOrgPhonecallView):  # ORG
    """
    Página com dados do relatório resumido da organização
    Permissão: Adiministrador da organização
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']
    template_name = 'phonecalls/org_phonecall_ust.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        phonecall_data = self.object_list \
            .filter(company__isnull=False,
                    inbound=False,
                    calltype__in=[LOCAL, VC1, VC2, VC3, LDN, LDI]) \
            .values('calltype') \
            .annotate(price_ust=  ExpressionWrapper(F('org_price') / settings.PRICE_UST, output_field=FloatField()),
                      billedtime_sum=Sum('billedtime'),
                      cost_ust_sum=Sum('org_billedamount', output_field=FloatField()) / settings.PRICE_UST,
                      cost_sum=Sum('org_billedamount')) \
            .values('calltype', 'price_ust', 'billedtime_sum', 'cost_sum', 'cost_ust_sum') \
            .order_by('calltype')

        # constants
        TOTAL_DICT = {
            'amount': 0.0,
            'billedtime_sum': 0,
            'cost_ust_sum': 0.0,
            'cost_sum': 0.0}
        CALL_LOCAL = 'local'
        CALL_NATIONAL = 'national'
        CALL_INTERNATIONAL = 'international'

        multiplier, divider = get_values_proportionality(
            date_lt=self.date_lt,
            date_gt=self.date_gt,
            proportionality=context['proportionality'])

        # basic service
        service_pricetable = self.organization.settings.service_pricetable
        service_price_list = {}
        if service_pricetable:
            service_price_list = service_pricetable.price_set.active()

        bs_data = {}
        bs_amount = 0
        bs_cost_ust = 0.0
        bs_cost = 0.0
        services_voip_communication_price = 0
        services_voip_communication_amount = 0
        services_voip_communication_cost_ust = 0
        services_voip_communication_cost = 0
        contact_center_services_price = 0
        contact_center_services_amount = 0
        contact_center_services_cost_ust = 0
        contact_center_services_cost = 0

        for service in service_price_list:
            unit_price_ust = float(service.value) / float(settings.PRICE_UST)
            cost = ((service.basic_service_amount * float(service.value)) / divider) * multiplier
            cost_ust = float(cost) / float(settings.PRICE_UST)

            bs_data[BASIC_SERVICE_MAP[service.basic_service]] = {
                'price':    unit_price_ust,
                'amount':   service.basic_service_amount,
                'cost_ust': cost_ust,
                'cost':     cost}

            # total services voip communication
            if service.basic_service in services_voip_communication:
                services_voip_communication_amount += service.basic_service_amount
                services_voip_communication_cost_ust += cost_ust
                services_voip_communication_cost += cost

            # total contact center service
            if service.basic_service in contact_center_services:
                contact_center_services_amount += service.basic_service_amount
                contact_center_services_cost_ust += cost_ust
                contact_center_services_cost += cost

            # total
            bs_amount += service.basic_service_amount
            bs_cost_ust += cost_ust
            bs_cost += cost

        # total services voip communication
        if services_voip_communication_amount != 0 and services_voip_communication_cost != 0:
            bs_data['services_voip_communication'] = {
                'price': services_voip_communication_price,
                'amount': services_voip_communication_amount,
                'cost_ust': services_voip_communication_cost_ust,
                'cost': services_voip_communication_cost}

        # total contact center service
        if contact_center_services_amount != 0 and contact_center_services_cost != 0:
            bs_data['contact_center_services'] = {
                'price': contact_center_services_price,
                'amount': contact_center_services_amount,
                'cost_ust': contact_center_services_cost_ust,
                'cost': contact_center_services_cost}

        # total basic service
        if bs_amount != 0 and bs_cost != 0:
            bs_data['total'] = {
                'amount': bs_amount,
                'cost_ust': bs_cost_ust,
                'cost': bs_cost}

        # communication service
        cs_data = {}
        cs_amount = 0.0
        cs_cost_ust = 0.0
        cs_cost = 0.0
        for data in phonecall_data:
            calltype = data['calltype']
            amount = get_amount_ust(data['price_ust'], data['cost_ust_sum'])

            cs_data.setdefault(calltype, {
                'calltype': calltype,
                'price_ust': data['price_ust'],
                'amount': amount,
                'billedtime_sum': data['billedtime_sum'],
                'cost_ust_sum': float(data['cost_ust_sum']),
                'cost_sum': float(data['cost_sum'])})

            # total calltype distance
            cs_data.setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            cs_data.setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            cs_data.setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            if calltype in (LOCAL, VC1):
                cs_data[CALL_LOCAL]['amount'] += amount
                cs_data[CALL_LOCAL]['billedtime_sum'] += data['billedtime_sum']
                cs_data[CALL_LOCAL]['cost_ust_sum'] += float(data['cost_ust_sum'])
                cs_data[CALL_LOCAL]['cost_sum'] += float(data['cost_sum'])

            elif calltype in (VC2, VC3, LDN):
                cs_data[CALL_NATIONAL]['amount'] += amount
                cs_data[CALL_NATIONAL]['billedtime_sum'] += data['billedtime_sum']
                cs_data[CALL_NATIONAL]['cost_ust_sum'] += float(data['cost_ust_sum'])
                cs_data[CALL_NATIONAL]['cost_sum'] += float(data['cost_sum'])

            else:
                cs_data[CALL_INTERNATIONAL]['amount'] += amount
                cs_data[CALL_INTERNATIONAL]['billedtime_sum'] += data['billedtime_sum']
                cs_data[CALL_INTERNATIONAL]['cost_ust_sum'] += float(data['cost_ust_sum'])
                cs_data[CALL_INTERNATIONAL]['cost_sum'] += float(data['cost_sum'])

            # total
            cs_amount += amount
            cs_cost_ust += float(data['cost_ust_sum'])
            cs_cost += float(data['cost_sum'])

        # total communication service
        cs_data['total'] = {
            'amount': cs_amount,
            'cost_ust_sum': cs_cost_ust,
            'cost_sum': cs_cost}

        context.update({
            'basic_service': bs_data,
            'communication_service': cs_data,
            'total_cost_ust': bs_cost_ust + cs_cost_ust,
            'total_cost': bs_cost + cs_cost})
        return context


class OrgPhonecallReportRedirectView(RedirectView):  # ORG
    """
    Classe base de redirecionamento de acordo com formatação do relatório
    """

    query_string = True

    def get(self, request, *args, **kwargs):
        response_format = request.GET.get('format')
        if response_format not in ('csv', 'xlsx'):
            raise Http404

        if response_format == 'csv':
            self.pattern_name = 'phonecalls:org_phonecall_report_csv'
        elif response_format == 'xlsx':
            self.pattern_name = 'phonecalls:org_phonecall_report_xlsx'

        return super().get(request, *args, **kwargs)


class OrgPhonecallCSVReportView(BaseOrgPhonecallView):  # ORG
    """
    Exportar em CSV relatório detalhado das chamadas da organização
    Permissão: Administrador da organização
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()
        filename = self.get_filename()

        pseudo_buffer = Echo()
        fieldnames = {
            'CENTRO DE CUSTO':    'company__name',
            'DATA DE INICIO':     'startdate',
            'HORA DE INICIO':     'starttime',
            'DATA DE TÉRMINO':    'stopdate',
            'HORA DE TÉRMINO':    'stoptime',
            'RAMAL':              'extension__extension',
            'NÚMERO COBRADO':     'chargednumber',
            'NÚMERO DISCADO':     'dialednumber',
            'TIPO DE CHAMADA':    'calltype',
            'TIPO DE SERVIÇO':    'service',
            'CLASSIFICAÇÂO PABX': 'pabx',
            'DESCRIÇÂO':          'description',
            'DURAÇÃO':            'duration',
            'PREÇO':              'price',
            'VALOR FATURADO':     'billedamount'
        }
        rows = [fieldnames.keys()]
        phonecall_data = self.object_list.values_list(*fieldnames.values())
        for data in phonecall_data.iterator():
            data = list(data)
            data[8] = CALLTYPE_MAP[data[8]]
            data[9] = SERVICE_MAP[data[9]] if data[9] else ''
            data[10] = PABX_MAP[data[10]] if data[10] else ''
            data[12] = time_format(data[12])
            rows.append(data)

        writer = csv.writer(pseudo_buffer)
        response = StreamingHttpResponse(
            (writer.writerow(row) for row in rows), content_type="text/csv")
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        return response


class OrgPhonecallXLSXReportView(BaseOrgPhonecallView):  # ORG
    """
    Exportar em XLSX relatório detalhado das chamadas da organização
    Permissão: Administrador da organização
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['company', 'extension__extension', '-startdate', '-starttime']

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()
        context = self.get_context_data(filter=self.filterset, object_list=self.object_list)

        report = XLSXOrgReport(
            date_start=self.date_gt.strftime('%d/%m/%Y'),
            date_stop=self.date_lt.strftime('%d/%m/%Y'),
            title='Relatório Geral de Ligações por Ramal',
            org=self.organization)
        report.build_detail_report(context)

        filename = self.get_filename()
        response = HttpResponse(
            report.get_file(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachement; filename={filename}.xlsx'
        return response

    def get_context_data(self, object_list=None, **kwargs):
        phonecall_values = object_list \
            .filter(company__isnull=False,
                    calltype__in=[VC1, VC2, VC3, LOCAL, LDN, LDI]) \
            .values('company__name', 'company__description', 'startdate', 'starttime', 'stopdate', 'stoptime',
                    'extension__extension', 'chargednumber', 'dialednumber', 'calltype', 'service', 'pabx',
                    'duration', 'billedamount')

        phonecall_data = {}
        for phonecall in phonecall_values:
            name = phonecall['company__name']
            description = phonecall['company__description']
            company = f'{name.upper()} - {description}' if description else name.upper()
            extension = phonecall['extension__extension']

            phonecall_data.setdefault(company, {})
            phonecall_data[company].setdefault(extension, {'phonecall_list': []})
            phonecall_data[company][extension]['phonecall_list'].append(phonecall)
        kwargs['phonecall_data'] = phonecall_data
        return super().get_context_data(**kwargs)


class OrgPhonecallResumeReportRedirectView(RedirectView):  # ORG
    """
    Classe base de redirecionamento de acordo com formatação do relatório
    """

    query_string = True

    def get(self, request, *args, **kwargs):
        response_format = request.GET.get('format')
        if response_format not in ('xlsx', 'pdf'):
            raise Http404

        if response_format == 'xlsx':
            self.pattern_name = 'phonecalls:org_phonecall_resume_report_xlsx'
        elif response_format == 'pdf':
            self.pattern_name = 'phonecalls:org_phonecall_resume_report_pdf'

        return super().get(request, *args, **kwargs)


class OrgPhonecallResumeXLSXReportView(BaseOrgPhonecallView):  # ORG
    """
    Exportar em XLSX relatório resumido das chamadas da organização
    Permissão: Administrador da organização
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()
        context = self.get_context_data(filter=self.filterset, object_list=self.object_list)

        report = XLSXOrgReport(
            date_start=self.date_gt.strftime('%d/%m/%Y'),
            date_stop=self.date_lt.strftime('%d/%m/%Y'),
            title='Relatório de Resumo dos Serviços',
            org=self.organization)
        report.build_resume_report(context)

        filename = self.get_filename()
        response = HttpResponse(
            report.get_file(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachement; filename={filename}.xlsx'
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        phonecall_data = self.object_list \
            .filter(company__isnull=False,
                    inbound=False,
                    calltype__in=[LOCAL, VC1, VC2, VC3, LDN, LDI]) \
            .values('company__name', 'calltype') \
            .annotate(count=Count('id'),
                      billedtime_sum=Sum('billedtime'),
                      cost_sum=Sum('billedamount')) \
            .values('company__name', 'company__description', 'calltype',
                    'price', 'count', 'billedtime_sum', 'cost_sum') \
            .order_by('company__name', 'calltype')

        # constants
        BASIC_SERVICE = 'basic_service'
        COMMUNICATION_SERVICE = 'communication_service'
        CALL_LOCAL = 'local'
        CALL_NATIONAL = 'national'
        CALL_INTERNATIONAL = 'international'
        TOTAL_DICT = {
            'count': 0,
            'cost_sum': 0.0,
            'billedtime_sum': 0}

        # basic service
        bs_data = {}
        basic_service_map = dict(BASIC_SERVICE_CHOICES)
        for bs in basic_service_map.keys():
            bs_data.setdefault(bs, {
                'amount': 0,
                'cost': 0})

        # communication service
        cs_data = copy(TOTAL_DICT)

        data = {}
        multiplier, divider = get_values_proportionality(
            date_lt=self.date_lt,
            date_gt=self.date_gt,
            proportionality=context['proportionality'])

        for phonecall in phonecall_data:
            name = phonecall['company__name']
            description = phonecall['company__description']
            company = f'{name.upper()} - {description}' if description else name.upper()
            calltype = phonecall['calltype']

            data.setdefault(company, copy(TOTAL_DICT))

            data[company][calltype] = phonecall

            # communication service
            cs_data.setdefault(calltype, {
                'cost_sum': 0.0,
                'count': 0,
                'billedtime_sum': 0,
                'price': phonecall['price']})
            cs_data[calltype]['cost_sum'] += float(phonecall['cost_sum'])
            cs_data[calltype]['count'] += phonecall['count']
            cs_data[calltype]['billedtime_sum'] += phonecall['billedtime_sum']

            data[company].setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            data[company].setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            data[company].setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            # communication service
            cs_data.setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            cs_data.setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            cs_data.setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            if calltype in (LOCAL, VC1):
                data[company][CALL_LOCAL]['count'] += phonecall['count']
                data[company][CALL_LOCAL]['cost_sum'] += float(phonecall['cost_sum'])
                data[company][CALL_LOCAL]['billedtime_sum'] += phonecall['billedtime_sum']

                # communication service
                cs_data[CALL_LOCAL]['count'] += phonecall['count']
                cs_data[CALL_LOCAL]['cost_sum'] += float(phonecall['cost_sum'])
                cs_data[CALL_LOCAL]['billedtime_sum'] += phonecall['billedtime_sum']

            elif calltype in (VC2, VC3, LDN):
                data[company][CALL_NATIONAL]['count'] += phonecall['count']
                data[company][CALL_NATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                data[company][CALL_NATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']

                # communication service
                cs_data[CALL_NATIONAL]['count'] += phonecall['count']
                cs_data[CALL_NATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                cs_data[CALL_NATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']

            else:
                data[company][CALL_INTERNATIONAL]['count'] += phonecall['count']
                data[company][CALL_INTERNATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                data[company][CALL_INTERNATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']

                # communication service
                cs_data[CALL_INTERNATIONAL]['count'] += phonecall['count']
                cs_data[CALL_INTERNATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                cs_data[CALL_INTERNATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']

            data[company]['count'] += phonecall['count']
            data[company]['cost_sum'] += float(phonecall['cost_sum'])
            data[company]['billedtime_sum'] += phonecall['billedtime_sum']

            # communication service
            cs_data['count'] += phonecall['count']
            cs_data['cost_sum'] += float(phonecall['cost_sum'])
            cs_data['billedtime_sum'] += phonecall['billedtime_sum']

        company_list = self.organization.company_set.active()
        for company in company_list:
            name = company.name
            description = company.description
            company_name = f'{name.upper()} - {description}' if description else name.upper()

            data.setdefault(company_name, copy(TOTAL_DICT))

            service_pricetable = company.service_pricetable
            service_price_list = {}
            if service_pricetable:
                service_price_list = service_pricetable.price_set.active()

            for service in service_price_list:
                data[company_name].setdefault(BASIC_SERVICE, {})

                if service.basic_service not in data[company_name][BASIC_SERVICE]:
                    service_cost = service.basic_service_amount * service.value
                    service_cost = (service_cost / divider) * multiplier

                    data[company_name][BASIC_SERVICE][service.basic_service] = {
                        'price': service.value,
                        'amount': service.basic_service_amount,
                        'cost': service_cost}
                    bs_data[service.basic_service]['amount'] += service.basic_service_amount
                    bs_data[service.basic_service]['cost'] += service_cost

        kwargs['data'] = {
            BASIC_SERVICE: bs_data,
            COMMUNICATION_SERVICE: cs_data,
            'company_data': data}
        return super().get_context_data(**kwargs)


class OrgPhonecallResumePDFReportView(BaseOrgPhonecallView):  # ORG
    """
    Exportar em PDF relatório resumido das chamadas da organização
    Permissão: Administrador da organização
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()
        context = self.get_context_data(filter=self.filterset, object_list=self.object_list)

        filename = self.get_filename(resume=True)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachement; filename={filename}.pdf'
        report = SystemReportOrganization(
            dateBegin=self.date_gt.strftime('%d/%m/%Y'),
            dateEnd=self.date_lt.strftime('%d/%m/%Y'),
            reportTitle='Resumo Geral dos Serviços',
            context=context)
        pdf = report.create_table_resume_services(context['phonecall_map'])
        response.write(pdf)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        phonecall_data = self.object_list \
            .filter(company__isnull=False,
                    inbound=False,
                    calltype__in=[VC1, VC2, VC3, LOCAL, LDN, LDI]) \
            .values('company__name', 'company__description', 'calltype') \
            .annotate(count=Count('id'),
                      billedtime_sum=Sum('billedtime'),
                      cost_sum=Sum('billedamount')) \
            .values('company__name', 'company__description', 'calltype',
                    'price', 'count', 'billedtime_sum', 'cost_sum') \
            .order_by('company__name', 'calltype')

        # constants
        SERVICE = 'SERVIÇOS DE COMUNICAÇÃO'
        SERVICE_BASIC = 'SERVIÇOS BÁSICOS'
        CALL_LOCAL = 'local'
        CALL_NATIONAL = 'national'
        CALL_INTERNATIONAL = 'international'
        TOTAL_DICT = {
            'count': 0,
            'cost_sum': 0.0,
            'billedtime_sum': 0}

        service_basic_total = {}
        for key, value in BASIC_SERVICE_MAP.items():
            service_basic_total.setdefault(value, {
                'amount': 0,
                'cost': 0})

        phonecall_map = {}
        service_data = copy(TOTAL_DICT)
        multiplier, divider = get_values_proportionality(
            date_lt=self.date_lt,
            date_gt=self.date_gt,
            proportionality=context['proportionality'])

        for phonecall in phonecall_data:
            company_name = phonecall['company__name']

            phonecall_map.setdefault(company_name, copy(TOTAL_DICT))
            phonecall_map[company_name]['desc'] = phonecall['company__description']

            phonecall_map[company_name][phonecall['calltype']] = phonecall
            service_data.setdefault(phonecall['calltype'], {
                'cost_sum': 0.0,
                'count': 0,
                'billedtime_sum': 0,
                'price': phonecall['price']})
            service_data[phonecall['calltype']]['cost_sum'] += float(phonecall['cost_sum'])
            service_data[phonecall['calltype']]['count'] += phonecall['count']
            service_data[phonecall['calltype']]['billedtime_sum'] += phonecall['billedtime_sum']

            phonecall_map[company_name].setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            phonecall_map[company_name].setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            phonecall_map[company_name].setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            if phonecall['calltype'] in (LOCAL, VC1, VC2, VC3):
                phonecall_map[company_name][CALL_LOCAL]['count'] \
                    += phonecall['count']
                phonecall_map[company_name][CALL_LOCAL]['cost_sum'] \
                    += float(phonecall['cost_sum'])
                phonecall_map[company_name][CALL_LOCAL]['billedtime_sum'] \
                    += phonecall['billedtime_sum']
                service_data[CALL_LOCAL]['count'] += phonecall['count']
                service_data[CALL_LOCAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_LOCAL]['billedtime_sum'] += phonecall['billedtime_sum']
            elif phonecall['calltype'] in (LDN,):
                phonecall_map[company_name][CALL_NATIONAL]['count'] += \
                    phonecall['count']
                phonecall_map[company_name][CALL_NATIONAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[company_name][CALL_NATIONAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']
                service_data[CALL_NATIONAL]['count'] += phonecall['count']
                service_data[CALL_NATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_NATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']
            else:
                phonecall_map[company_name][CALL_INTERNATIONAL]['count'] += \
                    phonecall['count']
                phonecall_map[company_name][CALL_INTERNATIONAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[company_name][CALL_INTERNATIONAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']
                service_data[CALL_INTERNATIONAL]['count'] += phonecall['count']
                service_data[CALL_INTERNATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_INTERNATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']

            phonecall_map[company_name]['count'] += phonecall['count']
            phonecall_map[company_name]['cost_sum'] += float(phonecall['cost_sum'])
            phonecall_map[company_name]['billedtime_sum'] += phonecall['billedtime_sum']
            service_data['count'] += phonecall['count']
            service_data['cost_sum'] += float(phonecall['cost_sum'])
            service_data['billedtime_sum'] += phonecall['billedtime_sum']

        company_list = self.organization.company_set.all()
        for company in company_list:
            service_pricetable = company.service_pricetable
            service_price_list = {}
            if service_pricetable:
                service_price_list = service_pricetable.price_set.active()

            phonecall_map.setdefault(company.name, copy(TOTAL_DICT))
            phonecall_map[company.name]['desc'] = company.description
            phonecall_map[company.name].update({'contract_version': company.is_new_contract})

            service_basic_amount = 0
            service_basic_cost = 0
            for service in service_price_list:
                if BASIC_SERVICE_MAP[service.basic_service] not in phonecall_map[company.name]:
                    service_cost = service.basic_service_amount * service.value
                    service_cost = (service_cost / divider) * multiplier
                    phonecall_map[company.name].setdefault(
                        BASIC_SERVICE_MAP[service.basic_service], {
                            'price': service.value,
                            'amount': service.basic_service_amount,
                            'cost': service_cost})
                    # Now for each level_6 service (DECT phone without a base) we need to add a base
                    if BASIC_SERVICE_MAP[service.basic_service] == 'LEVEL_6_ACCESS_SERVICE' and company.is_new_contract == OLD_CONTRACT:
                        service_basic_total[BASIC_SERVICE_MAP[WIRELESS_ACCESS_SERVICE]]['amount'] += \
                            service.basic_service_amount
                        service_basic_total[BASIC_SERVICE_MAP[WIRELESS_ACCESS_SERVICE]]['cost'] += \
                            service_cost
                    elif BASIC_SERVICE_MAP[service.basic_service] != 'WIRELESS_ACCESS_SERVICE' or company.is_new_contract == NEW_CONTRACT:
                        service_basic_total[BASIC_SERVICE_MAP[service.basic_service]]['amount'] += \
                            service.basic_service_amount
                        service_basic_total[BASIC_SERVICE_MAP[service.basic_service]]['cost'] += \
                            service_cost
                    service_basic_amount += service.basic_service_amount
                    service_basic_cost += service_cost

            if service_basic_amount != 0 and service_basic_cost != 0:
                phonecall_map[company.name].setdefault('service_basic', {
                    'amount': service_basic_amount,
                    'cost': service_basic_cost})

        phonecall_map[SERVICE_BASIC] = service_basic_total
        phonecall_map[SERVICE] = service_data
        kwargs['phonecall_map'] = phonecall_map
        return super().get_context_data(**kwargs)


class OrgPhonecallUSTResumeReportRedirectView(RedirectView):  # ORG
    """
    Classe base de redirecionamento de acordo com formatação do relatório
    """

    query_string = True

    def get(self, request, *args, **kwargs):
        response_format = request.GET.get('format')
        if response_format not in ('xlsx', 'pdf'):
            raise Http404

        if response_format == 'xlsx':
            self.pattern_name = 'phonecalls:org_phonecall_ust_resume_report_xlsx'
        elif response_format == 'pdf':
            self.pattern_name = 'phonecalls:org_phonecall_ust_resume_report_pdf'

        return super().get(request, *args, **kwargs)


class OrgPhonecallUSTResumeXLSXReportView(BaseOrgPhonecallView):  # ORG
    """
    Exportar em XLSX relatório resumido UST das chamadas da organização
    Permissão: Administrador da organização
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()
        context = self.get_context_data(filter=self.filterset, object_list=self.object_list)
        filename = self.get_filename(resume=True)

        report = XLSXOrgReport(
            date_start=self.date_gt.strftime('%d/%m/%Y'),
            date_stop=self.date_lt.strftime('%d/%m/%Y'),
            title='Relatório Execução dos Serviços em UST',
            org=self.organization)
        report.build_ust_resume_report(context)

        filename = self.get_filename()
        response = HttpResponse(
            report.get_file(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachement; filename={filename}.xlsx'
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        phonecall_data = self.object_list \
            .filter(company__isnull=False,
                    inbound=False,
                    calltype__in=[VC1, VC2, VC3, LOCAL, LDN, LDI]) \
            .values('calltype') \
            .annotate(price_ust=F('org_price') / settings.PRICE_UST,
                      billedtime_sum=Sum('billedtime'),
                      cost_ust_sum=Sum('org_billedamount') / settings.PRICE_UST,
                      cost_sum=Sum('org_billedamount')) \
            .values('calltype', 'price_ust', 'billedtime_sum', 'cost_sum', 'cost_ust_sum') \
            .order_by('calltype')

        # constants
        multiplier, divider = get_values_proportionality(
            date_lt=self.date_lt,
            date_gt=self.date_gt,
            proportionality=context['proportionality'])

        # basic service
        service_pricetable = self.organization.settings.service_pricetable
        service_price_list = {}
        if service_pricetable:
            service_price_list = service_pricetable.price_set.active()

        bs_data = {}
        for service in service_price_list:
            unit_price_ust = float(service.value) / float(settings.PRICE_UST)
            cost = ((service.basic_service_amount * service.value) / divider) * multiplier
            bs_data[service.basic_service] = {
                'price': unit_price_ust,
                'amount': service.basic_service_amount,
                'cost_ust': float(cost) / float(settings.PRICE_UST),
                'cost': cost}

        # communication service
        cs_data = {}
        for call_data in phonecall_data:
            calltype = call_data['calltype']
            cs_data[calltype] = call_data

        context.update({
            'basic_service': bs_data,
            'communication_service': cs_data})
        return context


class OrgPhonecallUSTResumePDFReportView(BaseOrgPhonecallView):  # ORG
    """
    Exportar em PDF relatório resumido das chamadas da organização
    Permissão: Administrador da organização
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()
        context = self.get_context_data(filter=self.filterset, object_list=self.object_list)
        filename = self.get_filename(resume=True)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachement; filename={filename}.pdf'
        report = SystemReportOrganization(
            dateBegin=self.date_gt.strftime('%d/%m/%Y'),
            dateEnd=self.date_lt.strftime('%d/%m/%Y'),
            reportTitle='Relatório Execução dos Serviços em UST',
            context=context,
            ust=True)
        pdf = report.create_table_ust_services(context['phonecall_map'])
        response.write(pdf)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        phonecall_data = self.object_list \
            .filter(company__isnull=False,
                    inbound=False,
                    calltype__in=[VC1, VC2, VC3, LOCAL, LDN, LDI]) \
            .values('organization__name', 'company__name', 'calltype') \
            .annotate(count=Count('id'),
                      price_ust=F('org_price') / settings.PRICE_UST,
                      billedtime_sum=Sum('billedtime'),
                      cost_ust_sum=Sum('org_billedamount') / settings.PRICE_UST,
                      cost_sum=Sum('org_billedamount')) \
            .values('organization__name', 'company__name', 'calltype', 'price_ust',
                    'count', 'billedtime_sum', 'cost_sum', 'cost_ust_sum') \
            .order_by('organization__name', 'company__name', 'calltype')

        # constants
        SERVICE = 'SERVIÇOS DE COMUNICAÇÃO'
        CALL_LOCAL = 'local'
        CALL_NATIONAL = 'national'
        CALL_INTERNATIONAL = 'international'
        TOTAL_DICT = {
            'count': 0,
            'cost_sum': 0.0,
            'cost_ust_sum': 0.0,
            'billedtime_sum': 0}

        phonecall_map = {}
        service_data = copy(TOTAL_DICT)
        multiplier, divider = get_values_proportionality(
            date_lt=self.date_lt,
            date_gt=self.date_gt,
            proportionality=context['proportionality'])

        for phonecall in phonecall_data:
            org_name = phonecall['organization__name']
            company_name = phonecall['company__name']

            # organization
            phonecall_map.setdefault(org_name, copy(TOTAL_DICT))
            phonecall_map[org_name].setdefault('companies', {})

            # company
            phonecall_map[org_name]['companies'].setdefault(company_name, copy(TOTAL_DICT))

            organization = Organization.objects.get(name=org_name)
            service_pricetable = organization.settings.service_pricetable
            service_price_list = {}
            if service_pricetable:
                service_price_list = service_pricetable.price_set.active()

            service_basic_price = 0
            service_basic_amount = 0
            service_basic_cost_ust = 0
            service_basic_cost = 0
            for service in service_price_list:
                price_unid_ust = float(service.value) / float(settings.PRICE_UST)
                cost = ((service.basic_service_amount * service.value) / divider) * multiplier
                phonecall_map[org_name].update({
                    BASIC_SERVICE_MAP[service.basic_service]: {
                        'price': price_unid_ust,
                        'amount': service.basic_service_amount,
                        'cost_ust': float(cost) / float(settings.PRICE_UST),
                        'cost': cost
                    }
                })
                service_basic_price += price_unid_ust
                service_basic_amount += service.basic_service_amount
                service_basic_cost_ust += float(cost) / float(settings.PRICE_UST)
                service_basic_cost += cost

            if service_basic_amount != 0 and service_basic_cost != 0:
                phonecall_map[org_name].update({
                    'service_basic': {
                        'price': service_basic_price,
                        'amount': service_basic_amount,
                        'cost_ust': service_basic_cost_ust,
                        'cost': service_basic_cost
                    }
                })

            phonecall_map[org_name].setdefault(phonecall['calltype'], {
                'organization_name': org_name,
                'company_name': company_name,
                'calltype': phonecall['calltype'],
                'price_ust': phonecall['price_ust'],
                'count': 0,
                'billedtime_sum': 0,
                'cost_ust_sum': 0,
                'cost_sum': 0})
            phonecall_map[org_name][phonecall['calltype']]['count'] \
                += phonecall['count']
            phonecall_map[org_name][phonecall['calltype']]['billedtime_sum'] \
                += phonecall['billedtime_sum']
            phonecall_map[org_name][phonecall['calltype']]['cost_sum'] \
                += phonecall['cost_sum']
            phonecall_map[org_name][phonecall['calltype']]['cost_ust_sum'] \
                += phonecall['cost_ust_sum']

            phonecall_map[org_name]['companies'][company_name][phonecall['calltype']] = phonecall
            service_data.setdefault(phonecall['calltype'], {
                'cost_sum': 0.0,
                'cost_ust_sum': 0.0,
                'count': 0,
                'billedtime_sum': 0,
                'price_ust': phonecall['price_ust']})

            service_data[phonecall['calltype']]['cost_sum'] += float(phonecall['cost_sum'])
            service_data[phonecall['calltype']]['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
            service_data[phonecall['calltype']]['count'] += phonecall['count']
            service_data[phonecall['calltype']]['billedtime_sum'] += phonecall['billedtime_sum']

            # organization
            phonecall_map[org_name].setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            phonecall_map[org_name].setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            phonecall_map[org_name].setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            # company
            phonecall_map[org_name]['companies'][company_name] \
                .setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            phonecall_map[org_name]['companies'][company_name] \
                .setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            phonecall_map[org_name]['companies'][company_name] \
                .setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            service_data.setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            if phonecall['calltype'] in (LOCAL, VC1, VC2, VC3):
                phonecall_map[org_name][CALL_LOCAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name][CALL_LOCAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name][CALL_LOCAL]['cost_ust_sum'] += \
                    float(phonecall['cost_ust_sum'])
                phonecall_map[org_name][CALL_LOCAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['cost_ust_sum'] += \
                    float(phonecall['cost_ust_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                service_data[CALL_LOCAL]['count'] += phonecall['count']
                service_data[CALL_LOCAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_LOCAL]['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
                service_data[CALL_LOCAL]['billedtime_sum'] += phonecall['billedtime_sum']
            elif phonecall['calltype'] in (LDN,):
                phonecall_map[org_name][CALL_NATIONAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name][CALL_NATIONAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name][CALL_NATIONAL]['cost_ust_sum'] += \
                    float(phonecall['cost_ust_sum'])
                phonecall_map[org_name][CALL_NATIONAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['count'] \
                    += phonecall['count']
                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['cost_sum'] \
                    += float(phonecall['cost_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['cost_ust_sum'] \
                    += float(phonecall['cost_ust_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['billedtime_sum'] \
                    += phonecall['billedtime_sum']

                service_data[CALL_NATIONAL]['count'] += phonecall['count']
                service_data[CALL_NATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_NATIONAL]['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
                service_data[CALL_NATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']
            else:
                phonecall_map[org_name][CALL_INTERNATIONAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name][CALL_INTERNATIONAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name][CALL_INTERNATIONAL]['cost_ust_sum'] += \
                    float(phonecall['cost_ust_sum'])
                phonecall_map[org_name][CALL_INTERNATIONAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['count'] \
                    += phonecall['count']
                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['cost_sum'] \
                    += float(phonecall['cost_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['cost_ust_sum'] \
                    += float(phonecall['cost_ust_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['billedtime_sum'] \
                    += phonecall['billedtime_sum']

                service_data[CALL_INTERNATIONAL]['count'] += phonecall['count']
                service_data[CALL_INTERNATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_INTERNATIONAL]['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
                service_data[CALL_INTERNATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']

            phonecall_map[org_name]['count'] += phonecall['count']
            phonecall_map[org_name]['cost_sum'] += float(phonecall['cost_sum'])
            phonecall_map[org_name]['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
            phonecall_map[org_name]['billedtime_sum'] += phonecall['billedtime_sum']

            phonecall_map[org_name]['companies'][company_name]['count'] \
                += phonecall['count']
            phonecall_map[org_name]['companies'][company_name]['cost_sum'] \
                += float(phonecall['cost_sum'])
            phonecall_map[org_name]['companies'][company_name]['cost_ust_sum'] \
                += float(phonecall['cost_ust_sum'])
            phonecall_map[org_name]['companies'][company_name]['billedtime_sum'] \
                += phonecall['billedtime_sum']

            service_data['count'] += phonecall['count']
            service_data['cost_sum'] += float(phonecall['cost_sum'])
            service_data['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
            service_data['billedtime_sum'] += phonecall['billedtime_sum']
        phonecall_map[SERVICE] = service_data
        context['phonecall_map'] = phonecall_map
        return context


class AdmPhonecallListView(BaseAdmPhonecallView):  # SUPERUSER
    """
    Lista de chamadas
    Permissão: Super usuário
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']
    template_name = 'phonecalls/adm_phonecall_list.html'

    def get_paginate_by(self, queryset):
        paginate_by = super().get_paginate_by(queryset)
        page_size = self.request.GET.get('page_size', 20)
        try:
            page_size = int(page_size)
            page_size = max(10, min(page_size, 100))
        except TypeError:
            page_size = paginate_by
        return page_size

    def get_org_choices(self):
        org_choices = []
        for org in Organization.objects.all():
            org_choices.append((org.slug, org.name))
        return org_choices

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = Organization.objects.filter(slug=self.params.get('organization')).first()
        company = Company.objects.filter(slug=self.params.get('company')).first()
        center = Center.objects.filter(id=self.params.get('center')).first()
        sector = Sector.objects.filter(id=self.params.get('sector')).first()

        if company:
            org = company.organization
        if center:
            org = center.organization
            company = center.company
        if sector:
            org = sector.organization
            company = sector.company
            center = sector.center

        context.update({
            'calltype_choices': CALLTYPE_CHOICES,
            'pabx_choices': PABX_CHOICES,
            'service_choices': SERVICE_CHOICES,
            'ddd_choices': DDD_CHOICES,
            'org_choices': self.get_org_choices(),
            'company_choices': get_company_choices(org),
            'center_choices': get_center_choices(company),
            'sector_choices': get_sector_choices(center)})
        return context


class AdmPhonecallResumeView(BaseAdmPhonecallView):  # SUPERUSER
    """
    Página com dados do relatório resumido das organizações
    Permissão: Super Usuário
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']
    template_name = 'phonecalls/adm_phonecall_resume.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        phonecall_data = self.object_list \
            .filter(organization__isnull=False,
                    inbound=False,
                    calltype__in=[VC1, VC2, VC3, LOCAL, LDN, LDI]) \
            .values('organization__name', 'company__name', 'calltype') \
            .annotate(count=Count('id'),
                      billedtime_sum=Sum('billedtime'),
                      cost_sum=Sum('org_billedamount')) \
            .values('organization__name', 'company__name', 'calltype', 'org_price',
                    'count', 'billedtime_sum', 'cost_sum') \
            .order_by('organization__name', 'company__name', 'calltype')

        # constants
        SERVICE = 'SERVIÇOS DE COMUNICAÇÃO'
        CALL_LOCAL = 'local'
        CALL_NATIONAL = 'national'
        CALL_INTERNATIONAL = 'international'
        TOTAL_DICT = {
            'count': 0,
            'cost_sum': 0.0,
            'billedtime_sum': 0}

        phonecall_map = {}
        service_data = copy(TOTAL_DICT)
        multiplier, divider = get_values_proportionality(
            date_lt=self.date_lt,
            date_gt=self.date_gt,
            proportionality=context['proportionality'])

        for phonecall in phonecall_data:
            org_name = phonecall['organization__name']
            company_name = phonecall['company__name']

            # organization
            phonecall_map.setdefault(org_name, copy(TOTAL_DICT))
            phonecall_map[org_name].setdefault('companies', {})

            # company
            phonecall_map[org_name]['companies'].setdefault(company_name, copy(TOTAL_DICT))

            organization = Organization.objects.get(name=org_name)
            service_pricetable = organization.settings.service_pricetable
            service_price_list = {}
            if service_pricetable:
                service_price_list = service_pricetable.price_set.active()

            service_basic_amount = 0
            service_basic_cost = 0
            for service in service_price_list:
                cost = ((service.basic_service_amount * service.value) / divider) * multiplier
                phonecall_map[org_name].update({
                    BASIC_SERVICE_MAP[service.basic_service]: {
                        'price': service.value,
                        'amount': service.basic_service_amount,
                        'cost': cost
                    }
                })
                service_basic_amount += service.basic_service_amount
                service_basic_cost += cost

            if service_basic_amount != 0 and service_basic_cost != 0:
                phonecall_map[org_name].update({
                    'service_basic': {
                        'amount': service_basic_amount,
                        'cost': service_basic_cost
                    }
                })

            phonecall_map[org_name].setdefault(phonecall['calltype'], {
                'organization_name': org_name,
                'company_name': company_name,
                'calltype': phonecall['calltype'],
                'org_price': phonecall['org_price'],
                'count': 0,
                'billedtime_sum': 0,
                'cost_sum': 0})
            phonecall_map[org_name][phonecall['calltype']]['count'] \
                += phonecall['count']
            phonecall_map[org_name][phonecall['calltype']]['billedtime_sum'] \
                += phonecall['billedtime_sum']
            phonecall_map[org_name][phonecall['calltype']]['cost_sum'] \
                += phonecall['cost_sum']

            phonecall_map[org_name]['companies'][company_name][phonecall['calltype']] = phonecall
            service_data.setdefault(phonecall['calltype'], {
                'cost_sum': 0.0,
                'count': 0,
                'billedtime_sum': 0,
                'org_price': phonecall['org_price']})

            service_data[phonecall['calltype']]['cost_sum'] += float(phonecall['cost_sum'])
            service_data[phonecall['calltype']]['count'] += phonecall['count']
            service_data[phonecall['calltype']]['billedtime_sum'] += phonecall['billedtime_sum']

            # organization
            phonecall_map[org_name].setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            phonecall_map[org_name].setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            phonecall_map[org_name].setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            # company
            phonecall_map[org_name]['companies'][company_name] \
                .setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            phonecall_map[org_name]['companies'][company_name] \
                .setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            phonecall_map[org_name]['companies'][company_name] \
                .setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            service_data.setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            if phonecall['calltype'] in (LOCAL, VC1, VC2, VC3):
                phonecall_map[org_name][CALL_LOCAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name][CALL_LOCAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name][CALL_LOCAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                service_data[CALL_LOCAL]['count'] += phonecall['count']
                service_data[CALL_LOCAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_LOCAL]['billedtime_sum'] += phonecall['billedtime_sum']
            elif phonecall['calltype'] in (LDN,):
                phonecall_map[org_name][CALL_NATIONAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name][CALL_NATIONAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name][CALL_NATIONAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                service_data[CALL_NATIONAL]['count'] += phonecall['count']
                service_data[CALL_NATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_NATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']
            else:
                phonecall_map[org_name][CALL_INTERNATIONAL]['count'] \
                    += phonecall['count']
                phonecall_map[org_name][CALL_INTERNATIONAL]['cost_sum'] \
                    += float(phonecall['cost_sum'])
                phonecall_map[org_name][CALL_INTERNATIONAL]['billedtime_sum'] \
                    += phonecall['billedtime_sum']

                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['count'] \
                    += phonecall['count']
                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['cost_sum'] \
                    += float(phonecall['cost_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['billedtime_sum'] \
                    += phonecall['billedtime_sum']

                service_data[CALL_INTERNATIONAL]['count'] += phonecall['count']
                service_data[CALL_INTERNATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_INTERNATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']

            phonecall_map[org_name]['count'] += phonecall['count']
            phonecall_map[org_name]['cost_sum'] += float(phonecall['cost_sum'])
            phonecall_map[org_name]['billedtime_sum'] += phonecall['billedtime_sum']

            phonecall_map[org_name]['companies'][company_name]['count'] \
                += phonecall['count']
            phonecall_map[org_name]['companies'][company_name]['cost_sum'] \
                += float(phonecall['cost_sum'])
            phonecall_map[org_name]['companies'][company_name]['billedtime_sum'] \
                += phonecall['billedtime_sum']

            service_data['count'] += phonecall['count']
            service_data['cost_sum'] += float(phonecall['cost_sum'])
            service_data['billedtime_sum'] += phonecall['billedtime_sum']
        phonecall_map[SERVICE] = service_data
        context['phonecall_map'] = phonecall_map
        return context


class AdmPhonecallUSTView(BaseAdmPhonecallView):  # SUPERUSER
    """
    Página com dados do relatório resumido das organizações
    Permissão: Super Usuário
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']
    template_name = 'phonecalls/adm_phonecall_ust.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        phonecall_data = self.object_list \
            .filter(organization__isnull=False,
                    inbound=False,
                    calltype__in=[VC1, VC2, VC3, LOCAL, LDN, LDI]) \
            .values('organization__name', 'company__name', 'calltype') \
            .annotate(count=Count('id'),
                      price_ust=F('org_price') / settings.PRICE_UST,
                      billedtime_sum=Sum('billedtime'),
                      cost_ust_sum=Sum('org_billedamount') / settings.PRICE_UST,
                      cost_sum=Sum('org_billedamount')) \
            .values('organization__name', 'company__name', 'calltype', 'price_ust',
                    'count', 'billedtime_sum', 'cost_sum', 'cost_ust_sum') \
            .order_by('organization__name', 'company__name', 'calltype')

        # constants
        SERVICE = 'SERVIÇOS DE COMUNICAÇÃO'
        CALL_LOCAL = 'local'
        CALL_NATIONAL = 'national'
        CALL_INTERNATIONAL = 'international'
        TOTAL_DICT = {
            'count': 0,
            'cost_sum': 0.0,
            'cost_ust_sum': 0.0,
            'billedtime_sum': 0}

        phonecall_map = {}
        service_data = copy(TOTAL_DICT)
        multiplier, divider = get_values_proportionality(
            date_lt=self.date_lt,
            date_gt=self.date_gt,
            proportionality=context['proportionality'])

        for phonecall in phonecall_data:
            org_name = phonecall['organization__name']
            company_name = phonecall['company__name']

            # organization
            phonecall_map.setdefault(org_name, copy(TOTAL_DICT))
            phonecall_map[org_name].setdefault('companies', {})

            # company
            phonecall_map[org_name]['companies'].setdefault(company_name, copy(TOTAL_DICT))

            organization = Organization.objects.get(name=org_name)
            service_pricetable = organization.settings.service_pricetable
            service_price_list = {}
            if service_pricetable:
                service_price_list = service_pricetable.price_set.active()

            service_basic_price = 0
            service_basic_amount = 0
            service_basic_cost_ust = 0
            service_basic_cost = 0
            services_voip_communication_price = 0
            services_voip_communication_amount = 0
            services_voip_communication_cost_ust = 0
            services_voip_communication_cost = 0
            contact_center_services_price = 0
            contact_center_services_amount = 0
            contact_center_services_cost_ust = 0
            contact_center_services_cost = 0
            for service in service_price_list:
                price_unid_ust = round(float(service.value) / float(settings.PRICE_UST), 4)
                cost_service_ust = price_unid_ust * service.basic_service_amount
                cost = round(float(cost_service_ust) * float(settings.PRICE_UST), 4)

                phonecall_map[org_name].update({
                    BASIC_SERVICE_MAP[service.basic_service]: {
                        'price': price_unid_ust,
                        'amount': service.basic_service_amount,
                        'cost_ust': cost_service_ust,
                        'cost': cost
                    }
                })

                service_basic_price += price_unid_ust
                service_basic_amount += service.basic_service_amount
                service_basic_cost_ust += cost_service_ust
                service_basic_cost += cost

                if service.basic_service in services_voip_communication:
                    services_voip_communication_price += price_unid_ust
                    services_voip_communication_amount += service.basic_service_amount
                    services_voip_communication_cost_ust += cost_service_ust
                    services_voip_communication_cost += cost

                if service.basic_service in contact_center_services:
                    contact_center_services_price += price_unid_ust
                    contact_center_services_amount += service.basic_service_amount
                    contact_center_services_cost_ust += cost_service_ust
                    contact_center_services_cost += cost

            if service_basic_amount != 0 and service_basic_cost != 0:
                phonecall_map[org_name].update({
                    'service_basic': {
                        'price': service_basic_price,
                        'amount': service_basic_amount,
                        'cost_ust': service_basic_cost_ust,
                        'cost': service_basic_cost
                    }
                })
            if services_voip_communication_amount != 0 and services_voip_communication_cost != 0:
                phonecall_map[org_name].update({
                    'services_voip_communication': {
                        'price': services_voip_communication_price,
                        'amount': services_voip_communication_amount,
                        'cost_ust': services_voip_communication_cost_ust,
                        'cost': services_voip_communication_cost
                    }
                })
            if contact_center_services_amount != 0 and contact_center_services_cost != 0:
                phonecall_map[org_name].update({
                    'contact_center_services': {
                        'price': contact_center_services_price,
                        'amount': contact_center_services_amount,
                        'cost_ust': contact_center_services_cost_ust,
                        'cost': contact_center_services_cost
                    }
                })

            phonecall_map[org_name].setdefault(phonecall['calltype'], {
                'organization_name': org_name,
                'company_name': company_name,
                'calltype': phonecall['calltype'],
                'price_ust': phonecall['price_ust'],
                'count': 0,
                'billedtime_sum': 0,
                'cost_ust_sum': 0,
                'cost_sum': 0})
            phonecall_map[org_name][phonecall['calltype']]['count'] \
                += phonecall['count']
            phonecall_map[org_name][phonecall['calltype']]['billedtime_sum'] \
                += phonecall['billedtime_sum']
            phonecall_map[org_name][phonecall['calltype']]['cost_sum'] \
                += phonecall['cost_sum']
            phonecall_map[org_name][phonecall['calltype']]['cost_ust_sum'] \
                += phonecall['cost_ust_sum']

            phonecall_map[org_name]['companies'][company_name][phonecall['calltype']] = phonecall
            service_data.setdefault(phonecall['calltype'], {
                'cost_sum': 0.0,
                'cost_ust_sum': 0.0,
                'count': 0,
                'billedtime_sum': 0,
                'price_ust': phonecall['price_ust']})

            service_data[phonecall['calltype']]['cost_sum'] += float(phonecall['cost_sum'])
            service_data[phonecall['calltype']]['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
            service_data[phonecall['calltype']]['count'] += phonecall['count']
            service_data[phonecall['calltype']]['billedtime_sum'] += phonecall['billedtime_sum']

            # organization
            phonecall_map[org_name].setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            phonecall_map[org_name].setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            phonecall_map[org_name].setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            # company
            phonecall_map[org_name]['companies'][company_name] \
                .setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            phonecall_map[org_name]['companies'][company_name] \
                .setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            phonecall_map[org_name]['companies'][company_name] \
                .setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            service_data.setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            if phonecall['calltype'] in (LOCAL, VC1, VC2, VC3):
                phonecall_map[org_name][CALL_LOCAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name][CALL_LOCAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name][CALL_LOCAL]['cost_ust_sum'] += \
                    float(phonecall['cost_ust_sum'])
                phonecall_map[org_name][CALL_LOCAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['cost_ust_sum'] += \
                    float(phonecall['cost_ust_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                service_data[CALL_LOCAL]['count'] += phonecall['count']
                service_data[CALL_LOCAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_LOCAL]['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
                service_data[CALL_LOCAL]['billedtime_sum'] += phonecall['billedtime_sum']
            elif phonecall['calltype'] in (LDN,):
                phonecall_map[org_name][CALL_NATIONAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name][CALL_NATIONAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name][CALL_NATIONAL]['cost_ust_sum'] += \
                    float(phonecall['cost_ust_sum'])
                phonecall_map[org_name][CALL_NATIONAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['count'] \
                    += phonecall['count']
                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['cost_sum'] \
                    += float(phonecall['cost_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['cost_ust_sum'] \
                    += float(phonecall['cost_ust_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['billedtime_sum'] \
                    += phonecall['billedtime_sum']

                service_data[CALL_NATIONAL]['count'] += phonecall['count']
                service_data[CALL_NATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_NATIONAL]['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
                service_data[CALL_NATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']
            else:
                phonecall_map[org_name][CALL_INTERNATIONAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name][CALL_INTERNATIONAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name][CALL_INTERNATIONAL]['cost_ust_sum'] += \
                    float(phonecall['cost_ust_sum'])
                phonecall_map[org_name][CALL_INTERNATIONAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['cost_ust_sum'] += \
                    float(phonecall['cost_ust_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                service_data[CALL_INTERNATIONAL]['count'] += phonecall['count']
                service_data[CALL_INTERNATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_INTERNATIONAL]['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
                service_data[CALL_INTERNATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']

            phonecall_map[org_name]['count'] += phonecall['count']
            phonecall_map[org_name]['cost_sum'] += float(phonecall['cost_sum'])
            phonecall_map[org_name]['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
            phonecall_map[org_name]['billedtime_sum'] += phonecall['billedtime_sum']

            phonecall_map[org_name]['companies'][company_name]['count'] \
                += phonecall['count']
            phonecall_map[org_name]['companies'][company_name]['cost_sum'] \
                += float(phonecall['cost_sum'])
            phonecall_map[org_name]['companies'][company_name]['cost_ust_sum'] \
                += float(phonecall['cost_ust_sum'])
            phonecall_map[org_name]['companies'][company_name]['billedtime_sum'] \
                += phonecall['billedtime_sum']

            service_data['count'] += phonecall['count']
            service_data['cost_sum'] += float(phonecall['cost_sum'])
            service_data['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
            service_data['billedtime_sum'] += phonecall['billedtime_sum']
        phonecall_map[SERVICE] = service_data
        context['phonecall_map'] = phonecall_map
        return context


class AdmPhonecallCSVReportView(BaseAdmPhonecallView):  # SUPERUSER
    """
    Exportar em CSV relatório detalhado das chamadas
    Permissão: Super usuário
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()
        context = self.get_context_data(filter=self.filterset, object_list=self.object_list)

        filename = self.get_filename(context)

        pseudo_buffer = Echo()
        fieldnames = {
            'CENTRO DE CUSTO':    'company__name',
            'DATA DE INICIO':     'startdate',
            'HORA DE INICIO':     'starttime',
            'DATA DE TÉRMINO':    'stopdate',
            'HORA DE TÉRMINO':    'stoptime',
            'RAMAL':              'extension__extension',
            'NÚMERO COBRADO':     'chargednumber',
            'NÚMERO DISCADO':     'dialednumber',
            'TIPO DE CHAMADA':    'calltype',
            'TIPO DE SERVIÇO':    'service',
            'CLASSIFICAÇÂO PABX': 'pabx',
            'DESCRIÇÂO':          'description',
            'DURAÇÃO':            'billedtime',
            'PREÇO':              'org_price',
            'VALOR FATURADO':     'org_billedamount'
        }
        rows = [fieldnames.keys()]
        phonecall_data = self.object_list.values_list(*fieldnames.values())
        for data in phonecall_data.iterator():
            data = list(data)
            data[8] = CALLTYPE_MAP[data[8]]
            data[9] = SERVICE_MAP[data[9]] if data[9] else ''
            data[10] = PABX_MAP[data[10]] if data[10] else ''
            data[12] = time_format(data[12])
            rows.append(data)

        writer = csv.writer(pseudo_buffer)
        response = StreamingHttpResponse(
            (writer.writerow(row) for row in rows), content_type="text/csv")
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        return response


class AdmPhonecallResumePDFReportView(BaseAdmPhonecallView):  # SUPERUSER
    """
    Exportar em PDF relatório resumido das chamadas das organizações
    Permissão: Super Usuário
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()
        context = self.get_context_data(filter=self.filterset, object_list=self.object_list)

        filename = self.get_filename(resume=True)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachement; filename={filename}.pdf'
        report = SystemReportAdministrador(
            dateBegin=self.date_gt.strftime('%d/%m/%Y'),
            dateEnd=self.date_lt.strftime('%d/%m/%Y'),
            reportTitle='Resumo Geral dos Serviços',
            context=context,
            showCompanies=context['showcompanies'])
        pdf = report.create_table_resume_services(context['phonecall_map'])
        response.write(pdf)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        phonecall_data = self.object_list \
            .filter(organization__isnull=False,
                    inbound=False,
                    calltype__in=[VC1, VC2, VC3, LOCAL, LDN, LDI]) \
            .values('organization__name', 'company__name', 'calltype') \
            .annotate(count=Count('id'),
                      billedtime_sum=Sum('billedtime'),
                      cost_sum=Sum('org_billedamount')) \
            .values('organization__name', 'company__name', 'calltype', 'org_price',
                    'count', 'billedtime_sum', 'cost_sum') \
            .order_by('organization__name', 'company__name', 'calltype')

        # constants
        SERVICE = 'SERVIÇOS DE COMUNICAÇÃO'
        CALL_LOCAL = 'local'
        CALL_NATIONAL = 'national'
        CALL_INTERNATIONAL = 'international'
        TOTAL_DICT = {
            'count': 0,
            'cost_sum': 0.0,
            'billedtime_sum': 0}

        phonecall_map = {}
        service_data = copy(TOTAL_DICT)
        multiplier, divider = get_values_proportionality(
            date_lt=self.date_lt,
            date_gt=self.date_gt,
            proportionality=context['proportionality'])

        for phonecall in phonecall_data:
            org_name = phonecall['organization__name']
            company_name = phonecall['company__name']

            # organization
            phonecall_map.setdefault(org_name, copy(TOTAL_DICT))
            phonecall_map[org_name].setdefault('companies', {})

            # company
            phonecall_map[org_name]['companies'] \
                .setdefault(company_name, copy(TOTAL_DICT))
            # service_data.setdefault(org_name, copy(TOTAL_DICT))

            organization = Organization.objects.get(name=org_name)
            service_pricetable = organization.settings.service_pricetable
            service_price_list = {}
            if service_pricetable:
                service_price_list = service_pricetable.price_set.active()

            service_basic_amount = 0
            service_basic_cost = 0
            for service in service_price_list:
                cost = ((service.basic_service_amount * service.value) / divider) * multiplier
                phonecall_map[org_name].update({
                    BASIC_SERVICE_MAP[service.basic_service]: {
                        'price': service.value,
                        'amount': service.basic_service_amount,
                        'cost': cost
                    }
                })
                service_basic_amount += service.basic_service_amount
                service_basic_cost += cost

            if service_basic_amount != 0 and service_basic_cost != 0:
                phonecall_map[org_name].update({
                    'service_basic': {
                        'amount': service_basic_amount,
                        'cost': service_basic_cost
                    }
                })

            phonecall_map[org_name].setdefault(phonecall['calltype'], {
                'organization_name': org_name,
                'company_name': company_name,
                'calltype': phonecall['calltype'],
                'org_price': phonecall['org_price'],
                'count': 0,
                'billedtime_sum': 0,
                'cost_sum': 0})

            phonecall_map[org_name][phonecall['calltype']]['count'] \
                += phonecall['count']
            phonecall_map[org_name][phonecall['calltype']]['billedtime_sum'] \
                += phonecall['billedtime_sum']
            phonecall_map[org_name][phonecall['calltype']]['cost_sum'] \
                += phonecall['cost_sum']

            phonecall_map[org_name]['companies'][company_name][phonecall['calltype']] = phonecall
            service_data.setdefault(phonecall['calltype'], {
                'cost_sum': 0.0,
                'count': 0,
                'billedtime_sum': 0,
                'org_price': phonecall['org_price']})

            service_data[phonecall['calltype']]['cost_sum'] += float(phonecall['cost_sum'])
            service_data[phonecall['calltype']]['count'] += phonecall['count']
            service_data[phonecall['calltype']]['billedtime_sum'] += phonecall['billedtime_sum']

            # organization
            phonecall_map[org_name].setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            phonecall_map[org_name].setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            phonecall_map[org_name].setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            # company
            phonecall_map[org_name]['companies'][company_name] \
                .setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            phonecall_map[org_name]['companies'][company_name] \
                .setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            phonecall_map[org_name]['companies'][company_name] \
                .setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            service_data.setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            if phonecall['calltype'] in (LOCAL, VC1, VC2, VC3):
                phonecall_map[org_name][CALL_LOCAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name][CALL_LOCAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name][CALL_LOCAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                service_data[CALL_LOCAL]['count'] += phonecall['count']
                service_data[CALL_LOCAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_LOCAL]['billedtime_sum'] += phonecall['billedtime_sum']
            elif phonecall['calltype'] in (LDN,):
                phonecall_map[org_name][CALL_NATIONAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name][CALL_NATIONAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name][CALL_NATIONAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['count'] \
                    += phonecall['count']
                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['cost_sum'] \
                    += float(phonecall['cost_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['billedtime_sum'] \
                    += phonecall['billedtime_sum']

                service_data[CALL_NATIONAL]['count'] += phonecall['count']
                service_data[CALL_NATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_NATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']
            else:
                phonecall_map[org_name][CALL_INTERNATIONAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name][CALL_INTERNATIONAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name][CALL_INTERNATIONAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['count'] \
                    += phonecall['count']
                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['cost_sum'] \
                    += float(phonecall['cost_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['billedtime_sum'] \
                    += phonecall['billedtime_sum']

                service_data[CALL_INTERNATIONAL]['count'] += phonecall['count']
                service_data[CALL_INTERNATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_INTERNATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']

            phonecall_map[org_name]['count'] += phonecall['count']
            phonecall_map[org_name]['cost_sum'] += float(phonecall['cost_sum'])
            phonecall_map[org_name]['billedtime_sum'] += phonecall['billedtime_sum']

            phonecall_map[org_name]['companies'][company_name]['count'] \
                += phonecall['count']
            phonecall_map[org_name]['companies'][company_name]['cost_sum'] \
                += float(phonecall['cost_sum'])
            phonecall_map[org_name]['companies'][company_name]['billedtime_sum'] \
                += phonecall['billedtime_sum']

            service_data['count'] += phonecall['count']
            service_data['cost_sum'] += float(phonecall['cost_sum'])
            service_data['billedtime_sum'] += phonecall['billedtime_sum']
        phonecall_map[SERVICE] = service_data
        context['phonecall_map'] = phonecall_map
        return context


class AdmPhonecallUSTPDFReportView(BaseAdmPhonecallView):  # SUPERUSER
    """
    Exportar em PDF relatório resumido das chamadas das organizações
    Permissão: Super Usuário
    """

    context_object_name = 'phonecall_list'
    filterset_class = PhonecallFilter
    http_method_names = ['get']
    model = Phonecall
    ordering = ['-startdate', '-starttime']

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()
        context = self.get_context_data(filter=self.filterset, object_list=self.object_list)

        filename = self.get_filename(resume=True)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachement; filename={filename}.pdf'
        report = SystemReportAdministrador(
            dateBegin=self.date_gt.strftime('%d/%m/%Y'),
            dateEnd=self.date_lt.strftime('%d/%m/%Y'),
            reportTitle='Relatório Execução dos Serviços em UST',
            context=context,
            ust=True)
        pdf = report.create_table_ust_services(context['phonecall_map'])
        response.write(pdf)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        phonecall_data = self.object_list \
            .filter(organization__isnull=False,
                    inbound=False,
                    calltype__in=[VC1, VC2, VC3, LOCAL, LDN, LDI]) \
            .values('organization__name', 'company__name', 'calltype') \
            .annotate(count=Count('id'),
                      price_ust=F('org_price') / settings.PRICE_UST,
                      billedtime_sum=Sum('billedtime'),
                      cost_ust_sum=Sum('org_billedamount') / settings.PRICE_UST,
                      cost_sum=Sum('org_billedamount')) \
            .values('organization__name', 'company__name', 'calltype', 'price_ust',
                    'count', 'billedtime_sum', 'cost_sum', 'cost_ust_sum') \
            .order_by('organization__name', 'company__name', 'calltype')

        # constants
        SERVICE = 'SERVIÇOS DE COMUNICAÇÃO'
        CALL_LOCAL = 'local'
        CALL_NATIONAL = 'national'
        CALL_INTERNATIONAL = 'international'
        TOTAL_DICT = {
            'count': 0,
            'cost_sum': 0.0,
            'cost_ust_sum': 0.0,
            'billedtime_sum': 0}

        phonecall_map = {}
        service_data = copy(TOTAL_DICT)
        multiplier, divider = get_values_proportionality(
            date_lt=self.date_lt,
            date_gt=self.date_gt,
            proportionality=context['proportionality'])

        for phonecall in phonecall_data:
            org_name = phonecall['organization__name']
            company_name = phonecall['company__name']

            # organization
            phonecall_map.setdefault(org_name, copy(TOTAL_DICT))
            phonecall_map[org_name].setdefault('companies', {})

            # company
            phonecall_map[org_name]['companies'].setdefault(company_name, copy(TOTAL_DICT))

            organization = Organization.objects.get(name=org_name)
            service_pricetable = organization.settings.service_pricetable
            service_price_list = {}
            if service_pricetable:
                service_price_list = service_pricetable.price_set.active()

            service_basic_price = 0
            service_basic_amount = 0
            service_basic_cost_ust = 0
            service_basic_cost = 0
            services_voip_communication_price = 0
            services_voip_communication_amount = 0
            services_voip_communication_cost_ust = 0
            services_voip_communication_cost = 0
            contact_center_services_price = 0
            contact_center_services_amount = 0
            contact_center_services_cost_ust = 0
            contact_center_services_cost = 0
            for service in service_price_list:
                price_unid_ust = round(float(service.value) / float(settings.PRICE_UST), 4)
                cost_service_ust = price_unid_ust * service.basic_service_amount
                cost = round(float(cost_service_ust) * float(settings.PRICE_UST), 4)

                phonecall_map[org_name].update({
                    BASIC_SERVICE_MAP[service.basic_service]: {
                        'price': price_unid_ust,
                        'amount': service.basic_service_amount,
                        'cost_ust': cost_service_ust,
                        'cost': cost
                    }
                })

                service_basic_price += price_unid_ust
                service_basic_amount += service.basic_service_amount
                service_basic_cost_ust += cost_service_ust
                service_basic_cost += cost

                if service.basic_service in services_voip_communication:
                    services_voip_communication_price += price_unid_ust
                    services_voip_communication_amount += service.basic_service_amount
                    services_voip_communication_cost_ust += cost_service_ust
                    services_voip_communication_cost += cost

                if service.basic_service in contact_center_services:
                    contact_center_services_price += price_unid_ust
                    contact_center_services_amount += service.basic_service_amount
                    contact_center_services_cost_ust += cost_service_ust
                    contact_center_services_cost += cost

            if service_basic_amount != 0 and service_basic_cost != 0:
                phonecall_map[org_name].update({
                    'service_basic': {
                        'price': service_basic_price,
                        'amount': service_basic_amount,
                        'cost_ust': service_basic_cost_ust,
                        'cost': service_basic_cost
                    }
                })
            if services_voip_communication_amount != 0 and services_voip_communication_cost != 0:
                phonecall_map[org_name].update({
                    'services_voip_communication': {
                        'price': services_voip_communication_price,
                        'amount': services_voip_communication_amount,
                        'cost_ust': services_voip_communication_cost_ust,
                        'cost': services_voip_communication_cost
                    }
                })
            if contact_center_services_amount != 0 and contact_center_services_cost != 0:
                phonecall_map[org_name].update({
                    'contact_center_services': {
                        'price': contact_center_services_price,
                        'amount': contact_center_services_amount,
                        'cost_ust': contact_center_services_cost_ust,
                        'cost': contact_center_services_cost
                    }
                })

            phonecall_map[org_name].setdefault(phonecall['calltype'], {
                'organization_name': org_name,
                'company_name': company_name,
                'calltype': phonecall['calltype'],
                'price_ust': phonecall['price_ust'],
                'count': 0,
                'billedtime_sum': 0,
                'cost_ust_sum': 0,
                'cost_sum': 0})
            phonecall_map[org_name][phonecall['calltype']]['count'] \
                += phonecall['count']
            phonecall_map[org_name][phonecall['calltype']]['billedtime_sum'] \
                += phonecall['billedtime_sum']
            phonecall_map[org_name][phonecall['calltype']]['cost_sum'] \
                += phonecall['cost_sum']
            phonecall_map[org_name][phonecall['calltype']]['cost_ust_sum'] \
                += phonecall['cost_ust_sum']

            phonecall_map[org_name]['companies'][company_name][phonecall['calltype']] = phonecall
            service_data.setdefault(phonecall['calltype'], {
                'cost_sum': 0.0,
                'cost_ust_sum': 0.0,
                'count': 0,
                'billedtime_sum': 0,
                'price_ust': phonecall['price_ust']})

            service_data[phonecall['calltype']]['cost_sum'] += float(phonecall['cost_sum'])
            service_data[phonecall['calltype']]['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
            service_data[phonecall['calltype']]['count'] += phonecall['count']
            service_data[phonecall['calltype']]['billedtime_sum'] += phonecall['billedtime_sum']

            # organization
            phonecall_map[org_name].setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            phonecall_map[org_name].setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            phonecall_map[org_name].setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            # company
            phonecall_map[org_name]['companies'][company_name] \
                .setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            phonecall_map[org_name]['companies'][company_name] \
                .setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            phonecall_map[org_name]['companies'][company_name] \
                .setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            service_data.setdefault(CALL_LOCAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
            service_data.setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))

            if phonecall['calltype'] in (LOCAL, VC1, VC2, VC3):
                phonecall_map[org_name][CALL_LOCAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name][CALL_LOCAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name][CALL_LOCAL]['cost_ust_sum'] += \
                    float(phonecall['cost_ust_sum'])
                phonecall_map[org_name][CALL_LOCAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['cost_ust_sum'] += \
                    float(phonecall['cost_ust_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_LOCAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                service_data[CALL_LOCAL]['count'] += phonecall['count']
                service_data[CALL_LOCAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_LOCAL]['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
                service_data[CALL_LOCAL]['billedtime_sum'] += phonecall['billedtime_sum']
            elif phonecall['calltype'] in (LDN,):
                phonecall_map[org_name][CALL_NATIONAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name][CALL_NATIONAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name][CALL_NATIONAL]['cost_ust_sum'] += \
                    float(phonecall['cost_ust_sum'])
                phonecall_map[org_name][CALL_NATIONAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['count'] \
                    += phonecall['count']
                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['cost_sum'] \
                    += float(phonecall['cost_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['cost_ust_sum'] \
                    += float(phonecall['cost_ust_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_NATIONAL]['billedtime_sum'] \
                    += phonecall['billedtime_sum']

                service_data[CALL_NATIONAL]['count'] += phonecall['count']
                service_data[CALL_NATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_NATIONAL]['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
                service_data[CALL_NATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']
            else:
                phonecall_map[org_name][CALL_INTERNATIONAL]['count'] += \
                    phonecall['count']
                phonecall_map[org_name][CALL_INTERNATIONAL]['cost_sum'] += \
                    float(phonecall['cost_sum'])
                phonecall_map[org_name][CALL_INTERNATIONAL]['cost_ust_sum'] += \
                    float(phonecall['cost_ust_sum'])
                phonecall_map[org_name][CALL_INTERNATIONAL]['billedtime_sum'] += \
                    phonecall['billedtime_sum']

                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['count'] \
                    += phonecall['count']
                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['cost_sum'] \
                    += float(phonecall['cost_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['cost_ust_sum'] \
                    += float(phonecall['cost_ust_sum'])
                phonecall_map[org_name]['companies'][company_name][CALL_INTERNATIONAL]['billedtime_sum'] \
                    += phonecall['billedtime_sum']

                service_data[CALL_INTERNATIONAL]['count'] += phonecall['count']
                service_data[CALL_INTERNATIONAL]['cost_sum'] += float(phonecall['cost_sum'])
                service_data[CALL_INTERNATIONAL]['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
                service_data[CALL_INTERNATIONAL]['billedtime_sum'] += phonecall['billedtime_sum']

            phonecall_map[org_name]['count'] += phonecall['count']
            phonecall_map[org_name]['cost_sum'] += float(phonecall['cost_sum'])
            phonecall_map[org_name]['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
            phonecall_map[org_name]['billedtime_sum'] += phonecall['billedtime_sum']

            phonecall_map[org_name]['companies'][company_name]['count'] \
                += phonecall['count']
            phonecall_map[org_name]['companies'][company_name]['cost_sum'] \
                += float(phonecall['cost_sum'])
            phonecall_map[org_name]['companies'][company_name]['cost_ust_sum'] \
                += float(phonecall['cost_ust_sum'])
            phonecall_map[org_name]['companies'][company_name]['billedtime_sum'] \
                += phonecall['billedtime_sum']

            service_data['count'] += phonecall['count']
            service_data['cost_sum'] += float(phonecall['cost_sum'])
            service_data['cost_ust_sum'] += float(phonecall['cost_ust_sum'])
            service_data['billedtime_sum'] += phonecall['billedtime_sum']
        phonecall_map[SERVICE] = service_data
        context['phonecall_map'] = phonecall_map
        return context
