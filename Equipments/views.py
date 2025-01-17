from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.db.models import Q

# third party
from django_filters.views import BaseFilterView
from organizations.views.mixins import AdminRequiredMixin
from organizations.models import Organization

# project
from accounts.mixins import OrganizationContextMixin
from accounts.mixins import OrganizationMixin
from centers.mixins import CompanyContextMixin
from centers.mixins import CompanyMembershipRequiredMixin
from centers.mixins import CompanyMixin
from core.views import SuperuserRequiredMixin
from phonecalls.models import Price

from .models import Equipment, typeofphone, ContractBasicServices
from .forms import typeofphoneAssigned, OSAssignedForm, contractAssigned
from .filters import ContractFilter
from charges.constants import BASIC_SERVICE_CHOICES

class OSListView(SuperuserRequiredMixin, ListView):  # SUPERUSER
    """
    Lista de equipments atribuidos ao sistema
    Permissão: Super usuário
    """

    context_object_name = 'equipment_list'
    http_method_names = ['get']
    model = Equipment
    template_name = 'OS/os_list.html'


class OSCreateView(SuperuserRequiredMixin, CreateView):  # SUPERUSER
    """
    Formulário de atribuição de OS ao sistema
    Permissão: Super usuário
    """

    form_class = OSAssignedForm
    http_method_names = ['get', 'post']
    model = Equipment
    success_url = reverse_lazy('equipment_list')
    template_name = 'OS/os_assigned_form.html'

class EquipmentListView(SuperuserRequiredMixin, ListView):  # SUPERUSER
    """
    Lista de equipments atribuidos ao sistema
    Permissão: Super usuário
    """

    context_object_name = 'equipment_list'
    http_method_names = ['get']
    model = typeofphone
    template_name = 'OS/equipment_list.html'


class EquipmentCreateView(SuperuserRequiredMixin, CreateView):  # SUPERUSER
        """
        Formulário de atribuição de OS ao sistema
        Permissão: Super usuário
        """

        form_class = typeofphoneAssigned
        http_method_names = ['get', 'post']
        model = typeofphone
        success_url = reverse_lazy('equipment_list')
        template_name = 'OS/equipment_assigned_form.html'

class ContractListView(SuperuserRequiredMixin, ListView):  # SUPERUSER
    """
    Lista de equipments atribuidos ao sistema
    Permissão: Super usuário
    """

    context_object_name = 'contract_list'
    http_method_names = ['get']
    model = ContractBasicServices
    template_name = 'OS/contract_list.html'

class ContractCreateView(SuperuserRequiredMixin, CreateView):  # SUPERUSER
    """
    Formulário de atribuição de descrições e serviços de um contrato
    Permissão: Super usuário
    """

    form_class = contractAssigned
    http_method_names = ['get', 'post']
    model = ContractBasicServices
    success_url = reverse_lazy('contract_list')
    template_name = 'OS/contract_assigned_form.html'

class OrgContractListView(OrganizationMixin,
                               AdminRequiredMixin,
                               OrganizationContextMixin,
                               BaseFilterView,
                               ListView):  # ORG
    """
    Lista de ramais
    Permissão: Administrador da organização
    """

    context_object_name = 'basicservice_list'
#    filterset_class = ContractFilter
    http_method_names = ['get']
    model = ContractBasicServices
    ordering = ['created']
    paginate_by = 15
    template_name = 'OS/org_contract_list.html'

#    def get_queryset(self):
#        return super().get_queryset().filter(organization=self.organization)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract_data = self.object_list \
            .filter(organization=self.organization) \
            .values('pk', 'legacyID', 'contractID', 'description', 'org_price_table', 'org_price_table__name')
        contract_map = []
        for contract in contract_data:
            price = Price.objects.get(
                Q(status=1) & Q(table=contract['org_price_table']) & Q(basic_service=contract['legacyID']))
            contract_map.append((contract['legacyID'], contract['contractID'], contract['description'], contract['org_price_table__name'], price.value, contract['pk'] ))
        context['contract_map'] = contract_map
        return context

