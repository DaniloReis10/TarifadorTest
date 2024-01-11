# django
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.views.generic import ListView
from django.views.generic import UpdateView

# third party
from django_filters.views import BaseFilterView
from organizations.views.mixins import AdminRequiredMixin

# project
from accounts.mixins import OrganizationContextMixin
from accounts.mixins import OrganizationMixin
from centers.mixins import CompanyContextMixin
from centers.mixins import CompanyMembershipRequiredMixin
from centers.mixins import CompanyMixin
from core.views import SuperuserRequiredMixin

# local
from .constants import SOLICITATION_OPENED
from .filters import ExtensionFilter
from .forms import CompanyExtensionSolicitationForm
from .forms import ExtensionAssignedForm
from .forms import OrgExtensionSolicitationForm
from .models import ExtensionAssigned
from .models import ExtensionLine
from .models import ExtensionSolicitation


class ExtensionAssignedListView(SuperuserRequiredMixin, ListView):  # SUPERUSER
    """
    Lista de faixas de ramais atribuidos ao sistema
    Permissão: Super usuário
    """

    context_object_name = 'extension_assigned_list'
    http_method_names = ['get']
    model = ExtensionAssigned
    template_name = 'extensions/extension_assigned_list.html'


class ExtensionAssignedCreateView(SuperuserRequiredMixin, CreateView):  # SUPERUSER
    """
    Formulário de atribuição de faixa de ramais ao sistema
    Permissão: Super usuário
    """

    form_class = ExtensionAssignedForm
    http_method_names = ['get', 'post']
    model = ExtensionAssigned
    success_url = reverse_lazy('extension_list')
    template_name = 'extensions/extension_assigned_form.html'


class CompanyExtensionLineListView(CompanyMixin,
                                   CompanyMembershipRequiredMixin,
                                   CompanyContextMixin,
                                   BaseFilterView,
                                   ListView):  # COMPANY
    """
    Lista de ramais
    Permissão: Membro da empresa
    """

    context_object_name = 'extension_line_list'
    filterset_class = ExtensionFilter
    http_method_names = ['get']
    model = ExtensionLine
    ordering = ['created']
    paginate_by = 15
    template_name = 'extensions/center_extension_list.html'

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.organization, company=self.company)


class OrgExtensionLineListView(OrganizationMixin,
                               AdminRequiredMixin,
                               OrganizationContextMixin,
                               BaseFilterView,
                               ListView):  # ORG
    """
    Lista de ramais
    Permissão: Administrador da organização
    """

    context_object_name = 'extension_line_list'
    filterset_class = ExtensionFilter
    http_method_names = ['get']
    model = ExtensionLine
    ordering = ['created']
    paginate_by = 15
    template_name = 'extensions/org_extension_list.html'

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.organization)


class CompanyExtensionSolicitationListView(CompanyMixin,
                                           CompanyMembershipRequiredMixin,
                                           ListView):  # COMPANY
    """
    Lista de solicitações de faixas de ramais
    Permissão: Membro da empresa
    """

    context_object_name = 'solicitation_list'
    http_method_names = ['get']
    model = ExtensionSolicitation
    ordering = ['created']
    paginate_by = 15
    template_name = 'extensions/center_solicitation_list.html'

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.organization, company=self.company)


class OrgExtensionSolicitationListView(OrganizationMixin,
                                       AdminRequiredMixin,
                                       ListView):  # ORG
    """
    Lista de solicitações de faixa de ramais
    Permissão: Administrador da organização
    """

    context_object_name = 'solicitation_list'
    http_method_names = ['get']
    model = ExtensionSolicitation
    ordering = ['created']
    paginate_by = 15
    template_name = 'extensions/org_solicitation_list.html'

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.organization, company__isnull=True)

    def get_context_data(self, **kwargs):
        company_solicitation_list = self.model.objects \
            .filter(organization=self.organization,
                    company__isnull=False,
                    status=SOLICITATION_OPENED)
        kwargs['company_solicitation_list'] = company_solicitation_list
        return super().get_context_data(**kwargs)


class CompanyExtensionSolicitationCreateView(CompanyMixin,
                                             CompanyMembershipRequiredMixin,
                                             CreateView):  # COMPANY
    """
    Formulário de solicitação de faixa de ramais
    Permissão: Membro da empresa
    """

    form_class = CompanyExtensionSolicitationForm
    http_method_names = ['get', 'post']
    model = ExtensionSolicitation
    template_name = 'extensions/center_solicitation_form.html'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.organization = self.organization
        instance.company = self.company
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'extensions:company_solicitation_list',
            kwargs={'org_slug': self.organization.slug, 'company_slug': self.company.slug})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.organization
        return kwargs


class CompanyExtensionSolicitationUpdateView(CompanyMixin,
                                             CompanyMembershipRequiredMixin,
                                             UpdateView):  # COMPANY
    """
    Formulário de atualização do status da solicitação de faixas de ramais
    Permissão: Membro da empresa
    """
    # TODO segurança
    # TODO Validação de usuário que fez a ação para os tipos de status

    context_object_name = 'solicitation'
    fields = ['status']
    http_method_names = ['get', 'post', 'put', 'patch']
    model = ExtensionSolicitation

    def get_success_url(self):
        return reverse(
            'extensions:company_solicitation_list',
            kwargs={'org_slug': self.organization.slug, 'company_slug': self.company.slug})


class OrgExtensionSolicitationCreateView(OrganizationMixin,
                                         AdminRequiredMixin,
                                         CreateView):  # ORG
    """
    Formulário de solicitação de faixas de ramais
    Permissão: Administrador da organização
    """

    form_class = OrgExtensionSolicitationForm
    http_method_names = ['get', 'post']
    model = ExtensionSolicitation
    template_name = 'extensions/org_solicitation_form.html'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.organization = self.organization
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'extensions:org_solicitation_list',
            kwargs={'org_slug': self.organization.slug})


class OrgExtensionSolicitationUpdateView(OrganizationMixin,
                                         AdminRequiredMixin,
                                         UpdateView):  # ORG
    """
    Formulário de atualização do status da solicitação de faixas de ramais
    Permissão: Administrador da organização
    """
    # TODO segurança
    # TODO Validação de usuário que fez a ação para os tipos de status

    context_object_name = 'solicitation'
    fields = ['status']
    http_method_names = ['get', 'post', 'put', 'patch']
    model = ExtensionSolicitation

    def get_success_url(self):
        return reverse(
            'extensions:org_solicitation_list',
            kwargs={'org_slug': self.organization.slug})
