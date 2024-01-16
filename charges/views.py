# django
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

# third party
from django_filters.views import BaseFilterView
from organizations.views.mixins import AdminRequiredMixin

# project
from accounts.mixins import OrganizationMixin
from centers.utils import get_company_choices
from core.views import SuperuserRequiredMixin
from phonecalls import constants as phonecalls_constants
from phonecalls.models import Price
from phonecalls.models import PriceTable

# local
from . import constants as charges_constants
from .filters import PriceTableFilter
from .forms import CallPriceTableCreateForm
from .forms import CallPriceTableUpdateForm
from .forms import ServicePriceTableCreateForm
from .forms import ServicePriceTableUpdateForm
from .forms import OtherPriceTableCreateForm
from .forms import OtherPriceTableUpdateForm
from .mixins import CallPriceTableMixin
from .mixins import ServicePriceTableMixin
from .mixins import OtherPriceTableMixin

class CallPriceTableListView(CallPriceTableMixin,
                             BaseFilterView,
                             ListView):  # ORG
    """
    Lista das tabelas de valores para serviços de comunicação
    Permissão: Membro do organização
    """

    context_object_name = 'pricetable_list'
    filterset_class = PriceTableFilter
    http_method_names = ['get']
    model = PriceTable
    ordering = ['-created']
    paginate_by = 20
    template_name = 'pricetable/call_pricetable_list.html'

    def get_context_data(self, **kwargs):
        user = self.request.user
        if user.is_superuser or self.organization.is_admin(user):
            company_choices = get_company_choices(self.organization)
        else:
            company_choices = get_company_choices(self.organization, user.company_set)
        kwargs.update({
            'company_choices': company_choices})
        return super().get_context_data(**kwargs)


class CallPriceTableDetailView(CallPriceTableMixin,
                               DetailView):  # ORG
    """
    Detalhe da tabela de valores para serviços comunicação
    Permissão: Membro do organização
    """

    context_object_name = 'pricetable'
    http_method_names = ['get']
    model = PriceTable
    template_name = 'pricetable/call_pricetable_detail.html'

    def get_context_data(self, **kwargs):
        user = self.request.user
        company_set = self.object.call_company_set.only('name')
        if not user.is_superuser and not self.organization.is_admin(user):
            company_set = company_set.filter(id__in=user.company_set.only('id'))
        kwargs.update({
            'company_list': company_set,
            'price_list': self.object.price_set.active().order_by('basic_service')})
        return super().get_context_data(**kwargs)


class CallPriceTableCreateView(OrganizationMixin,
                               AdminRequiredMixin,
                               CreateView):  # ORG
    """
    Formulário de criação de tabelas de valores para serviços de comunicação
    Permissão: Administrador do organização
    """

    form_class = CallPriceTableCreateForm
    http_method_names = ['get', 'post']
    model = PriceTable
    template_name = 'pricetable/call_pricetable_form.html'

    def form_valid(self, form):
        pricetable = form.save(commit=False)
        pricetable.organization = self.organization
        pricetable.servicetype = charges_constants.COMMUNICATION_SERVICE
        pricetable.save()

        price_fields = charges_constants.PRICE_FIELDS_CALLTYPE_MAP.values()
        for price_field in price_fields:
            price = form.cleaned_data.get(f'{price_field}_price')
            if not price:
                continue
            calltype = getattr(phonecalls_constants, price_field.upper())
            Price.objects.create(table=pricetable, calltype=calltype, value=price)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'charges:call_pricetable_list', kwargs={'org_slug': self.organization.slug})


class CallPriceTableUpdateView(OrganizationMixin,
                               AdminRequiredMixin,
                               UpdateView):  # ORG
    """
    Formulário de atualização de tabelas de valores para serviços de comunicação
    Permissão: Administrador do organização
    """

    context_object_name = 'pricetable'
    form_class = CallPriceTableUpdateForm
    http_method_names = ['get', 'post']
    model = PriceTable
    template_name = 'pricetable/call_pricetable_form.html'

    def form_valid(self, form):
        pricetable = form.instance

        price_fields = charges_constants.PRICE_FIELDS_CALLTYPE_MAP.values()
        for price_field in price_fields:
            price = form.cleaned_data.get(f'{price_field}_price')
            if not price:
                continue
            calltype = getattr(phonecalls_constants, price_field.upper())
            updated = False
            try:
                curr_price = pricetable.price_set.active().get(calltype=calltype)
                if curr_price.value != price:
                    curr_price.inactive()
                    updated = True
            except Price.DoesNotExist:
                updated = True
            if updated:
                Price.objects.create(table=pricetable, calltype=calltype, value=price)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'charges:call_pricetable_list', kwargs={'org_slug': self.organization.slug})


