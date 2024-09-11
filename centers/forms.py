# python
import hashlib

# django
from django import forms
from django.db.models import Q
from django.utils.text import slugify

# project
from charges.constants import COMMUNICATION_SERVICE
from extensions.models import ExtensionLine
from extensions.utils import make_extension_list
from phonecalls.models import PriceTable
# from voip.models import Clients

# local
from .models import Center
from .models import Company
from .models import Sector


class CompanyCreateForm(forms.ModelForm):

    call_pricetable = forms.ModelChoiceField(
        PriceTable.objects.active().filter(servicetype=COMMUNICATION_SERVICE),
        label='Tabela de Preço', required=False)

    def __init__(self, request, organization, *args, **kwargs):
        self.request = request
        self.organization = organization

        super().__init__(*args, **kwargs)
        self.fields['call_pricetable'].queryset = \
            self.fields['call_pricetable'].queryset.filter(organization=self.organization)

    class Meta:
        model = Company
        exclude = [
            'created',
            'modified',
            'slug',
            'organization',
            'service_pricetable',
            'users',
            'status',
            'activate_date',
            'deactivate_date',
            'is_new_contract']

    def save(self,  **kwargs):
        company = super().save(commit=False)
        company.organization = self.organization

        company_slug = slugify(company.name)
        slug = company_slug
        count = 1
        while Company.objects.filter(slug=slug).exists():
            h = hashlib.sha3_512(f'{company.name}-{count}'.encode('utf-8'))
            slug = f'{company_slug[:39]}-{h.hexdigest()}'[:50]
            count += 1
        company.slug = slug
        company.save()
        extension_list = None,
#        extension_list = Clients.objects \
#            .filter(secretaria=company.code) \
#            .values_list('ramal', flat=True)
        if extension_list:
            ExtensionLine.objects.bulk_create([
                ExtensionLine(organization=self.organization, company=company, extension=extension)
                for extension in extension_list])
        return super().save()


class CenterForm(forms.ModelForm):

    class Meta:
        model = Center
        fields = ['name', 'extension_range']
        help_texts = {
            'extension_range': 'Ramal Único: 853108XXXX<br>'
                               'Faixa de Ramais: 853108XXXX-853108YYYY'}

    def __init__(self, organization, company, *args, **kwargs):
        self.organization = organization
        self.company = company

        super().__init__(*args, **kwargs)

    def clean_extension_range(self):
        extension_range = self.cleaned_data.get('extension_range')
        if not extension_range:
            return extension_range

        extension_range = extension_range.replace(' ', '')
        for extension_data in extension_range.split(','):
            try:
                extension_data = [int(extension) for extension in extension_data.split('-')]
            except ValueError:
                raise forms.ValidationError('Insira apenas valores númericos de 0 a 9 e o hífen \'-\'!')

        extension_list = make_extension_list(extension_range)
        extension_list_length = len(extension_list)
        available_extension = self.company.extensionline_set.filter(extension__in=extension_list)
        if self.instance.id:
            available_extension = available_extension.filter(Q(center__isnull=True) | Q(center=self.instance))
        else:
            available_extension = available_extension.filter(center__isnull=True)

        if available_extension.count() != extension_list_length:
            if extension_list_length > 1:
                raise forms.ValidationError('Faixas de ramais indisponível!')
            else:
                raise forms.ValidationError('Ramal indisponível!')

        return extension_range

    def save(self, **kwargs):
        center = super().save(commit=False)
        if not getattr(center, 'organization', None):
            center.organization = self.organization
        if not getattr(center, 'company', None):
            center.company = self.company
        center.save()


class SectorForm(forms.ModelForm):

    class Meta:
        model = Sector
        fields = ['center', 'name', 'extension_range']
        help_texts = {
            'extension_range': 'Ramal Único: 853108XXXX<br>'
                               'Faixa de Ramais: 853108XXXX-853108YYYY'}

    def __init__(self, organization, company, *args, **kwargs):
        self.organization = organization
        self.company = company

        super().__init__(*args, **kwargs)
        if 'center' in self.fields:
            self.fields['center'].queryset = self.company.center_set.all()

    def clean(self):
        cleaned_data = super().clean()
        center = cleaned_data.get('center')
        extension_range = cleaned_data.get('extension_range')

        if not extension_range:
            return cleaned_data

        extension_range = extension_range.replace(' ', '')
        for extension_data in extension_range.split(','):
            try:
                extension_data = [int(extension) for extension in extension_data.split('-')]
            except ValueError:
                raise forms.ValidationError(
                    {'extension_range': 'Insira apenas valores númericos de 0 a 9 e o hífen \'-\'!'})

        extension_list = make_extension_list(extension_range)
        extension_list_length = len(extension_list)
        if self.instance.id:
            available_extension = self.instance.center.extensionline_set \
                .filter(extension__in=extension_list).filter(Q(sector__isnull=True) | Q(sector=self.instance))
        else:
            available_extension = self.company.extensionline_set \
                .filter(center=center, extension__in=extension_list, sector__isnull=True)

        if available_extension.count() != extension_list_length:
            if extension_list_length > 1:
                raise forms.ValidationError({'extension_range': 'Faixas de ramais indisponível!'})
            else:
                raise forms.ValidationError({'extension_range': 'Ramal indisponível!'})

        cleaned_data.update({'extension_range': extension_range})
        return cleaned_data

    def save(self, **kwargs):
        sector = super().save(commit=False)
        if not getattr(sector, 'organization', None):
            sector.organization = self.organization
        if not getattr(sector, 'company', None):
            sector.company = self.company
        sector.save()


class SectorUpdateForm(SectorForm):

    class Meta:
        model = Sector
        fields = ['name', 'extension_range']
