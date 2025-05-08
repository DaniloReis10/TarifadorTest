# python
import csv
import urllib

from copy import copy
from datetime import date
from datetime import datetime, timedelta
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from zipfile import ZipFile
from io import BytesIO
# django
from django.conf import settings
from django.db.models import Count, Sum
from django.db.models import F, FloatField, ExpressionWrapper, Q
from django.http import Http404
from django.http import HttpResponse
from django.http import StreamingHttpResponse
from django.views.generic import ListView
from django.views.generic.base import RedirectView
from django.urls import reverse

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
from charges.constants import PRICE_FIELDS_BASIC_SERVICE_MAP_PMF
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
from Equipments.models import Equipment

# local
from .constants import CALLTYPE_CHOICES, REPORT_CALLTYPE_MAP
from .constants import DDD_CHOICES
from .constants import PABX_CHOICES
from .constants import SERVICE_CHOICES
from .constants import VC1, VC2, VC3, LOCAL, LDN, LDI
from .filters import PhonecallFilter
from .models import Phonecall
from .constants import OLD_CONTRACT,  NEW_CONTRACT

from phonecalls.models import Price, PriceTable

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

class BaseContextData():

    def get_Company_Context(self, phonecall_data):
        phonecall_total = 0
        duration_total = 0
        cost_total = 0.0
        phonecall_local = []
        phonecall_long_distance = []
        # The descending order will list VC3, VC2 and VC1 so I can do this
        total_mobile_count = 0
        total_mobile_billedtime_sum = 0
        for phonecall in phonecall_data:
            #AGAIN THIS NEEDS TO BE SET RIGHT
            if(phonecall['company__organization_id']==2 and phonecall['calltype'] in (VC2, VC3)):
                price = Price.objects.all().filter(table_id=phonecall['company__call_pricetable'],
                                                   calltype=VC1).active().values('value')
            else:
                price = Price.objects.all().filter(table_id=phonecall['company__call_pricetable'],
                                               calltype=phonecall['calltype']).active().values('value')
            phonecall['price'] = price.first()['value']
            if (phonecall['company__organization_id']==2 or phonecall['company__is_new_contract']) and phonecall['calltype'] in (VC2, VC3):
                total_mobile_count += phonecall['count']
                total_mobile_billedtime_sum += phonecall['billedtime_sum']
                phonecall['count'] = 0
                phonecall['billedtime_sum'] = 0
            elif (phonecall['company__organization_id']==2 or phonecall['company__is_new_contract']) and phonecall['calltype'] == VC1:
                phonecall['count'] += total_mobile_count
                phonecall['billedtime_sum'] += total_mobile_billedtime_sum
            phonecall['cost_sum'] = phonecall['billedtime_sum'] * phonecall['price'] / 60
            if phonecall['calltype'] in (VC1, LOCAL):
                phonecall_local.append(phonecall)
            elif phonecall['calltype'] in (VC2, VC3, LDN):
                phonecall_long_distance.append(phonecall)
            else:
                continue
            phonecall_total += phonecall['count']
            duration_total += phonecall['billedtime_sum']
            cost_total += float(phonecall['cost_sum'])

#        multiplier, divider = get_values_proportionality(
#            date_lt=self.date_lt,
#            date_gt=self.date_gt,
#            proportionality=context['proportionality'])

        service_pricetable = self.company.service_pricetable
        service_price_list = {}
        if service_pricetable:
            service_price_list = service_pricetable.price_set.active()

        service_basic_amount = 0
        service_basic_cost = 0
        basicservice = {}
        for service in service_price_list:
            service_cost = service.basic_service_amount * service.value
#            service_cost = (service_cost / divider) * multiplier
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
        company_context = {}
        company_context.update({
            'phonecall_local': phonecall_local,
            'phonecall_long_distance': phonecall_long_distance,
            'phonecall_total': phonecall_total,
            'cost_total': cost_total,
            'basic_service': basicservice,
            'prop': {},
            'duration_total': duration_total})
        return company_context

    def get_Org_Context(self):


        phonecall_data = self.object_list \
            .filter(company__isnull=False,
                    inbound=False,
                    calltype__in=[VC1, VC2, VC3, LOCAL, LDN, LDI]) \
            .values('company__name', 'calltype') \
            .annotate(count=Count('id'),
                      billedtime_sum=Sum('billedtime'),
                      cost_sum=Sum('billedamount') )\
            .values('company__name', 'company__is_new_contract', 'calltype', 'price', 'company__call_pricetable', 'company__organization_id',
                    'count', 'billedtime_sum', 'cost_sum') \
            .order_by('company__name', '-calltype')
        result_companies = {}
        company_list = Company.objects.filter(organization=self.organization).active()
        companies_phonedata = phonecall_data.values_list('company__name', flat=True)
        for company in company_list:
        #for company__name in phonecall_data:
            #if company.name in companies_phonedata:
            #if company.active():
                self.company = company
                sub_phonecall_data = self.get_Company_Context(phonecall_data.filter(company__name=company.name))
                sub_phonecall_data.update({'contract_version': company.is_new_contract})
                result_companies.update({company.name:sub_phonecall_data})

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
        service_data.update({'contract_version': NEW_CONTRACT})
