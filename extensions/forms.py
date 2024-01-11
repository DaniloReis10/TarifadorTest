# django
from django import forms
from django.db.models import BigIntegerField
from django.db.models import F
from django.db.models.functions import Cast

# local
from .models import ExtensionAssigned
from .models import ExtensionLine
from .models import ExtensionSolicitation
from .utils import make_extension_list
from .utils import make_extension_range

EXTENSION_LIMIT = 3000


class ExtensionAssignedForm(forms.ModelForm):  # SUPERUSER

    class Meta:
        model = ExtensionAssigned
        fields = ['extension_range']
        labels = {
            'extension_range': 'Faixa de Ramais'
        }
        help_texts = {
            'extension_range': 'Ramal Único: 853108XXXX<br>'
                               'Faixa de Ramais: 853108XXXX-853108YYYY'
        }

    def clean(self):
        extension_data = self.cleaned_data.get('extension_range')
        extension_data = extension_data.replace(' ', '').split('-')
        data_size = len(extension_data)

        try:
            extension_data = [int(extension) for extension in extension_data]
        except ValueError:
            raise forms.ValidationError(
                {'extension_range': 'Insira apenas valores númericos de 0 a 9.'})

        if data_size > 2:
            raise forms.ValidationError(
                {'extension_range': 'Insira apenas uma faixa de ramais por solicitação.'})

        extension_begin, extension_end = extension_data
        if extension_end - extension_begin > EXTENSION_LIMIT:
            raise forms.ValidationError(
                {'extension_range': 'Insira uma faixa de ramais menor ou igual a '
                                    f'{EXTENSION_LIMIT} números.'})

        extension_line_list = ExtensionLine.objects \
            .annotate(extension_line=Cast(F('extension'), BigIntegerField()))\
            .filter(extension_line__range=[extension_begin, extension_end]) \
            .order_by('extension_line')

        if extension_line_list.exists():
            extension_list = make_extension_list(f'{extension_begin}-{extension_end}')
            for extension_line in extension_line_list:
                try:
                    extension_list = \
                        extension_list[:extension_list.index(extension_line.extension)] + \
                        extension_list[(extension_list.index(extension_line.extension) + 1):]
                except ValueError:
                    pass
            solicitation_example = make_extension_range(extension_list)
            raise forms.ValidationError(
                {'extension_range': 'Já existem alguns ramais criados nesse range. Os ramais que '
                                    f'estão nesse range podem ser criados: {solicitation_example}'})


class CompanyExtensionSolicitationForm(forms.ModelForm):  # COMPANY
    """
    Formulário de solicitação de faixa de ramais para o centro de custo
    """

    by_quantity = forms.BooleanField(
        label='Solicitando por quantidade', required=False)

    class Meta:
        model = ExtensionSolicitation
        fields = ['extension_range']
        labels = {
            'extension_range': 'Faixas de Ramais'
        }
        help_texts = {
            'extension_range': 'Ramal Único: 853108XXXX<br>'
                               'Faixa de Ramais: 853108XXXX-853108YYYY'
        }

    def __init__(self, organization, *args, **kwargs):
        self.organization = organization
        super().__init__(*args, **kwargs)

    def clean(self):
        extension_range = self.cleaned_data.get('extension_range')
        by_quantity = self.cleaned_data.get('by_quantity')
        extension_range = extension_range.replace(' ', '')
        extension_data = extension_range.split('-')

        try:
            extension_data = [int(extension) for extension in extension_data]
        except ValueError:
            raise forms.ValidationError(
                {'extension_range': 'Insira apenas valores númericos de 0 a 9 e o hífen \'-\''})

        data_size = len(extension_data)
        if by_quantity:
            if data_size > 1:
                raise forms.ValidationError(
                    {'extension_range': 'Insira um único valor numérico 0 a 9 para '
                                        'solicitações por quantidade.'})

            quantity = extension_data[0]
            free_quantity = ExtensionLine.objects \
                .filter(organization_id=self.organization.id, company__isnull=True).count()
            if quantity > EXTENSION_LIMIT or quantity > free_quantity:
                raise forms.ValidationError(
                    {'extension_range': 'Quantidade solicitada indisponivel.'})

            extension_list = ExtensionLine.objects \
                .filter(organization_id=self.organization.id, company__isnull=True) \
                .annotate(extension_line=Cast(F('extension'), BigIntegerField())) \
                .order_by('extension_line') \
                .values_list('extension', flat=True)[:quantity]
            extension_range = make_extension_range(extension_list)
            return {'extension_range': extension_range}

        if data_size > 2:
            raise forms.ValidationError(
                {'extension_range': 'Insira apenas uma faixa de ramais por solicitação.'})

        extension_begin, extension_end = extension_data
        if extension_end - extension_begin > EXTENSION_LIMIT:
            raise forms.ValidationError(
                {'extension_range': 'Quantidade solicitada indisponivel.'})

        if data_size == 2:
            extension_begin, extension_end = extension_data
            data_available = ExtensionLine.objects \
                .annotate(extension_line=Cast(F('extension'), BigIntegerField())) \
                .filter(organization_id=self.organization.id,
                        company__isnull=True,
                        extension_line__range=[extension_begin, extension_end]) \
                .exists()
        else:
            extension = extension_data[0]
            data_available = ExtensionLine.objects \
                .filter(organization_id=self.organization.id,
                        company__isnull=True,
                        extension=extension) \
                .exists()

        if not data_available:
            if data_size == 2:
                raise forms.ValidationError({'extension_range': 'Faixa de ramais indisponível.'})
            else:
                raise forms.ValidationError({'extension_range': 'Ramal indisponível.'})
        return {'extension_range': extension_range}