class ServicePriceTableListView(ServicePriceTableMixin,
                                BaseFilterView,
                                ListView):  # ORG
    """
    Lista das tabelas de valores para serviços básicos
    Permissão: Membro da organização
    """

    context_object_name = 'pricetable_list'
    filterset_class = PriceTableFilter
    http_method_names = ['get']
    model = PriceTable
    ordering = ['-created']
    paginate_by = 20
    template_name = 'pricetable/service_pricetable_list.html'

    def get_context_data(self, **kwargs):
        user = self.request.user
        if user.is_superuser or self.organization.is_admin(user):
            company_choices = get_company_choices(self.organization)
        else:
            company_choices = get_company_choices(self.organization, user.company_set)
        kwargs.update({
            'company_choices': company_choices})
        return super().get_context_data(**kwargs)


class ServicePriceTableDetailView(ServicePriceTableMixin,
                                  DetailView):  # ORG
    """
    Detalhe da tabela de valores para serviços básicos
    Permissão: Membro da organização
    """

    context_object_name = 'pricetable'
    http_method_names = ['get']
    model = PriceTable
    template_name = 'pricetable/service_pricetable_detail.html'

    def get_context_data(self, **kwargs):
        kwargs.update({'price_list': self.object.price_set.active().order_by('basic_service')})
        return super().get_context_data(**kwargs)


class ServicePriceTableCreateView(OrganizationMixin,
                                  AdminRequiredMixin,
                                  CreateView):  # ORG
    """
    Formulário de criação de tabelas de valores para serviços básicos
    Permissão: Administrador do organização
    """

    form_class = ServicePriceTableCreateForm
    http_method_names = ['get', 'post']
    model = PriceTable
    template_name = 'pricetable/service_pricetable_form.html'

    def form_valid(self, form):
        pricetable = form.save(commit=False)
        pricetable.organization = self.organization
        pricetable.servicetype = charges_constants.BASIC_SERVICE
        pricetable.save()

        price_fields = charges_constants.PRICE_FIELDS_BASIC_SERVICE_MAP.values()
        for price_field in price_fields:
            amount = form.cleaned_data.get(f'{price_field}_amount')
            price = form.cleaned_data.get(f'{price_field}_price')
            if not (amount and price):
                continue
            basic_service = getattr(charges_constants, price_field.upper())
            Price.objects.create(table=pricetable, basic_service=basic_service,
                                 basic_service_amount=amount, value=price)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'charges:service_pricetable_list', kwargs={'org_slug': self.organization.slug})


class ServicePriceTableUpdateView(OrganizationMixin,
                                  AdminRequiredMixin,
                                  UpdateView):  # ORG
    """
    Formulário de atualização de tabelas de valores para serviços básicos
    Permissão: Administrador do organização
    """

    context_object_name = 'pricetable'
    form_class = ServicePriceTableUpdateForm
    http_method_names = ['get', 'post']
    model = PriceTable
    template_name = 'pricetable/service_pricetable_form.html'

    def form_valid(self, form):
        pricetable = form.instance

        price_fields = charges_constants.PRICE_FIELDS_BASIC_SERVICE_MAP.values()
        for price_field in price_fields:
            amount = form.cleaned_data.get(f'{price_field}_amount')
            price = form.cleaned_data.get(f'{price_field}_price')
            if not (amount and price):
                continue
            basic_service = getattr(charges_constants, price_field.upper())
            updated = False
            try:
                curr_price = pricetable.price_set.active().get(basic_service=basic_service)
                if curr_price.basic_service_amount != amount or curr_price.value != price:
                    curr_price.inactive()
                    updated = True
            except Price.DoesNotExist:
                updated = True
            if updated:
                Price.objects.create(table=pricetable, basic_service=basic_service,
                                     basic_service_amount=amount, value=price)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'charges:service_pricetable_list', kwargs={'org_slug': self.organization.slug})

    def get_context_data(self, **kwargs):
        context = super(ServicePriceTableUpdateView, self).get_context_data(**kwargs)
        context['new_contract_dict'] = charges_constants.BASIC_SERVICE_CHOICES_NEW


