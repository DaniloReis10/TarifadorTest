# django
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

# third party
from django_filters.views import BaseFilterView
from organizations.views.mixins import AdminRequiredMixin
from organizations.views.mixins import MembershipRequiredMixin

# project
from accounts.mixins import OrganizationMixin
from extensions.utils import make_extension_range

# local
from .filters import CompanyFilter
from .filters import SectorFilter
from .forms import CenterForm
from .forms import CompanyCreateForm
from .forms import SectorForm
from .forms import SectorUpdateForm
from .mixins import CompanyMembershipRequiredMixin
from .mixins import CompanyMixin
from .models import Center
from .models import Company
from .models import Sector
from .tasks import update_center_phonecalls
from .tasks import update_sector_phonecalls

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

class CompanyListView(OrganizationMixin,
                      MembershipRequiredMixin,
                      BaseFilterView,
                      ListView):  # COMPANY
    """
    Lista de empresas (clientes)
    Permissão: Membro da empresa
    """

    context_object_name = 'company_list'
    filterset_class = CompanyFilter
    http_method_names = ['get']
    model = Company
    ordering = ['-modified']
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().active().select_related('service_pricetable', 'call_pricetable')
        if self.request.user.is_superuser or self.organization.is_admin(self.request.user):
            return queryset.filter(organization=self.organization)
        return queryset.filter(organization=self.organization, users=self.request.user)

    def get(self, request, *args, **kwargs):
        if is_ajax(request=request):
            self.object_list = self.get_queryset()
            options = []
            for company in self.object_list:
                options.append({'text': company.name, 'value': company.slug})
            return JsonResponse({'options': options})
        return super().get(request, *args, **kwargs)


class CompanyCreateView(OrganizationMixin, AdminRequiredMixin, CreateView):  # ORG
    """
    Formulário de criação de uma nova empresa (novo cliente)
    Permissão: Administrador da organização
    """

    form_class = CompanyCreateForm
    http_method_names = ['get', 'post']
    model = Company

    def get_success_url(self):
        return reverse('centers:list', kwargs={'org_slug': self.organization.slug})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'request': self.request,
            'organization': self.organization})
        return kwargs


class CompanyUpdateView(OrganizationMixin, AdminRequiredMixin, UpdateView):  # ORG
    """
    Formulário de atualização da empresa (cliente)
    Permissão: Administrador da organização
    """

    context_object_name = 'company'
    fields = [
        'status', 'name', 'code', 'phone', 'cnpj', 'description',
        'logo', 'zip_code', 'country', 'state', 'city', 'call_pricetable',
        'street', 'street_number', 'neighborhood', 'complement', 'is_new_contract']
    http_method_names = ['get', 'post']
    model = Company
    query_pk_and_slug = True

    def get_success_url(self):
        company = self.get_object()
        return reverse(
            'centers:update',
            kwargs={'org_slug': self.organization.slug, 'slug': company.slug})


class CenterListView(CompanyMixin,
                     CompanyMembershipRequiredMixin,
                     ListView):  # COMPANY
    """
    Lista de centros de custo
    Permissão: Membro da empresa
    """

    context_object_name = 'center_list'
    http_method_names = ['get']
    model = Center
    ordering = ['modified']
    paginate_by = 15

    def get_queryset(self):
        return super().get_queryset().filter(company=self.company)

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            self.object_list = self.get_queryset()
            options = []
            for center in self.object_list:
                options.append({'text': center.name, 'value': center.id})
            return JsonResponse({'options': options})
        return super().get(request, *args, **kwargs)


class CenterDetailView(CompanyMixin,
                       CompanyMembershipRequiredMixin,
                       DetailView):  # COMPANY
    """
    Detalhe do centro de custo
    Permissão: Membro da empresa
    """

    http_method_names = ['get']
    model = Center
    pk_url_kwarg = 'center_pk'

    def get_queryset(self):
        return super().get_queryset().filter(company=self.company)

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            center = self.get_object()
            extension_list = center.extensionline_set.filter(sector__isnull=True).values_list('extension', flat=True)
            return JsonResponse({'available_ext_range': make_extension_range(list(extension_list))})
        return super().get(request, *args, **kwargs)


class CenterCreateUpdateView:

    form_class = CenterForm
    http_method_names = ['get', 'post']
    model = Center

    def get_context_data(self, **kwargs):
        extension_list = self.company.extensionline_set.filter(center__isnull=True).values_list('extension', flat=True)
        kwargs['available_ext_range'] = make_extension_range(list(extension_list))
        return super().get_context_data(**kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'organization': self.organization,
                       'company': self.company})
        return kwargs

    def get_success_url(self):
        return reverse('centers:center_list', kwargs={'org_slug': self.organization.slug,
                                                      'company_slug': self.company.slug})