class OrgContractCreateView(OrganizationMixin,
                                        AdminRequiredMixin,
                                        CreateView):  # ORG
    """
    Lista de solicitações de faixa de ramais
    Permissão: Administrador da organização
    """

    form_class = contractAssigned
    http_method_names = ['get',  'post']
    model = ContractBasicServices
    template_name = 'OS/org_contract_assigned_form.html'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.organization = self.organization
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'Equipments:org_contract_list',
            kwargs={'org_slug': self.organization.slug})

    def get_form_kwargs(self):
        kwargs = super(OrgContractCreateView, self).get_form_kwargs()
        tempslg = self.kwargs['org_slug']
        try:
            kwargs['organization'] = Organization.objects.get(slug=tempslg)
        except Organization.DoesNotExist:
            # We have no object! Do something...
            pass
        kwargs['IsUpdate'] = False
        return kwargs

class OrgContractUpdateView(OrganizationMixin, AdminRequiredMixin, UpdateView):  # ORG
    """
    Formulário de atualização da empresa (cliente)
    Permissão: Administrador da organização
    """

    form_class = contractAssigned
    http_method_names = ['get', 'post']
    model = ContractBasicServices
    template_name = 'OS/org_contract_assigned_form.html'
    query_pk_and_slug = True

    def get_success_url(self):
        return reverse(
            'Equipments:org_contract_list',
            kwargs={'org_slug': self.organization.slug})

    def get_form_kwargs(self):
        kwargs = super(OrgContractUpdateView, self).get_form_kwargs()
        tempslg = self.kwargs['org_slug']
        try:
            kwargs['organization'] = Organization.objects.get(slug=tempslg)
        except Organization.DoesNotExist:
            # We have no object! Do something...
            pass
        kwargs['IsUpdate'] = True
        return kwargs

class OrgEquipmentListView(OrganizationMixin,
                               AdminRequiredMixin,
                               OrganizationContextMixin,
                               BaseFilterView,
                               ListView):  # ORG
    """
    Lista de equipments atribuidos ao sistema
    Permissão: Super usuário
    """

    context_object_name = 'equipment_list'
    http_method_names = ['get']
    model = typeofphone
    template_name = 'OS/equipment_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipment_data = self.object_list \
            .filter(organization=self.organization) \
            .values('pk', 'manufacturer', 'phoneModel', 'servicetype__contractID', 'servicetype__description')
        context['equipment_map'] = equipment_data
        return context

class OrgEquipmentCreateView(OrganizationMixin,
                                        AdminRequiredMixin,
                                        CreateView):  # ORG
    """
    Lista de solicitações de faixa de ramais
    Permissão: Administrador da organização
    """

    form_class = typeofphoneAssigned
    http_method_names = ['get',  'post']
    model = typeofphone
    template_name = 'OS/equipment_assigned_form.html'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.organization = self.organization
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'Equipments:org_equipment_list',
            kwargs={'org_slug': self.organization.slug})

    def get_form_kwargs(self):
        kwargs = super(OrgEquipmentCreateView, self).get_form_kwargs()
        tempslg = self.kwargs['org_slug']
        try:
            kwargs['organization'] = Organization.objects.get(slug=tempslg)
        except Organization.DoesNotExist:
            # We have no object! Do something...
            pass
 #       kwargs['IsUpdate'] = False
        return kwargs

class OrgEquipmentUpdateView(OrganizationMixin, AdminRequiredMixin, UpdateView):  # ORG
        """
        Formulário de atualização da empresa (cliente)
        Permissão: Administrador da organização
        """

        form_class = typeofphoneAssigned
        http_method_names = ['get', 'post']
        model = typeofphone
        template_name = 'OS/equipment_assigned_form.html'
        query_pk_and_slug = True

        def get_success_url(self):
            return reverse(
                'Equipments:equipment_list',
                kwargs={'org_slug': self.organization.slug})

        def get_form_kwargs(self):
            kwargs = super(OrgEquipmentUpdateView, self).get_form_kwargs()
            tempslg = self.kwargs['org_slug']
            try:
                kwargs['organization'] = Organization.objects.get(slug=tempslg)
            except Organization.DoesNotExist:
                # We have no object! Do something...
                pass
#            kwargs['IsUpdate'] = True
            return kwargs