class OtherPriceTableListView(OtherPriceTableMixin,
                                BaseFilterView,
                                ListView):  # ORG
    """
    Lista das tabelas de valores para serviços diversos
    Permissão: Membro da organização
    """

    context_object_name = 'pricetable_list'
    filterset_class = PriceTableFilter
    http_method_names = ['get']
    model = PriceTable
    ordering = ['-created']
    paginate_by = 20
    template_name = 'pricetable/other_pricetable_list.html'

    def get_context_data(self, **kwargs):
        user = self.request.user
        if user.is_superuser or self.organization.is_admin(user):
            company_choices = get_company_choices(self.organization)
        else:
            company_choices = get_company_choices(self.organization, user.company_set)
        kwargs.update({
            'company_choices': company_choices})
        return super().get_context_data(**kwargs)


class OtherPriceTableDetailView(OtherPriceTableMixin,
                                  DetailView):  # ORG
    """
    Detalhe da tabela de valores para serviços diversos
    Permissão: Membro da organização
    """

    context_object_name = 'pricetable'
    http_method_names = ['get']
    model = PriceTable
    template_name = 'pricetable/other_pricetable_detail.html'

    def get_context_data(self, **kwargs):
        kwargs.update({'price_list': self.object.price_set.active().order_by('basic_service')})
        return super().get_context_data(**kwargs)


class OtherPriceTableCreateView(OrganizationMixin,
                                  AdminRequiredMixin,
                                  CreateView):  # ORG
    """
    Formulário de criação de tabelas de valores para serviços básicos
    Permissão: Administrador do organização
    """

    form_class = OtherPriceTableCreateForm
    http_method_names = ['get', 'post']
    model = PriceTable
    template_name = 'pricetable/other_pricetable_form.html'

    def form_valid(self, form):
        pricetable = form.save(commit=False)
        pricetable.organization = self.organization
        pricetable.servicetype = charges_constants.DIVERSE_SERVICE
        pricetable.save()

        price_fields = charges_constants.PRICE_FIELDS_OTHERTYPE_MAP.values()
        for price_field in price_fields:
            price = form.cleaned_data.get(f'{price_field}_price')
            if not price:
                continue
            other_service = getattr(phonecalls_constants, price_field.upper())
            Price.objects.create(table=pricetable, othertype=other_service,
                                 value=price)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'charges:other_pricetable_list', kwargs={'org_slug': self.organization.slug})


class OtherPriceTableUpdateView(OrganizationMixin,
                                  AdminRequiredMixin,
                                  UpdateView):  # ORG
    """
    Formulário de atualização de tabelas de valores para serviços diversos
    Permissão: Administrador do organização
    """

    context_object_name = 'pricetable'
    form_class = OtherPriceTableUpdateForm
    http_method_names = ['get', 'post']
    model = PriceTable
    template_name = 'pricetable/other_pricetable_form.html'


    def form_valid(self, form):
        pricetable = form.instance

        price_fields = charges_constants.PRICE_FIELDS_OTHERTYPE_MAP.values()
        for price_field in price_fields:
            price = form.cleaned_data.get(f'{price_field}_price')
            if not price:
                continue
            othertype = getattr(phonecalls_constants, price_field.upper())
            updated = False
            try:
                curr_price = pricetable.price_set.active().get(othertype=othertype)
                if curr_price.value != price:
                    curr_price.inactive()
                    updated = True
            except Price.DoesNotExist:
                updated = True
            if updated:
                Price.objects.create(table=pricetable, othertype=othertype, value=price)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'charges:other_pricetable_list', kwargs={'org_slug': self.organization.slug})


class AdmCallPriceTableListView(SuperuserRequiredMixin,
                                ListView):  # SUPERUSER
    """
    Lista das tabelas de valores para serviços Diversos
    Permissão: Superusuário
    """

    context_object_name = 'pricetable_list'
    http_method_names = ['get']
    model = PriceTable
    ordering = ['-created']
    paginate_by = 20
    template_name = 'pricetable/adm_call_pricetable_list.html'

    def get_queryset(self):
        return super().get_queryset().filter(servicetype=charges_constants.COMMUNICATION_SERVICE)


class AdmCallPriceTableDetailView(SuperuserRequiredMixin,
                                  DetailView):  # SUPERUSER
    """
    Detalhe da tabela de valores para serviços comunicação
    Permissão: Superusuário
    """

    context_object_name = 'pricetable'
    http_method_names = ['get']
    model = PriceTable
    template_name = 'pricetable/adm_call_pricetable_detail.html'

    def get_queryset(self):
        return super().get_queryset().filter(servicetype=charges_constants.COMMUNICATION_SERVICE)

    def get_context_data(self, **kwargs):
        kwargs.update({'price_list': self.object.price_set.active().order_by('basic_service')})
        return super().get_context_data(**kwargs)