#        multiplier, divider = get_values_proportionality(
#            date_lt=self.date_lt,
#            date_gt=self.date_gt,
#            proportionality=context['proportionality'])
        # Fix VC1 + VC2 + VC3
        new_contract_mobile = self.object_list \
            .filter(company__isnull=False,
                    inbound=False,
                    calltype__in=[VC1, VC2, VC3],
                    company__is_new_contract = NEW_CONTRACT) \
            .values('company__name') \
            .annotate(count=Count('id'),
                      billedtime_sum=Sum('billedtime'),
                      cost_sum=Sum('billedamount') )\
            .values('company__name',
                    'count', 'billedtime_sum', 'cost_sum') \
            .order_by('company__name')
        new_contract_list = new_contract_mobile.values_list('company__name', flat = True)
        service_data.setdefault(VC1, {
            'cost_sum': 0.0,
            'count': 0,
            'billedtime_sum': 0,
            'price': 0})
        service_data.setdefault(VC2, {
            'cost_sum': 0.0,
            'count': 0,
            'billedtime_sum': 0,
            'price': 0})
        service_data.setdefault(VC3, {
            'cost_sum': 0.0,
            'count': 0,
            'billedtime_sum': 0,
            'price': 0})
        service_data.setdefault(LOCAL, {
            'cost_sum': 0.0,
            'count': 0,
            'billedtime_sum': 0,
            'price': 0})
        service_data.setdefault(LDN, {
            'cost_sum': 0.0,
            'count': 0,
            'billedtime_sum': 0,
            'price': 0})
        service_data.setdefault(LDI, {
            'cost_sum': 0.0,
            'count': 0,
            'billedtime_sum': 0,
            'price': 0})
        service_data.setdefault(CALL_LOCAL, copy(TOTAL_DICT))
        service_data.setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
        service_data.setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))
        service_data[VC1]['price'] = Price.objects.all().filter(table_id=PriceTable.objects.get(name = "Valores Base ETICE").id,
                                           calltype=VC1).active().values('value').first()['value']
        service_data[LOCAL]['price'] = \
        Price.objects.all().filter(table_id=PriceTable.objects.get(name="Valores Base ETICE").id,
                                   calltype=LOCAL).active().values('value').first()['value']
        service_data[LDN]['price'] = \
        Price.objects.all().filter(table_id=PriceTable.objects.get(name="Valores Base ETICE").id,
                                   calltype=LDN).active().values('value').first()['value']
        service_data[LDI]['price'] = \
            Price.objects.all().filter(table_id=PriceTable.objects.get(name="Valores Base ETICE").id,
                                       calltype=LDI).active().values('value').first()['value']
        for phonecall in phonecall_data:
            company_name = phonecall['company__name']
            if (company_name in new_contract_list):
                for company_info in new_contract_mobile:
                    # For a company with new contract VC1 is the summ of all mobile and VC2 = VC3 = 0
                    if company_info['company__name'] == company_name and phonecall['calltype'] == VC1:
                        phonecall['count'] = company_info['count']
                        phonecall['billedtime_sum'] = company_info['billedtime_sum']
                    elif company_info['company__name'] == company_name and phonecall['calltype'] in (VC2, VC3):
                        phonecall['count'] = 0
                        phonecall['billedtime_sum'] = 0
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
                if company_name not in new_contract_list or phonecall['calltype'] not in (VC2, VC3):
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
                #service_cost = (service_cost / divider) * multiplier

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

        service_data[VC1]['count'] += service_data[VC2]['count'] + service_data[VC3]['count']
        service_data[VC1]['billedtime_sum'] += service_data[VC2]['billedtime_sum'] + service_data[VC3]['billedtime_sum']
        service_data[VC1]['cost_sum'] = service_data[VC1]['billedtime_sum'] * service_data[VC1]['price'] / 60
        service_data[LOCAL]['cost_sum'] = service_data[LOCAL]['billedtime_sum'] * service_data[LOCAL]['price'] /60
        service_data[LDN]['cost_sum'] = service_data[LDN]['billedtime_sum'] * service_data[LDN]['price'] / 60
        service_data[LDI]['cost_sum'] = service_data[LDI]['billedtime_sum'] * service_data[LDI]['price'] / 60
        service_data[CALL_LOCAL]['cost_sum'] = service_data[VC1]['cost_sum'] + service_data[LOCAL]['cost_sum']
        service_data[CALL_NATIONAL]['cost_sum'] = service_data[LDN]['cost_sum']
        service_data[CALL_INTERNATIONAL]['cost_sum'] = service_data[LDI]['cost_sum']
        service_data['cost_sum'] = service_data[CALL_LOCAL]['cost_sum'] + service_data[CALL_NATIONAL]['cost_sum'] + service_data[LDI]['cost_sum']
        phonecall_map[SERVICE] = service_data
        org_context = {}
        org_context.update({
            'phonecall_map': phonecall_map,
            'new_contract': NEW_CONTRACT,
            'old_contract': OLD_CONTRACT,
            'company': result_companies})

        return org_context

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

    """
        Someth
        """
    def get_queryset(self):
        if self.request.GET.get('date_gt') is not None:
            self.date_gt = datetime.strptime( self.request.GET.get('date_gt'), '%Y-%m-%d').date()
            self.date_lt = datetime.strptime(self.request.GET.get('date_lt'), '%Y-%m-%d').date()
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

# In this (admin case) the fixing of the date from the get to here is happening here
    def dispatch(self, request, *args, **kwargs):
        self.params = {key: value for key, value in self.request.GET.items() if key != 'page' and value}
        self.date_gt, self.date_lt = get_range_date(self.request.GET)
        if self.date_gt is None or self.date_lt is None:
            self.date_lt = date.today()
            self.date_gt = date(self.date_lt.year, self.date_lt.month, 1)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.request.GET.get('date_gt') is not None:
            self.date_gt = datetime.strptime( self.request.GET.get('date_gt'), '%Y-%m-%d').date()
            self.date_lt = datetime.strptime(self.request.GET.get('date_lt'), '%Y-%m-%d').date()
        if self.request.POST.get('date_gt') is not None:
            self.date_gt = datetime.strptime( self.request.POST.get('date_gt'), '%Y-%m-%d').date()
            self.date_lt = datetime.strptime(self.request.POST.get('date_lt'), '%Y-%m-%d').date()
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