class OrgExtensionSolicitationForm(forms.ModelForm):  # ORG
    """
    Formulário de solicitação de faixa de ramais para a organização
    """

    by_quantity = forms.BooleanField(
        label='Solicitando por quantidade', required=False)

    class Meta:
        model = ExtensionSolicitation
        fields = ['extension_range']
        labels = {
            'extension_range': 'Faixa de Ramais'
        }
        help_texts = {
            'extension_range': 'Ramal Único: 853108XXXX<br>'
                               'Faixa de Ramais: 853108XXXX-853108YYYY'
        }

    def clean(self):
        extension_range = self.cleaned_data.get('extension_range')
        by_quantity = self.cleaned_data.get('by_quantity')
        extension_range = extension_range.replace(' ', '')
        extension_data = extension_range.split('-')

        try:
            extension_data = [int(extension) for extension in extension_data]
        except ValueError:
            raise forms.ValidationError(
                {'extension_range': 'Insira apenas valores númericos de 0 a 9 e o hífen \'-\''})

        data_size = len(extension_data)
        if by_quantity:
            if data_size > 1:
                raise forms.ValidationError(
                    {'extension_range': 'Insira um único valor numérico 0 a 9 para '
                                        'solicitações por quantidade.'})

            quantity = extension_data[0]
            free_quantity = ExtensionLine.objects \
                .filter(organization__isnull=True).count()
            if quantity > EXTENSION_LIMIT or quantity > free_quantity:
                raise forms.ValidationError(
                    {'extension_range': 'Quantidade solicitada indisponivel.'})

            extension_list = ExtensionLine.objects \
                .filter(organization__isnull=True) \
                .annotate(extension_line=Cast(F('extension'), BigIntegerField())) \
                .order_by('extension_line') \
                .values_list('extension', flat=True)[:quantity]
            extension_range = make_extension_range(extension_list)
            return {'extension_range': extension_range}

        if data_size > 2:
            raise forms.ValidationError(
                {'extension_range': 'Insira apenas uma faixa de ramais por solicitação.'})

        extension_begin, extension_end = extension_data
        if extension_end - extension_begin > EXTENSION_LIMIT:
            raise forms.ValidationError(
                {'extension_range': 'Quantidade solicitada indisponivel.'})

        if data_size == 2:
            extension_begin, extension_end = extension_data
            data_available = ExtensionLine.objects \
                .annotate(extension_line=Cast(F('extension'), BigIntegerField())) \
                .filter(organization__isnull=True,
                        extension_line__range=[extension_begin, extension_end]) \
                .exists()
        else:
            extension = extension_data[0]
            data_available = ExtensionLine.objects \
                .filter(organization__isnull=True,
                        extension=extension) \
                .exists()

        if not data_available:
            if data_size == 2:
                raise forms.ValidationError({'extension_range': 'Faixa de ramais indisponível.'})
            else:
                raise forms.ValidationError({'extension_range': 'Ramal indisponível.'})
        return {'extension_range': extension_range}


class PriceTableCreateForm(forms.Form):

    name = forms.CharField(max_length=255, required=True)

    VC1_value = forms.DecimalField(
        label='Ligações para celular local (VC1)',
        required=True)

    VC2_value = forms.DecimalField(
        label='Ligações para celular na mesma região (VC2)',
        required=True)

    VC3_value = forms.DecimalField(
        label='Ligações para celular em outra área (VC3)',
        required=True)

    LOCAL_value = forms.DecimalField(
        label='Ligações locais para fixo',
        required=True)

    LDN_value = forms.DecimalField(
        label='Ligações DDD para fixo',
        required=True)

    LDI_value = forms.DecimalField(
        label='Ligação internacional',
        required=True)

    def __init__(self, organization, *args, **kwargs):
        self.organization = organization
        super().__init__(*args, **kwargs)