class AdmCallPriceTableCreateView(SuperuserRequiredMixin,
                                  CreateView):  # SUPERUSER
    """
    Formulário de criação de tabelas de valores para serviços de comunicação
    Permissão: Superusuário
    """

    form_class = CallPriceTableCreateForm
    http_method_names = ['get', 'post']
    model = PriceTable
    template_name = 'pricetable/adm_call_pricetable_form.html'
    success_url = reverse_lazy('adm_call_pricetable_list')

    def form_valid(self, form):
        pricetable = form.save(commit=False)
        pricetable.servicetype = charges_constants.COMMUNICATION_SERVICE
        pricetable.save()

        price_fields = charges_constants.PRICE_FIELDS_CALLTYPE_MAP.values()
        for price_field in price_fields:
            price = form.cleaned_data.get(f'{price_field}_price')
            if not price:
                continue
            calltype = getattr(phonecalls_constants, price_field.upper())
            Price.objects.create(table=pricetable, calltype=calltype, value=price)
        return super().form_valid(form)


class AdmCallPriceTableUpdateView(SuperuserRequiredMixin,
                                  UpdateView):  # SUPERUSER
    """
    Formulário de atualização de tabelas de valores para serviços de comunicação
    Permissão: Superusuário
    """

    context_object_name = 'pricetable'
    form_class = CallPriceTableUpdateForm
    http_method_names = ['get', 'post']
    model = PriceTable
    success_url = reverse_lazy('adm_call_pricetable_list')
    template_name = 'pricetable/adm_call_pricetable_form.html'

    def form_valid(self, form):
        pricetable = form.instance

        price_fields = charges_constants.PRICE_FIELDS_CALLTYPE_MAP.values()
        for price_field in price_fields:
            price = form.cleaned_data.get(f'{price_field}_price')
            if not price:
                continue
            calltype = getattr(phonecalls_constants, price_field.upper())
            updated = False
            try:
                curr_price = pricetable.price_set.active().get(calltype=calltype)
                if curr_price.value != price:
                    curr_price.inactive()
                    updated = True
            except Price.DoesNotExist:
                updated = True
            if updated:
                Price.objects.create(table=pricetable, calltype=calltype, value=price)
        return super().form_valid(form)


class AdmServicePriceTableListView(SuperuserRequiredMixin,
                                   ListView):  # SUPERUSER
    """
    Lista das tabelas de valores para serviços básicos
    Permissão: Superusuário
    """

    context_object_name = 'pricetable_list'
    http_method_names = ['get']
    model = PriceTable
    ordering = ['-created']
    paginate_by = 20
    template_name = 'pricetable/adm_service_pricetable_list.html'

    def get_queryset(self):
        return super().get_queryset().filter(servicetype=charges_constants.BASIC_SERVICE)


class AdmServicePriceTableDetailView(SuperuserRequiredMixin,
                                     DetailView):  # SUPERUSER
    """
    Detalhe da tabela de valores para serviços básicos
    Permissão: Superusuário
    """

    context_object_name = 'pricetable'
    http_method_names = ['get']
    model = PriceTable
    template_name = 'pricetable/adm_service_pricetable_detail.html'

    def get_queryset(self):
        return super().get_queryset().filter(servicetype=charges_constants.BASIC_SERVICE)

    def get_context_data(self, **kwargs):
        kwargs.update({'price_list': self.object.price_set.active().order_by('basic_service')})
        return super().get_context_data(**kwargs)


class AdmServicePriceTableCreateView(SuperuserRequiredMixin,
                                     CreateView):  # SUPERUSER
    """
    Formulário de criação de tabelas de valores para serviços básicos
    Permissão: Superusuário
    """

    form_class = ServicePriceTableCreateForm
    http_method_names = ['get', 'post']
    model = PriceTable
    template_name = 'pricetable/adm_service_pricetable_form.html'
    success_url = reverse_lazy('adm_service_pricetable_list')

    def form_valid(self, form):
        pricetable = form.save(commit=False)
        pricetable.servicetype = charges_constants.BASIC_SERVICE
        pricetable.save()

        price_fields = charges_constants.PRICE_FIELDS_BASIC_SERVICE_MAP.values()
        for price_field in price_fields:
            amount = form.cleaned_data.get(f'{price_field}_amount')
            price = form.cleaned_data.get(f'{price_field}_price')
            if not (amount and price):
                continue
            basic_service = getattr(charges_constants, price_field.upper())
            Price.objects.create(table=pricetable, basic_service=basic_service,
                                 basic_service_amount=amount, value=price)
        return super().form_valid(form)