class CenterCreateView(CompanyMixin,
                       CompanyMembershipRequiredMixin,
                       CenterCreateUpdateView,
                       CreateView):  # COMPANY
    """
    Formulário de criação de um centro de custo
    Permissão: Membro da empresa
    """

    def form_valid(self, form):
        self.object = form.save()
        update_center_phonecalls.apply_async(args=[form.instance.id, True])
        return super().form_valid(form)


class CenterUpdateView(CompanyMixin,
                       CompanyMembershipRequiredMixin,
                       CenterCreateUpdateView,
                       UpdateView):  # COMPANY
    """
    Formulário de atualização de um centro de custo
    Permissão: Membro da empresa
    """

    context_object_name = 'center'
    pk_url_kwarg = 'center_pk'

    def form_valid(self, form):
        self.object = form.save()
        update_center_phonecalls.apply_async(args=[form.instance.id, False])
        return super().form_valid(form)


class CenterDeleteView(CompanyMixin,
                       CompanyMembershipRequiredMixin,
                       DeleteView):  # COMPANY
    """
    Formulário de deleção de um centro de custo
    Permissão: Membro da empresa
    """

    model = Center
    pk_url_kwarg = 'center_pk'

    def get_success_url(self):
        return reverse('centers:center_list', kwargs={'org_slug': self.organization.slug,
                                                      'company_slug': self.company.slug})


class SectorListView(CompanyMixin,
                     CompanyMembershipRequiredMixin,
                     BaseFilterView,
                     ListView):  # COMPANY
    """
    Lista de setores
    Permissão: Membro da empresa
    """

    context_object_name = 'sector_list'
    filterset_class = SectorFilter
    http_method_names = ['get']
    model = Sector
    ordering = ['center', 'modified']
    paginate_by = 15

    def get_queryset(self):
        return super().get_queryset().filter(company=self.company)

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            filterset_class = self.get_filterset_class()
            self.filterset = self.get_filterset(filterset_class)

            if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
                self.object_list = self.filterset.qs
            else:
                self.object_list = self.filterset.queryset.none()

            options = []
            for sector in self.object_list:
                options.append({'text': sector.name, 'value': sector.id})
            return JsonResponse({'options': options})
        return super().get(request, *args, **kwargs)


class SectorCreateUpdateView:
    form_class = SectorForm
    http_method_names = ['get', 'post']
    model = Sector

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'organization': self.organization,
                       'company': self.company})
        return kwargs

    def get_success_url(self):
        return reverse('centers:sector_list', kwargs={'org_slug': self.organization.slug,
                                                      'company_slug': self.company.slug})


class SectorCreateView(CompanyMixin,
                       CompanyMembershipRequiredMixin,
                       SectorCreateUpdateView,
                       CreateView):  # COMPANY
    """
    Formulário de criação de um setor
    Permissão: Membro da empresa
    """

    def form_valid(self, form):
        self.object = form.save()
        update_sector_phonecalls.apply_async(args=[form.instance.id, True])
        return super().form_valid(form)


class SectorUpdateView(CompanyMixin,
                       CompanyMembershipRequiredMixin,
                       SectorCreateUpdateView,
                       UpdateView):  # COMPANY
    """
    Formulário de atualização de um setor
    Permissão: Membro da empresa
    """

    context_object_name = 'sector'
    form_class = SectorUpdateForm
    pk_url_kwarg = 'sector_pk'

    def form_valid(self, form):
        self.object = form.save()
        update_sector_phonecalls.apply_async(args=[form.instance.id, False])
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        extension_list = self.object.center.extensionline_set \
            .filter(sector__isnull=True).values_list('extension', flat=True)
        kwargs['available_ext_range'] = make_extension_range(list(extension_list))
        return super().get_context_data(**kwargs)


class SectorDeleteView(CompanyMixin,
                       CompanyMembershipRequiredMixin,
                       DeleteView):  # COMPANY
    """
    Formulário de deleção de um setor
    Permissão: Membro da empresa
    """

    model = Sector
    pk_url_kwarg = 'sector_pk'

    def get_success_url(self):
        return reverse('centers:sector_list', kwargs={'org_slug': self.organization.slug,
                                                      'company_slug': self.company.slug})
