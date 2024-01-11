# django
from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site

# third party
from cities_light.models import City
from cities_light.models import Country
from cities_light.models import Region
from organizations.models import Organization
from organizations.models import OrganizationOwner
from organizations.models import OrganizationUser
from phonecalls.models import PriceTable
from phonenumber_field.formfields import PhoneNumberField

# project
from centers.models import Company
from centers.models import CompanyUser
from core.utils import invite_by_email
from core.utils import make_random_password
from core.utils import make_username

# local
from .models import OrganizationSetting
from .models import Profile


class OrganizationCreateForm(forms.ModelForm):

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    class Meta:
        model = Organization
        exclude = ['users', 'is_active']
        help_texts = {
            'name': '',
            'slug': ''
        }


class OrganizationForm(forms.ModelForm):

    email = forms.EmailField(
        required=False)

    logo = forms.ImageField(
        required=False)

    owner = forms.ModelChoiceField(
        Profile.objects.all(), label='Proprietário', required=False)

    call_pricetable = forms.ModelChoiceField(
        PriceTable.objects.all(), label='Tabela de Preço', required=False)

    zip_code = forms.CharField(
        label='CEP', required=False)

    city = forms.ModelChoiceField(
        City.objects.all(), label='Cidade', required=False)

    state = forms.ModelChoiceField(
        Region.objects.all(), label='Estado', required=False)

    country = forms.ModelChoiceField(
        Country.objects.all(), label='Pais', required=False)

    street = forms.CharField(
        label='Endereço', required=False)

    street_number = forms.CharField(
        label='Numero', required=False)

    neighborhood = forms.CharField(
        label='Bairro', required=False)

    complement = forms.CharField(
        label='Complemento', required=False)

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
        settings = self.instance.settings

        self.fields['call_pricetable'].queryset = \
            self.fields['call_pricetable'].queryset.filter(organization__isnull=True)

        profile_id_list = self.instance.users \
            .filter(organizations_organizationuser__is_admin=True, is_active=True)\
            .values_list('profile', flat=True)
        self.fields['owner'].queryset = \
            self.fields['owner'].queryset.filter(id__in=profile_id_list)
        if hasattr(self.instance, 'owner'):
            self.fields['owner'].initial = self.instance.owner.organization_user.user

        self.fields['email'].initial = settings.email
        self.fields['logo'].initial = settings.logo
        self.fields['call_pricetable'].initial = settings.call_pricetable
        self.fields['zip_code'].initial = settings.zip_code
        self.fields['city'].initial = settings.city
        self.fields['state'].initial = settings.state
        self.fields['country'].initial = settings.country
        self.fields['street'].initial = settings.street
        self.fields['street_number'].initial = settings.street_number
        self.fields['neighborhood'].initial = settings.neighborhood
        self.fields['complement'].initial = settings.complement

    class Meta:
        model = Organization
        exclude = ['users']
        labels = {
            'email': 'E-mail',
            'is_active': 'Ativa',
            'name': 'Nome'
        }

    def save(self):
        owner = self.cleaned_data['owner']

        if hasattr(self.instance, 'owner'):
            if owner.user != self.instance.owner.organization_user.user:
                org_user = self.instance.organization_users.get(user=owner.user)
                self.instance.change_owner(org_user)
        elif owner:
            org_user = self.instance.organization_users.get(user=owner.user)
            OrganizationOwner.objects.create(
                organization_user=org_user, organization=self.instance)
        return super().save()

    def clean_owner(self):
        owner = self.cleaned_data['owner']
        if not owner:
            return owner
        validation_error = forms.ValidationError(
            'Somente o proprietário da organização ou administrador '
            'do sistema podem alterar a propriedade')
        if hasattr(self.instance, 'owner'):
            if owner != self.instance.owner.organization_user.user.profile:
                if self.request.user != self.instance.owner.organization_user.user or \
                   not self.request.user.is_superuser:
                    raise validation_error
        elif not self.request.user.is_superuser:
            raise validation_error
        return owner


class OrganizationUserCreateForm(forms.ModelForm):
    is_admin = forms.BooleanField(label='Administrador', required=False)
    is_owner = forms.BooleanField(label='Proprietário', required=False)
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        label='Empresa',
        empty_label='Selecione a Empresa',
        required=False)

    def __init__(self, request, organization, *args, **kwargs):
        self.request = request
        self.organization = organization
        super().__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ['email']
        labels = {
            'email': 'E-mail'
        }

    def save(self):
        email = self.cleaned_data['email']
        is_admin = self.cleaned_data['is_admin']
        is_owner = self.cleaned_data['is_owner']

        username = make_username(email)
        user, created = User.objects.get_or_create(username=username, email=email)
        if created:
            password = make_random_password(length=15)
            user.set_password(password)
            user.save()
            if self.cleaned_data.get('company'):
                company = self.cleaned_data.get('company')
                company_user = CompanyUser(user=user, company=company)
                company_user.save()

            invite_by_email(
                self.organization,
                user,
                {
                    'domain': get_current_site(self.request),
                    'organization': self.organization,
                    'password': password,
                    'sender': self.request.user
                }
            )

        org_user, created = OrganizationUser.objects.get_or_create(
            user=user, organization=self.organization)
        if is_admin:
            org_user.is_admin = is_admin
            org_user.save()
        if is_owner:
            org_user.is_admin = True
            org_user.save()
            OrganizationOwner.objects.create(
                organization_user=org_user, organization=self.organization)
        return user

    def clean_email(self):
        email = self.cleaned_data['email']
        if self.organization.users.filter(email=email):
            raise forms.ValidationError(
                'Já existe um membro da organização com este endereço de e-mail!')
        return email

    def clean_is_owner(self):
        is_owner = self.cleaned_data['is_owner']
        if is_owner:
            if not self.request.user.is_superuser:
                raise forms.ValidationError(
                    'Somente o administrador do sistema pode criar proprietários!')
            if hasattr(self.organization, 'owner'):
                raise forms.ValidationError(
                    'Essa organização já tem um proprietário!')
        return is_owner


class OrganizationSettingsForm(forms.ModelForm):

    logo = forms.ImageField(required=False)

    class Meta:
        model = OrganizationSetting
        fields = ['logo', 'email', 'call_pricetable']


class ProfileForm(UserChangeForm):
    # avatar = forms.ImageField(required=False)
    phone = PhoneNumberField(label='Telefone', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        profile = self.instance.profile
        # self.fields['avatar'].initial = profile.avatar
        self.fields['phone'].initial = profile.phone

    def save(self):
        super().save()
        profile = self.instance.profile
        # profile.avatar = self.cleaned_data.get('avatar')
        profile.phone = self.cleaned_data.get('phone')
        profile.save()

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'username']
