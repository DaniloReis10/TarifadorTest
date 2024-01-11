# django
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import ListView
from django.views.generic import UpdateView

# thrid party
# from organizations import views as org_views
from organizations.views import default as org_views
from organizations.views import mixins as org_mixins
from organizations.models import Organization

# project
from core.views import SuperuserRequiredMixin
from extensions.constants import SOLICITATION_OPENED
from extensions.models import ExtensionSolicitation

# local
from .forms import OrganizationCreateForm
from .forms import OrganizationForm
from .forms import OrganizationUserCreateForm
from .forms import ProfileForm
from .models import OrganizationSetting


class OrganizationMixin(org_mixins.OrganizationMixin):

    def get_organization(self):
        if hasattr(self, 'organization'):
            return self.organization
        org_slug = self.kwargs.get('org_slug', None)
        self.organization = get_object_or_404(self.get_org_model(), slug=org_slug)
        return self.organization


class OrganizationList(SuperuserRequiredMixin,
                       ListView):
    """
    Lista de organizações
    Permissão: Super usuário
    """

    context_object_name = 'organizations'
    model = Organization

    def get_context_data(self, **kwargs):
        solicitation_list = ExtensionSolicitation.objects \
            .filter(company__isnull=True, status=SOLICITATION_OPENED)
        kwargs['solicitation_list'] = solicitation_list
        return super().get_context_data(**kwargs)


class OrganizationCreate(SuperuserRequiredMixin,
                         org_views.OrganizationCreate):
    """
    Formulário de criação de novas organizações
    Permissão: Super usuário
    """

    form_class = OrganizationCreateForm


class OrganizationDetail(OrganizationMixin,
                         org_mixins.AdminRequiredMixin,
                         org_views.OrganizationDetail):
    """
    Página de detalhes da organização
    Permissão: Administrador da organização
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        organization_users = self.organization.organization_users \
            .select_related('user', 'user__profile', 'organizationowner')

        company_list = self.organization.company_set.active() \
            .prefetch_related('users') \
            .select_related('service_pricetable', 'call_pricetable')
        if not self.organization.is_admin(self.request.user) and \
           not self.request.user.is_superuser:
            company_list = company_list.filter(users=self.request.user)

        context.update({
            'organization': self.organization,
            'organization_users': organization_users,
            'company_list': company_list})
        return context


class OrganizationUpdate(OrganizationMixin,
                         org_views.OrganizationUpdate):
    """
    Formulário de atualização da organização
    Permissão: Administrador da organização
    """

    form_class = OrganizationForm

    def form_valid(self, form):
        settings, created = OrganizationSetting.objects \
            .get_or_create(organization=self.organization)
        settings.logo = form.cleaned_data['logo']
        settings.email = form.cleaned_data['email']
        settings.call_pricetable = form.cleaned_data['call_pricetable']
        settings.zip_code = form.cleaned_data['zip_code']
        settings.city = form.cleaned_data['city']
        settings.state = form.cleaned_data['state']
        settings.country = form.cleaned_data['country']
        settings.street = form.cleaned_data['street']
        settings.street_number = form.cleaned_data['street_number']
        settings.neighborhood = form.cleaned_data['neighborhood']
        settings.complement = form.cleaned_data['complement']
        settings.save()
        return super().form_valid(form)


class OrganizationUserList(OrganizationMixin,
                           org_views.OrganizationUserList):
    """
    Lista de usuários da organização
    Permissão: Membro da organização
    """
    pass


class OrganizationUserCreate(OrganizationMixin,
                             org_views.OrganizationUserCreate):
    """
    Formulário de criação de usuários para organização
    Permissão: Administrador da organização
    """

    form_class = OrganizationUserCreateForm

    def get_success_url(self):
        return reverse('organization_detail', kwargs={'org_slug': self.organization.slug})


class OrganizationUserDetail(OrganizationMixin,
                             org_views.OrganizationUserDetail):
    pass


class OrganizationUserUpdate(OrganizationMixin,
                             org_views.OrganizationUserUpdate):
    pass


class OrganizationUserDelete(OrganizationMixin,
                             org_views.OrganizationUserDelete):
    pass


class OrganizationProfileUpdateView(LoginRequiredMixin,
                                    OrganizationMixin,
                                    org_mixins.AdminRequiredMixin,
                                    UpdateView):

    context_object_name = 'profile'
    form_class = ProfileForm
    http_method_names = ['get', 'post', 'put', 'patch']
    model = User
    template_name = 'accounts/profile_form.html'

    def get_queryset(self):
        return self.get_organization().users.all()

    def get_object(self):
        queryset = self.get_queryset()

        pk = self.kwargs.get(self.pk_url_kwarg)
        queryset = queryset.filter(pk=pk)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_(f"No { queryset.model._meta.verbose_name } found matching the query"))
        return obj

    def get_success_url(self):
        user = self.get_object()
        return reverse('org_profile_update', args=[self.organization.slug, user.pk])


class ProfileUpdateView(LoginRequiredMixin,
                        UpdateView):

    context_object_name = 'profile'
    form_class = ProfileForm
    http_method_names = ['get', 'post', 'put', 'patch']
    model = User
    success_url = 'profile_update'
    template_name = 'accounts/profile_form.html'

    def get_object(self):
        return self.request.user