class AdmServicePriceTableUpdateView(SuperuserRequiredMixin,
                                     UpdateView):  # SUPERUSER
    """
    Formulário de atualização de tabelas de valores para serviços básicos
    Permissão: Superusuário
    """

    context_object_name = 'pricetable'
    form_class = ServicePriceTableUpdateForm
    http_method_names = ['get', 'post']
    model = PriceTable
    success_url = reverse_lazy('adm_service_pricetable_list')
    template_name = 'pricetable/adm_service_pricetable_form.html'

    def form_valid(self, form):
        pricetable = form.instance

        price_fields = charges_constants.PRICE_FIELDS_BASIC_SERVICE_MAP.values()
        for price_field in price_fields:
            amount = form.cleaned_data.get(f'{price_field}_amount')
            price = form.cleaned_data.get(f'{price_field}_price')
            if not (amount and price):
                continue
            basic_service = getattr(charges_constants, price_field.upper())
            updated = False
            try:
                curr_price = pricetable.price_set.active().get(basic_service=basic_service)
                if curr_price.basic_service_amount != amount or curr_price.value != price:
                    curr_price.inactive()
                    updated = True
            except Price.DoesNotExist:
                updated = True
            if updated:
                Price.objects.create(table=pricetable, basic_service=basic_service,
                                     basic_service_amount=amount, value=price)
        return super().form_valid(form)

class AdmOtherPriceTableListView(SuperuserRequiredMixin,
                                ListView):  # SUPERUSER
    """
    Lista das tabelas de valores para serviços Diversos
    Permissão: Superusuário
    """

    context_object_name = 'pricetable_list'
    http_method_names = ['get']
    model = PriceTable
    ordering = ['-created']
    paginate_by = 20
    template_name = 'pricetable/adm_other_pricetable_list.html'

    def get_queryset(self):
        return super().get_queryset().filter(servicetype=charges_constants.DIVERSE_SERVICE)


class AdmOtherPriceTableDetailView(SuperuserRequiredMixin,
                                  DetailView):  # SUPERUSER
    """
    Detalhe da tabela de valores para serviços diversos
    Permissão: Superusuário
    """

    context_object_name = 'pricetable'
    http_method_names = ['get']
    model = PriceTable
    template_name = 'pricetable/adm_other_pricetable_detail.html'

    def get_queryset(self):
        return super().get_queryset().filter(servicetype=charges_constants.DIVERSE_SERVICE)

    def get_context_data(self, **kwargs):
        kwargs.update({'price_list': self.object.price_set.active().order_by('basic_service')})
        return super().get_context_data(**kwargs)


class AdmOtherPriceTableCreateView(SuperuserRequiredMixin,
                                  CreateView):  # SUPERUSER
    """
    Formulário de criação de tabelas de valores para serviços diversos
    Permissão: Superusuário
    """

    form_class = OtherPriceTableCreateForm
    http_method_names = ['get', 'post']
    model = PriceTable
    template_name = 'pricetable/adm_other_pricetable_form.html'
    success_url = reverse_lazy('adm_other_pricetable_list')

    def form_valid(self, form):
        pricetable = form.save(commit=False)
        pricetable.servicetype = charges_constants.DIVERSE_SERVICE
        pricetable.save()

        price_fields = charges_constants.PRICE_FIELDS_OTHERTYPE_MAP.values()
        for price_field in price_fields:
            price = form.cleaned_data.get(f'{price_field}_price')
            if not price:
                continue
            othertype = getattr(phonecalls_constants, price_field.upper())
            Price.objects.create(table=pricetable, othertype=othertype, value=price)
        return super().form_valid(form)


class AdmOtherPriceTableUpdateView(SuperuserRequiredMixin,
                                  UpdateView):  # SUPERUSER
    """
    Formulário de atualização de tabelas de valores para serviços diversos
    Permissão: Superusuário
    """

    context_object_name = 'pricetable'
    form_class = OtherPriceTableUpdateForm
    http_method_names = ['get', 'post']
    model = PriceTable
    success_url = reverse_lazy('adm_other_pricetable_list')
    template_name = 'pricetable/adm_other_pricetable_form.html'

    def form_valid(self, form):
        pricetable = form.instance

        price_fields = charges_constants.PRICE_FIELDS_OTHERTYPE_MAP.values()
        for price_field in price_fields:
            price = form.cleaned_data.get(f'{price_field}_price')
            if not price:
                continue
            othertype = getattr(phonecalls_constants, price_field.upper())
            updated = False
            try:
                curr_price = pricetable.price_set.active().get(othertype=othertype)
                if curr_price.value != price:
                    curr_price.inactive()
                    updated = True
            except Price.DoesNotExist:
                updated = True
            if updated:
                Price.objects.create(table=pricetable, othertype=othertype, value=price)
        return super().form_valid(form)