class CompanyPhonecallResumeView(BaseCompanyPhonecallView, BaseContextData):  # COMPANY
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
            .values( 'company__is_new_contract', 'calltype', 'price', 'company__call_pricetable', 'company__organization_id',
                    'count', 'billedtime_sum', 'cost_sum')\
            .order_by('-calltype')
        context_info = super().get_Company_Context(phonecall_data)
        context.update(context_info)
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
                    'chargednumber', 'dialednumber', 'calltype', 'duration', 'billedtime', 'billedamount')

        phonecall_data = {}
        for phonecall in phonecall_values:
            extension = phonecall['extension__extension']
            price = Price.objects.get(Q(status=1) & \
                                      Q(table=self.company.call_pricetable) & \
                                      Q(calltype=phonecall['calltype']))
            phonecall['billedamount'] = phonecall['billedtime'] * price.value / 60
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
            .values('company__is_new_contract', 'calltype', 'price', 'company__call_pricetable',
                    'count', 'billedtime_sum', 'cost_sum') \
            .order_by('-calltype')

        phonecall_total = 0
        duration_total = 0
        cost_total = 0.0
        phonecall_local = []
        phonecall_long_distance = []
        total_mobile_count = 0
        total_mobile_billedtime_sum = 0
        contract_version = OLD_CONTRACT
        teste = list(phonecall_data)
        for phonecall in phonecall_data:
            price = Price.objects.all().filter(table_id=phonecall['company__call_pricetable'],
                                               calltype=phonecall['calltype']).active().values('value')
            phonecall['price'] = price.first()['value']
            contract_version = phonecall['company__is_new_contract']
            if phonecall['company__is_new_contract'] and phonecall['calltype'] in (VC2,VC3):
                total_mobile_count += phonecall['count']
                total_mobile_billedtime_sum += phonecall['billedtime_sum']
                phonecall['count'] = 0
                phonecall['billedtime_sum'] = 0
            elif phonecall['company__is_new_contract'] and phonecall['calltype'] == VC1:
                phonecall['count'] += total_mobile_count
                phonecall['billedtime_sum'] += total_mobile_billedtime_sum
            phonecall['cost_sum'] = phonecall['billedtime_sum'] * phonecall['price'] / 60
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
            'contract_version': contract_version,
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
            .values('company__name', 'calltype', 'price', 'company__call_pricetable', 'company__organization_id',
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
        service_data.update({'contract_version': NEW_CONTRACT})
        multiplier, divider = get_values_proportionality(
            date_lt=self.date_lt,
            date_gt=self.date_gt,
            proportionality=context['proportionality'])
        # Fix VC1 + VC2 + VC3
        new_contract_mobile = self.object_list \
            .filter(company__isnull=False,
                    inbound=False,
                    calltype__in=[VC1, VC2, VC3],
                    company__is_new_contract = NEW_CONTRACT) \
            .values('company__name') \
            .annotate(count=Count('id'),
                      billedtime_sum=Sum('billedtime'),
                      cost_sum=Sum('billedamount') )\
            .values('company__name',
                    'count', 'billedtime_sum', 'cost_sum') \
            .order_by('company__name')
        new_contract_list = new_contract_mobile.values_list('company__name', flat = True)
        service_data.setdefault(VC1, {
            'cost_sum': 0.0,
            'count': 0,
            'billedtime_sum': 0,
            'price': 0})
        service_data.setdefault(VC2, {
            'cost_sum': 0.0,
            'count': 0,
            'billedtime_sum': 0,
            'price': 0})
        service_data.setdefault(VC3, {
            'cost_sum': 0.0,
            'count': 0,
            'billedtime_sum': 0,
            'price': 0})
        service_data.setdefault(LOCAL, {
            'cost_sum': 0.0,
            'count': 0,
            'billedtime_sum': 0,
            'price': 0})
        service_data.setdefault(LDN, {
            'cost_sum': 0.0,
            'count': 0,
            'billedtime_sum': 0,
            'price': 0})
        service_data.setdefault(LDI, {
            'cost_sum': 0.0,
            'count': 0,
            'billedtime_sum': 0,
            'price': 0})
        service_data.setdefault(CALL_LOCAL, copy(TOTAL_DICT))
        service_data.setdefault(CALL_NATIONAL, copy(TOTAL_DICT))
        service_data.setdefault(CALL_INTERNATIONAL, copy(TOTAL_DICT))
        service_data[VC1]['price'] = Price.objects.all().filter(table_id=PriceTable.objects.get(name = "Valores Base ETICE").id,
                                           calltype=VC1).active().values('value').first()['value']
        service_data[LOCAL]['price'] = \
        Price.objects.all().filter(table_id=PriceTable.objects.get(name="Valores Base ETICE").id,
                                   calltype=LOCAL).active().values('value').first()['value']
        service_data[LDN]['price'] = \
        Price.objects.all().filter(table_id=PriceTable.objects.get(name="Valores Base ETICE").id,
                                   calltype=LDN).active().values('value').first()['value']
        service_data[LDI]['price'] = \
            Price.objects.all().filter(table_id=PriceTable.objects.get(name="Valores Base ETICE").id,
                                       calltype=LDI).active().values('value').first()['value']
        for phonecall in phonecall_data:
            company_name = phonecall['company__name']
            if (company_name in new_contract_list):
                for company_info in new_contract_mobile:
                    # For a company with new contract VC1 is the summ of all mobile and VC2 = VC3 = 0
                    if company_info['company__name'] == company_name and phonecall['calltype'] == VC1:
                        phonecall['count'] = company_info['count']
                        phonecall['billedtime_sum'] = company_info['billedtime_sum']
                    elif company_info['company__name'] == company_name and phonecall['calltype'] in (VC2, VC3):
                        phonecall['count'] = 0
                        phonecall['billedtime_sum'] = 0
            # AGAIN THIS NEEDS TO BE SET RIGHT
            if (phonecall['company__organization_id'] == 2 and phonecall['calltype'] in (VC2, VC3)):
                price = Price.objects.all().filter(table_id=phonecall['company__call_pricetable'],
                                                               calltype=VC1).active().values('value')
            else:
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
                if company_name not in new_contract_list or phonecall['calltype'] not in (VC2, VC3):
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

        service_data[VC1]['count'] += service_data[VC2]['count'] + service_data[VC3]['count']
        service_data[VC1]['billedtime_sum'] += service_data[VC2]['billedtime_sum'] + service_data[VC3]['billedtime_sum']
        service_data[VC1]['cost_sum'] = service_data[VC1]['billedtime_sum'] * service_data[VC1]['price'] / 60
        service_data[LOCAL]['cost_sum'] = service_data[LOCAL]['billedtime_sum'] * service_data[LOCAL]['price'] /60
        service_data[LDN]['cost_sum'] = service_data[LDN]['billedtime_sum'] * service_data[LDN]['price'] / 60
        service_data[LDI]['cost_sum'] = service_data[LDI]['billedtime_sum'] * service_data[LDI]['price'] / 60
        service_data[CALL_LOCAL]['cost_sum'] = service_data[VC1]['cost_sum'] + service_data[LOCAL]['cost_sum']
        service_data[CALL_NATIONAL]['cost_sum'] = service_data[LDN]['cost_sum']
        service_data[CALL_INTERNATIONAL]['cost_sum'] = service_data[LDI]['cost_sum']
        service_data['cost_sum'] = service_data[CALL_LOCAL]['cost_sum'] + service_data[CALL_NATIONAL]['cost_sum'] + service_data[LDI]['cost_sum']
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
            .values('company__name', 'company__description', 'calltype', 'company__organization_id',
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
        phonecall = phonecall_data[0]
        if phonecall['company__organization_id'] == 2:
            basic_services = PRICE_FIELDS_BASIC_SERVICE_MAP_PMF
        else:
            basic_services = BASIC_SERVICE_MAP
        for key, value in basic_services.items():
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
                if basic_services[service.basic_service] not in phonecall_map[company.name]:
                    service_cost = service.basic_service_amount * service.value
                    service_cost = (service_cost / divider) * multiplier
                    phonecall_map[company.name].setdefault(
                        basic_services[service.basic_service], {
                            'price': service.value,
                            'amount': service.basic_service_amount,
                            'cost': service_cost})
                    # Now for each level_6 service (DECT phone without a base) we need to add a base
                    if basic_services[service.basic_service] == 'LEVEL_6_ACCESS_SERVICE' and company.is_new_contract == OLD_CONTRACT:
                        service_basic_total[basic_services[WIRELESS_ACCESS_SERVICE]]['amount'] += \
                            service.basic_service_amount
                        service_basic_total[basic_services[WIRELESS_ACCESS_SERVICE]]['cost'] += \
                            service_cost
                    elif basic_services[service.basic_service] != 'WIRELESS_ACCESS_SERVICE' or company.is_new_contract == NEW_CONTRACT:
                        service_basic_total[basic_services[service.basic_service]]['amount'] += \
                            service.basic_service_amount
                        service_basic_total[basic_services[service.basic_service]]['cost'] += \
                            service_cost
                    service_basic_amount += service.basic_service_amount
                    service_basic_cost += service_cost

            if service_basic_amount != 0 and service_basic_cost != 0:
                phonecall_map[company.name].setdefault('service_basic', {
                    'amount': service_basic_amount,
                    'cost': service_basic_cost})

        phonecall_map[SERVICE_BASIC] = service_basic_total
        phonecall_map[SERVICE] = service_data
        phonecall_map['ORGANIZATION'] = self.organization.name
        phonecall_map['ORGANIZATION_id'] = self.organization.id
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

            call_pricetable = organization.settings.call_pricetable
            call_price_list = {}
            if call_pricetable:
                call_price_list = call_pricetable.price_set.active()
                # TO DO: Take everything out of the loop and do a for organization o something
            phonecall['org_price'] = call_price_list.filter(calltype=phonecall['calltype']).values('value').first()['value']
            phonecall_map[org_name].setdefault(phonecall['calltype'], {
                'organization_name': org_name,
                'company_name': company_name,
                'calltype': phonecall['calltype'],
                'org_price': phonecall['org_price'],
                'count': 0,
                'billedtime_sum': 0,
                'cost_sum': 0})
            phonecall['cost_sum'] = phonecall['billedtime_sum'] * phonecall['org_price'] / 60
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
            #Fix VC1 = VC1+VC2+VC3
        for org_name in phonecall_map:
            #NEED TO FIX: for some interval there is no VC2, VC3 and/or VC1. Perhaps ok now
            if VC2 in phonecall_map[org_name]:
                phonecall_map[org_name][VC1]['count'] += phonecall_map[org_name][VC2]['count']
                phonecall_map[org_name][VC1]['billedtime_sum'] += phonecall_map[org_name][VC2]['billedtime_sum']
                phonecall_map[org_name][VC1]['cost_sum'] += phonecall_map[org_name][VC2]['cost_sum']
            if VC3 in phonecall_map[org_name]:
                phonecall_map[org_name][VC1]['count'] += phonecall_map[org_name][VC3]['count']
                phonecall_map[org_name][VC1]['billedtime_sum'] += phonecall_map[org_name][VC3]['billedtime_sum']
                phonecall_map[org_name][VC1]['cost_sum'] += phonecall_map[org_name][VC3]['cost_sum']
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
                      price_ust=ExpressionWrapper(F('org_price') / settings.PRICE_UST, output_field=FloatField()),
                      billedtime_sum=Sum('billedtime'),
                      cost_ust_sum=Sum('org_billedamount',output_field=FloatField()) / settings.PRICE_UST,
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
            .filter(organization__isnull=False, company__status=1,
                    inbound=False,
                    calltype__in=[VC1, VC2, VC3, LOCAL, LDN, LDI]) \
            .values('organization__name', 'company__name', 'calltype') \
            .annotate(count=Count('id'),
                      billedtime_sum=Sum('billedtime'),
                      cost_sum=Sum('org_billedamount')) \
            .values('organization__name', 'company__name', 'calltype', 'org_price',
                    'count', 'billedtime_sum', 'cost_sum') \
            .order_by('organization__name', 'company__name', 'calltype')

        test = list(phonecall_data)
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

        org_list = Organization.objects.all()
        for org in org_list:
            phonecall_map.setdefault(org.name, copy(TOTAL_DICT))
            phonecall_map[org.name].setdefault('companies', {})
        for phonecall in phonecall_data:
            org_name = phonecall['organization__name']
            company_name = phonecall['company__name']
            if not company_name :
                continue


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

            if company_name is not None:
                company = Company.objects.get(name=company_name)
                company_pricetable = company.service_pricetable
                company_price_list = {}
                phonecall_map[org_name]['companies'][company_name].setdefault('services', {})
                if company_pricetable:
                    company_price_list = company_pricetable.price_set.active()
# Not the value comes from the service_price_list

                for company_service in company_price_list:
                    if organization.id != 2 and company.is_new_contract == 0:
                        #TODO: FIX the level services in the database At least level 1
                        if company_service.basic_service == LEVEL_1_ACCESS_SERVICE:
                            company_service.basic_service = LEVEL_2_ACCESS_SERVICE
                        elif company_service.basic_service == LEVEL_6_ACCESS_SERVICE:
                            company_service.basic_service = WIRELESS_ACCESS_SERVICE
                        elif company_service.basic_service == WIRELESS_ACCESS_SERVICE:
                            continue
                    #TODO: Deal with multiple values and doesnotexist
                    service_cost = service_pricetable.price_set.active().get(basic_service=company_service.basic_service).value
                    cost = ((company_service.basic_service_amount * service_cost) / divider) * multiplier
                    #phonecall_map[org_name]['services'].setdefault(company_name, {})
                    phonecall_map[org_name]['companies'][company_name]['services'].update({
                        BASIC_SERVICE_MAP[company_service.basic_service]: {
                            'price': service_cost,
                            'amount': company_service.basic_service_amount,
                            'cost': cost
                        }
                    })
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

            call_pricetable = organization.settings.call_pricetable
            call_price_list = {}
            if call_pricetable:
                call_price_list = call_pricetable.price_set.active()
                # TODO: Take everything out of the loop and do a for organization o something
            phonecall['org_price'] = call_price_list.filter(calltype=phonecall['calltype']).values('value').first()['value']

            phonecall_map[org_name].setdefault(phonecall['calltype'], {
                'organization_name': org_name,
                'company_name': company_name,
                'calltype': phonecall['calltype'],
                'org_price': phonecall['org_price'],
                'count': 0,
                'billedtime_sum': 0,
                'cost_sum': 0})

            phonecall['cost_sum'] = phonecall['billedtime_sum'] * phonecall['org_price'] / 60
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
        Typesofcall = {VC1, VC2, VC3, LOCAL, LDN, LDI }
        for org_name in phonecall_map:
            organization = Organization.objects.get(name=org_name)
            call_pricetable = organization.settings.call_pricetable
            call_price_list = {}
            if call_pricetable:
                call_price_list = call_pricetable.price_set.active()

            for calltype in Typesofcall:
                if calltype not in phonecall_map[org_name]:
                    org_price = call_price_list.filter(calltype=calltype).values('value').first()['value']
                    phonecall_map[org_name].setdefault(calltype, {
                        'organization_name': org_name,
                        'company_name': org_name,
                        'calltype': calltype,
                        'org_price': org_price,
                        'count': 0,
                        'billedtime_sum': 0,
                        'cost_sum': 0})
            phonecall_map[org_name][VC1]['count'] += phonecall_map[org_name][VC2]['count'] + phonecall_map[org_name][VC3]['count']
            phonecall_map[org_name][VC1]['billedtime_sum'] += phonecall_map[org_name][VC2]['billedtime_sum'] + \
                                                     phonecall_map[org_name][VC3]['billedtime_sum']
            phonecall_map[org_name][VC1]['cost_sum'] += phonecall_map[org_name][VC2]['cost_sum'] + \
                                                          phonecall_map[org_name][VC3]['cost_sum']
            for company_name in phonecall_map[org_name]['companies']:
                for calltype in Typesofcall:
                    if calltype not in phonecall_map[org_name]['companies'][company_name]:
                        org_price = call_price_list.filter(calltype=calltype).values('value').first()['value']
                        phonecall_map[org_name]['companies'][company_name].setdefault(calltype, {
                            'organization_name': org_name,
                            'company_name': company_name,
                            'calltype': calltype,
                            'org_price': org_price,
                            'count': 0,
                            'billedtime_sum': 0,
                            'cost_sum': 0})
                phonecall_map[org_name]['companies'][company_name][VC1]['count'] += \
                    phonecall_map[org_name]['companies'][company_name][VC2]['count'] + \
                    phonecall_map[org_name]['companies'][company_name][VC3]['count']
                phonecall_map[org_name]['companies'][company_name][VC1]['billedtime_sum'] += \
                    phonecall_map[org_name]['companies'][company_name][VC2]['billedtime_sum'] + \
                    phonecall_map[org_name]['companies'][company_name][VC3]['billedtime_sum']
                phonecall_map[org_name]['companies'][company_name][VC1]['cost_sum'] += \
                    phonecall_map[org_name]['companies'][company_name][VC2]['cost_sum'] + \
                    phonecall_map[org_name]['companies'][company_name][VC3]['cost_sum']


#There was a problem that any company that did not generate a call would not be included
        company_list = Company.objects.all()
        for company in company_list:
            if company.status != 1:
                continue
            company_pricetable = company.service_pricetable
            company_price_list = {}
            orga = company.organization
            organizName = orga.name
            service_pricetable = orga.settings.service_pricetable
            phonecall_map[organizName]['companies'] \
                .setdefault(company.name, copy(TOTAL_DICT))
            phonecall_map[organizName]['companies'][company.name].setdefault('services', {})
            if company_pricetable:
                company_price_list = company_pricetable.price_set.active()
            # Not the value comes from the service_price_list

            for company_service in company_price_list:
                if orga.id != 2 and company.is_new_contract == 0:
                    # TODO: FIX the level services in the database At least level 1
                    if company_service.basic_service == LEVEL_1_ACCESS_SERVICE:
                        company_service.basic_service = LEVEL_2_ACCESS_SERVICE
                    elif company_service.basic_service == LEVEL_6_ACCESS_SERVICE:
                        company_service.basic_service = WIRELESS_ACCESS_SERVICE
                    elif company_service.basic_service == WIRELESS_ACCESS_SERVICE:
                        continue
                # TODO: Deal with multiple values and doesnotexist
                service_cost = service_pricetable.price_set.active().get(basic_service=company_service.basic_service).value
                cost = ((company_service.basic_service_amount * service_cost) / divider) * multiplier
                # phonecall_map[org_name]['services'].setdefault(company_name, {})
                phonecall_map[organizName]['companies'][company.name]['services'].update({
                    BASIC_SERVICE_MAP[company_service.basic_service]: {
                        'price': service_cost,
                        'amount': company_service.basic_service_amount,
                        'cost': cost
                    }
                })




        phonecall_map[SERVICE] = service_data
        context['phonecall_map'] = phonecall_map
        context.update({
            'contract_version': NEW_CONTRACT})
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
                      price_ust=ExpressionWrapper(F('org_price') / settings.PRICE_UST, output_field=FloatField()),
                      billedtime_sum=Sum('billedtime'),
                      cost_ust_sum=Sum('org_billedamount',output_field=FloatField()) / settings.PRICE_UST,
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


class TotalReportPDFMasterOrg(AdmPhonecallResumePDFReportView):
    template_name = 'phonecalls/master_phonecall_list.html'
    http_method_names = ['get', 'post']

    def get_success_url(self):
        return reverse(
            'accounts:organization_list',)

    def get(self, request, *args, **kwargs):
        if not request.GET:
            return super(AdmPhonecallResumePDFReportView, self).get(request, *args, **kwargs)
        else:
    #def post(self, request, *args, **kwargs):
        #self.date_lt = datetime.fromisoformat(request.POST.get('date_lt'))
        #self.date_gt = datetime.fromisoformat(request.POST.get('date_gt'))
            filterset_class = self.get_filterset_class()
            self.filterset = self.get_filterset(filterset_class)
            if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
                self.object_list = self.filterset.qs
            else:
                self.object_list = self.filterset.queryset.none()
            context = self.get_context_data(filter=self.filterset, object_list=self.object_list)
            organization_list = Organization.objects.all()

            inMemoryOutputFile = BytesIO()
            zipFile = ZipFile(inMemoryOutputFile, 'a')
            filename = self.get_filename(resume=True)
            for org in organization_list:
                org_context = context['phonecall_map'][org.name]
                org_context.update({
                                       'organization': Organization.objects.get(name=org.name),
                            })
                report = SystemReportOrganization(
                    dateBegin=self.date_gt.strftime('%d/%m/%Y'),
                    dateEnd=self.date_lt.strftime('%d/%m/%Y'),
                    reportTitle='Resumo Geral dos Serviços',
                    context=org_context,
                    showCompanies=True)
                pdf = report.create_table_resume_services(org_context)
                zipFile.writestr(filename + org.name+'.pdf', pdf)
                if org.id != 2:
                    report2 = SystemReportOrganization(
                        dateBegin=self.date_gt.strftime('%d/%m/%Y'),
                        dateEnd=self.date_lt.strftime('%d/%m/%Y'),
                        reportTitle='Resumo Geral dos Serviços',
                        context=org_context,
                        showCompanies=True)
                    pdf = report2.create_table_resume_services(org_context, True)
                    zipFile.writestr(filename + org.name + 'mew.pdf', pdf)
            zipFile.close()
            response = HttpResponse(content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachement; filename={filename}.zip'
            response.write(inMemoryOutputFile.getvalue())
            return response


    def get_context_data(self, **kwargs):
        TOTAL_DICT = {
        'count': 0,
            'cost_sum': 0.0,
            'billedtime_sum': 0}
        context = super().get_context_data(**kwargs)
        lastmonthdate = self.date_lt.replace(day=1)
        # In fact I am not considering that the beggining has proportional. Should I???
        basic_service_data_full = Equipment.objects\
                                    .filter(Dateinstalled__lt=lastmonthdate, contract__org_price_table__price__status=1)\
                                    .values('organization__name', 'company__name', 'contract__id')\
                                    .annotate(amount_sum=Count('id'))\
                                    .values('organization__name', 'company__name', \
                                            'contract__id', 'contract__legacyID', 'amount_sum', \
                                            'contract__org_price_table__price', 'contract__org_price_table__price__status', \
                                           'contract__org_price_table__price__basic_service', 'contract__org_price_table__price__value')

        org_list = Organization.objects.all()
        for org in org_list:
            company_list = Company.objects.filter(organization__name=org.name).active()
            #Translate from legacy to new model
            context['phonecall_map'][org.name].setdefault('basic_service', {})
            for key, value in BASIC_SERVICE_MAP.items():
                if value in context['phonecall_map'][org.name]:
                    context['phonecall_map'][org.name]['basic_service'].update({
                        key: {
                            'price': context['phonecall_map'][org.name][value]['price'],
                            'amount': context['phonecall_map'][org.name][value]['amount'],
                            'cost': context['phonecall_map'][org.name][value]['cost'],
                        }
                    })
        #    accumulated_basic_service = Price.objects.filter(table=org.settings.service_pricetable, status=1)
   #         for b_service in accumulated_basic_service:
   #             if b_service.basic_service:
   #                 if b_service.basic_service in context['phonecall_map'][org.name]['basic_service']:
   #                     old_amount = context['phonecall_map'][org.name]['basic_service'][b_service.basic_service]['amount']
   #                     old_cost = context['phonecall_map'][org.name]['basic_service'][b_service.basic_service]['cost']
   #                 else:
   #                     old_amount = 0
   #                    old_cost = 0
   #                context['phonecall_map'][org.name]['basic_service'].update({
   #                    b_service.basic_service: {
   #                        'price': b_service.value,
   #                        'amount': old_amount + b_service.basic_service_amount,
   #                        'cost': b_service.value*(old_cost + b_service.basic_service_amount),
   #                    }
   #                })
            for company in company_list:
                if company.name in context['phonecall_map'][org.name]['companies']:
                    context['phonecall_map'][org.name]['companies'][company.name].setdefault('basic_service', {})
                    context['phonecall_map'][org.name]['companies'][company.name].setdefault('services', {})
                    for key, value in BASIC_SERVICE_MAP.items():
                        if value in context['phonecall_map'][org.name]['companies'][company.name]['services']:
                            context['phonecall_map'][org.name]['companies'][company.name]['basic_service'].update({
                                key: {
                                    'price': context['phonecall_map'][org.name]['companies'][company.name]['services'][value]['price'],
                                    'amount': context['phonecall_map'][org.name]['companies'][company.name]['services'][value]['amount'],
                                    'cost': context['phonecall_map'][org.name]['companies'][company.name]['services'][value]['cost'],
                                }
                            })
                service_data = basic_service_data_full.filter(organization__name=org.name,\
                                                            company__name=company.name)
                for service in service_data:
                    if service['contract__org_price_table__price__basic_service'] != service['contract__legacyID']:
                        continue
                    if org.name in context['phonecall_map']:
                        # Here I have to do with the legacy of the use of fized service_map
                        if service['contract__legacyID'] in context['phonecall_map'][org.name]['basic_service']:
                            old_amount = context['phonecall_map'][org.name]['basic_service'][service['contract__legacyID']]['amount']
                        else:
                            old_amount = 0
                        new_amount = service['amount_sum'] + old_amount
                        context['phonecall_map'][org.name]['basic_service'].update({
                                   service['contract__legacyID']: {
                                   'price': service['contract__org_price_table__price__value'],
                                   'amount': new_amount,
                                   'cost': service['contract__org_price_table__price__value']*new_amount,
                                   }
                        })
                        cost = service['amount_sum'] * service['contract__org_price_table__price__value']
                        if 'service_basic' in context['phonecall_map'][org.name]:
                            old_amount = context['phonecall_map'][org.name]['service_basic']['amount']
                            old_cost = context['phonecall_map'][org.name]['service_basic']['cost']
                        else:
                            old_amount = 0
                            old_cost = 0
                        new_amount = old_amount + service['amount_sum']
                        new_cost = old_cost + cost
                        context['phonecall_map'][org.name].update({
                            'service_basic': {
                                'amount': new_amount,
                                'cost': new_cost
                            }
                        })
                        context['phonecall_map'][org.name]['companies'] \
                            .setdefault(company.name, copy(TOTAL_DICT))
                        context['phonecall_map'][org.name]['companies'][company.name].setdefault('services', {})
                        if service['contract__legacyID'] in context['phonecall_map'][org.name]['companies'][company.name]['basic_service']:
                            old_amount = context['phonecall_map'][org.name]['companies'][company.name]['basic_service'][service['contract__legacyID']]['amount']
                        else:
                            old_amount = 0
                        new_amount = service['amount_sum'] + old_amount
                        context['phonecall_map'][org.name]['companies'][company.name]['basic_service'].update({
                                service['contract__legacyID']: {
                                    'price': service['contract__org_price_table__price__value'],
                                    'unit_cost': service['contract__org_price_table__price__value'],
                                    'amount': new_amount,
                                    'cost': service['contract__org_price_table__price__value'] * new_amount,
                                }
                            })
                        # Add dateinstalled!!!!!!
        basic_service_data_prop = Equipment.objects \
                                   .filter(Dateinstalled__gte = lastmonthdate, Dateinstalled__lte = self.date_lt, contract__org_price_table__price__status=1) \
                                    .values('organization__name', 'company__name', 'contract__id') \
                                    .annotate(amount_sum=Count('id')) \
                                    .values('organization__name', 'company__name', \
                                    'contract__id', 'contract__legacyID', 'amount_sum', \
                                    'contract__org_price_table__price', 'Dateinstalled', \
                                            'contract__org_price_table__price__status', \
                                           'contract__org_price_table__price__basic_service', 'contract__org_price_table__price__value')
        #Here I have filtered all the installation in the month that has installation date < date requested
        if self.date_lt.month == self.date_gt.month:
            days = self.date_lt.day - self.date_gt.day + 1
        else:
            days = self.date_lt
        #temp = (self.date_lt.replace(day=1) + relativedelta(month=+1))
        #last_day_month = ((self.date_lt.replace(day=1) + relativedelta(month=+1)) - timedelta(days=1)).day
        for org in org_list:
            if org.name in context['phonecall_map']:
                context['phonecall_map'][org.name].setdefault('prop', {})
            company_list = Company.objects.filter(organization__name=org.name)
            for company in company_list:
                service_data = basic_service_data_prop.filter(organization__name=org.name,\
                                                            company__name=company.name)
                for service in service_data:
                    if service['contract__org_price_table__price__basic_service'] != service['contract__legacyID']:
                        continue
                    if self.date_gt > service['Dateinstalled'] or self.date_gt.month != service['Dateinstalled'].month:
                        days_installed = days
                    else:
                        days_installed = self.date_lt.day - service['Dateinstalled'].day  + 1
                    prop = Decimal(days_installed)/Decimal(days)
                    if org.name in context['phonecall_map']:
                        #context['phonecall_map'][org.name].setdefault('prop', {})
                        if service['contract__legacyID'] in context['phonecall_map'][org.name]['prop']:
                            old_amount = context['phonecall_map'][org.name]['prop'][service['contract__legacyID']]['amount']
                            old_cost = context['phonecall_map'][org.name]['prop'][service['contract__legacyID']]['cost']
                        else:
                            old_amount = 0
                            old_cost = Decimal(0)
                        new_amount = service['amount_sum'] + old_amount
                        new_cost = prop * service['amount_sum'] * service['contract__org_price_table__price__value'] + old_cost
                        context['phonecall_map'][org.name]['prop'].update({
                                   service['contract__legacyID']: {
                                   'price': service['contract__org_price_table__price__value'],
                                   'amount': new_amount,
                                   'cost': new_cost,
                                   }
                        })
                        context['phonecall_map'][org.name]['companies'] \
                            .setdefault(company.name, copy(TOTAL_DICT))
                        context['phonecall_map'][org.name]['companies'][company.name].setdefault('prop', {})
                        if service['contract__legacyID'] in context['phonecall_map'][org.name]['companies'][company.name]['prop']:
                            old_amount = context['phonecall_map'][org.name]['companies'][company.name]['prop'][service['contract__legacyID']]['amount']
                            old_cost = \
                            context['phonecall_map'][org.name]['companies'][company.name]['prop'][service['contract__legacyID']][
                                'cost']
                        else:
                            old_amount = 0
                            old_cost = Decimal(0)
                        new_amount = service['amount_sum'] + old_amount
                        new_cost = prop*service['amount_sum']*service['contract__org_price_table__price__value'] + old_cost
                        #NEED TO add something for multiple OS in the same month
                        context['phonecall_map'][org.name]['companies'][company.name]['prop'].update({
                                service['contract__legacyID']: {
                                    'price': service['contract__org_price_table__price__value'],
                                    'amount': new_amount,
                                    'cost': new_cost,
                                }
                            })
        return context

class TotalReportPDFCompany(OrgPhonecallResumePDFReportView, BaseContextData):
        template_name = 'phonecalls/master_phonecall_list.html'
        http_method_names = ['get', 'post']

        def get_success_url(self):
            return reverse(
                'accounts:organization_list', )


        def get(self, request, *args, **kwargs):
            if not request.GET:
                return super(OrgPhonecallResumePDFReportView, self).get(request, *args, **kwargs)
            else:
                # def post(self, request, *args, **kwargs):
                # self.date_lt = datetime.fromisoformat(request.POST.get('date_lt'))
                # self.date_gt = datetime.fromisoformat(request.POST.get('date_gt'))
                filterset_class = self.get_filterset_class()
                self.filterset = self.get_filterset(filterset_class)
                if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
                    self.object_list = self.filterset.qs
                else:
                    self.object_list = self.filterset.queryset.none()
                company_list = Company.objects.filter(organization__name=self.organization.name).active()
                inMemoryOutputFile = BytesIO()
                zipFile = ZipFile(inMemoryOutputFile, 'a')
                filename = self.get_filename(resume=True)
                context = self.get_context_data(filter=self.filterset, object_list=self.object_list)
                for company in company_list:
                    self.company = company
                    if company.name not in context['company']:
                        continue
                    company_context = context['company'][company.name]
                    company_context.update({'organization':self.organization})
                    report = SystemReport(
                        dateBegin=self.date_gt.strftime('%d/%m/%Y'),
                        dateEnd=self.date_lt.strftime('%d/%m/%Y'),
                        reportTitle='Resumo dos Serviços',
                        company=self.company)
                    pdf = report.make_phonecall_resume_table(company_context)
                    zipFile.writestr(filename + company.name + '.pdf', pdf)
                zipFile.close()
                response = HttpResponse(content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachement; filename={filename}.zip'
                response.write(inMemoryOutputFile.getvalue())
                return response

        def get_context_data(self, **kwargs):
            #context = super().get_context_data(**kwargs)
            context = super().get_Org_Context()

            lastmonthdate = self.date_lt.replace(day=1)
                    # In fact I am not considering that the beggining has proportional. Should I???
            basic_service_data_full = Equipment.objects \
                        .filter(organization = self.organization ,Dateinstalled__lt=lastmonthdate, contract__org_price_table__price__status=1) \
                        .values( 'company__name', 'contract__id') \
                        .annotate(amount_sum=Count('id')) \
                        .values( 'company__name', \
                                'contract__id', 'contract__legacyID', 'amount_sum', \
                                'contract__org_price_table__price', 'contract__org_price_table__price__status', \
                                'contract__org_price_table__price__basic_service', 'contract__org_price_table__price__value')
            company_list = Company.objects.filter(organization=self.organization)

            for company in company_list:
                if company.name in context['company']:
                    context['company'][company.name].setdefault('basic_service', {})
                    context['company'][company.name].setdefault('services', {})

                    for key, value in BASIC_SERVICE_MAP.items():
                        if value in context['company'][company.name]['basic_service']:
                            context['company'][company.name]['basic_service'].update({
                                key: {
                                    'price': context['company'][company.name]['basic_service'][value]['price'],
                                    'amount': context['company'][company.name]['basic_service'][value]['amount'],
                                    'cost': context['company'][company.name]['basic_service'][value]['cost'],
                                }
                            })


                service_data = basic_service_data_full.filter(company__name=company.name)
                service_pricetable = company.service_pricetable
                service_price_list = {}
                if service_pricetable:
                    service_price_list = service_pricetable.price_set.active()
                for service in service_data:
                    if service['contract__org_price_table__price__basic_service'] != service['contract__legacyID']:
                        continue
                    if company.name not in context['company']:
                        context['company'].setdefault(company.name, {})
                    if 'prop' not in context['company'][company.name]:
                        context['company'][company.name].setdefault('prop', {})
                    if 'basic_service' not in context['company'][company.name]:
                        context['company'][company.name].setdefault('basic_service', {})
                    if service['contract__legacyID'] in context['company'][company.name]['basic_service']:
                        old_amount = context['company'][company.name]['basic_service'][service['contract__legacyID']]['amount']
                    else:
                        old_amount = 0
                    new_amount = service['amount_sum'] + old_amount
                    if self.organization.id ==1:
                        try:
                            price = service_price_list.get(basic_service=service['contract__legacyID']).value
                        except Exception as e:
                            # If cannot find in the company's table go to default
                            defaultcompany = Company.objects.get(name='SOP')
                            service_pricetable = defaultcompany.service_pricetable
                            service_price_list = {}
                            if service_pricetable:
                                service_price_list = service_pricetable.price_set.active()
                            try:
                                price = service_price_list.get(basic_service=service['contract__legacyID']).value
                            except Exception as e:
                                price = 0
                    elif self.organization.id ==2:
                        price = service['contract__org_price_table__price__value']
                    elif self.organization.id ==3:
                        defaultcompany = Company.objects.get(name='SAP')
                        service_pricetable = defaultcompany.service_pricetable
                        service_price_list = {}
                        if service_pricetable:
                            service_price_list = service_pricetable.price_set.active()
                        price = service_price_list.get(basic_service=service['contract__legacyID']).value
                    else:
                        price = 0
                    context['company'][company.name]['basic_service'].update({
                        service['contract__legacyID']: {
                            # later I will have to think if I create a contract for each of Etice's client
                            #'price': service['contract__org_price_table__price__value'], #check unit_cost if use
                            'price': price,
                            'amount': new_amount,
                            #here too
                            #'cost': service['contract__org_price_table__price__value'] * new_amount,
                            'cost': price * new_amount,
                        }
                    })
                    #cost = service['amount_sum'] * service['contract__org_price_table__price__value']
                    cost = service['amount_sum'] * price
                    if 'service_basic' in context['company'][company.name]:
                        old_amount = context['company'][company.name]['service_basic']['amount']
                        old_cost = context['company'][company.name]['service_basic']['cost']
                    else:
                        old_amount = 0
                        old_cost = 0
                    new_amount = old_amount + service['amount_sum']
                    new_cost = old_cost + cost
                    context['company'][company.name].update({
                        'service_basic': {
                            'amount': new_amount,
                            'cost': new_cost
                        }
                    })


                            # Add dateinstalled!!!!!!
                basic_service_data_prop = Equipment.objects \
                    .filter(Dateinstalled__gte=lastmonthdate, Dateinstalled__lte=self.date_lt,
                            contract__org_price_table__price__status=1, company=company) \
                    .values('organization__name', 'company__name', 'contract__id') \
                    .annotate(amount_sum=Count('id')) \
                    .values('organization__name', 'company__name', \
                            'contract__id', 'contract__legacyID', 'amount_sum', \
                            'contract__org_price_table__price', 'Dateinstalled', \
                            'contract__org_price_table__price__status', \
                            'contract__org_price_table__price__basic_service', 'contract__org_price_table__price__value')
                if self.date_lt.month == self.date_gt.month:
                    days = self.date_lt.day - self.date_gt.day + 1
                else:
                    days = self.date_lt
                #last_day_month = ((self.date_lt.replace(day=1) + relativedelta(month=+1)) - timedelta(days=1)).day
                service_data = basic_service_data_prop.filter(company__name=company.name)

                for service in service_data:
                    if service['contract__org_price_table__price__basic_service'] != service['contract__legacyID']:
                        continue
                    if self.date_gt > service['Dateinstalled'] or self.date_gt.month != service['Dateinstalled'].month:
                        days_installed = days
                    else:
                        days_installed = self.date_lt.day - service['Dateinstalled'].day  + 1
                    prop = Decimal(days_installed) / Decimal(days)
                    #prop = (last_day_month - service['Dateinstalled'].day + 1) / Decimal(last_day_month)
                    if company.name in context['company']:
                        context['company'][company.name].setdefault('prop', {})
                    else:
                        context['company'].setdefault(company.name, {})
                        context['company'][company.name].setdefault('prop', {})
                    if service['contract__legacyID'] in context['company'][company.name]['prop']:
                        old_amount = context['company'][company.name]['prop'][service['contract__legacyID']]['amount']
                        old_cost = context['company'][company.name]['prop'][service['contract__legacyID']]['cost']
                    else:
                        old_amount = 0
                        old_cost = Decimal(0)
                    new_amount = service['amount_sum'] + old_amount
                    #new_cost = prop * service['amount_sum'] * service['contract__org_price_table__price__value'] + old_cost
                    if self.organization.id ==1:
                        try:
                            price = service_price_list.get(basic_service=service['contract__legacyID']).value
                        except Exception as e:
                            # If cannot find in the company's table go to default
                            defaultcompany = Company.objects.get(name='SOP')
                            service_pricetable = defaultcompany.service_pricetable
                            service_price_list = {}
                            if service_pricetable:
                                service_price_list = service_pricetable.price_set.active()
                            price = service_price_list.get(basic_service=service['contract__legacyID']).value
                    elif self.organization.id ==2:
                        price = service['contract__org_price_table__price__value']
                    elif self.organization.id ==3:
                        defaultcompany = Company.objects.get(name='SAP')
                        service_pricetable = defaultcompany.service_pricetable
                        service_price_list = {}
                        if service_pricetable:
                            service_price_list = service_pricetable.price_set.active()
                        price = service_price_list.get(basic_service=service['contract__legacyID']).value
                    else:
                        price = 0
                    new_cost = prop * service['amount_sum']* price + old_cost


                    context['company'][company.name]['prop'].update({
                        service['contract__legacyID']: {
                            #'price': service['contract__org_price_table__price__value'],
                            'price': price,
                            'amount': new_amount,
                            'cost': new_cost,
                        }
                    })
            return context

class TotalReportPDFXLSCompany(OrgPhonecallXLSXReportView, BaseContextData):
            template_name = 'phonecalls/master_phonecall_list.html'
            http_method_names = ['get', 'post']

            def get_success_url(self):
                return reverse(
                    'accounts:organization_list', )

            def get(self, request, *args, **kwargs):
                if not request.GET:
                    return super(OrgPhonecallXLSXReportView, self).get(request, *args, **kwargs)
                else:
                    # def post(self, request, *args, **kwargs):
                    # self.date_lt = datetime.fromisoformat(request.POST.get('date_lt'))
                    # self.date_gt = datetime.fromisoformat(request.POST.get('date_gt'))
                    filterset_class = self.get_filterset_class()
                    self.filterset = self.get_filterset(filterset_class)
                    if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
                        self.object_list = self.filterset.qs
                    else:
                        self.object_list = self.filterset.queryset.none()
                    company_list = Company.objects.filter(organization__name=self.organization.name)
                    inMemoryOutputFile = BytesIO()
                    zipFile = ZipFile(inMemoryOutputFile, 'a')
                    filename = self.get_filename(resume=False)
                    context = self.get_context_data(filter=self.filterset, object_list=self.object_list)

                    for company in company_list:
                        self.company = company
                        company_tag = f'{company.name.upper()} - {company.description}' if company.description else company.name.upper()
                        if company_tag not in context['phonecall_data']:
                            continue
                        company_context ={}
                        company_context.update({'phonecall_data': {}})
                        company_context['phonecall_data'] = context['phonecall_data'][company_tag]
                        company_context.update({'organization': self.organization})
                        report = XLSXCompanyReport(
                            date_start=self.date_gt.strftime('%d/%m/%Y'),
                            date_stop=self.date_lt.strftime('%d/%m/%Y'),
                            title='Relatório de Ligações por Ramal',
                            company=company)
                        report.build_detail_report(company_context)
                        val = report.get_file()
                        zipFile.writestr(filename + company.name + '.xlsx', val.getvalue())
                        report = SystemReport(
                            dateBegin=self.date_gt.strftime('%d/%m/%Y'),
                            dateEnd=self.date_lt.strftime('%d/%m/%Y'),
                            reportTitle='Relatório de Ligações por Ramal',
                            company=self.company,
                            formatPage=2)
                        pdf = report.make_phonecall_table(company_context)
                        zipFile.writestr(filename + company.name + '.pdf',pdf)
                    zipFile.close()
                    response = HttpResponse(content_type='application/octet-stream')
                    response['Content-Disposition'] = f'attachement; filename={filename}.zip'
                    response.write(inMemoryOutputFile.getvalue())
                    return response

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                for client, client_phonedata in context['phonecall_data'].items():
                    for ramal, phonedata in client_phonedata.items():
                        count = 0
                        bill_sum =0
                        cost_sum = 0.0
                        for ramal_data in phonedata['phonecall_list']:
                            count += 1
                            bill_sum += ramal_data['duration']
                            cost_sum += float(ramal_data['billedamount'])
                        phonedata.setdefault('count', count)
                        phonedata.setdefault('billedtime_sum', bill_sum)
                        phonedata.setdefault('cost_sum', cost_sum)
                return context
