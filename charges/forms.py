# django
from django import forms

# project
from core.constants import INACTIVE_STATUS
from phonecalls.models import PriceTable

# local
from .constants import PRICE_FIELDS_BASIC_SERVICE_MAP
from .constants import PRICE_FIELDS_CALLTYPE_MAP
from .constants import PRICE_FIELDS_OTHERTYPE_MAP


class ServicePriceTableForm(forms.ModelForm):

    # Serviços de Disponibilização de Acesso a Comunicação Voip

    # Serviço de Acesso Nivel 1
    level_1_access_service_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    level_1_access_service_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Serviço de Acesso Nivel 2
    level_2_access_service_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    level_2_access_service_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Serviço de Acesso Nivel 3
    level_3_access_service_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    level_3_access_service_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Serviço de Acesso Nivel 4
    level_4_access_service_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    level_4_access_service_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Serviço de Acesso Nivel 5
    level_5_access_service_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    level_5_access_service_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Serviço de Acesso Nivel 6
    level_6_access_service_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    level_6_access_service_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Serviço de Acesso sem fio
    wireless_access_service_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    wireless_access_service_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Serviço de acesso via Software
    software_access_service_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    software_access_service_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Serviço de Extensão via software
    software_extension_service_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    software_extension_service_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Serviços de Contact Center

    # Gerência e Operação da Plataforma Básica de Contact Center
    mo_basic_contact_center_platform_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    mo_basic_contact_center_platform_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Gerência e Operação da Plataforma Básica de Gravação
    mo_basic_recording_platform_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    mo_basic_recording_platform_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Gerência e Operação de Posição de Atendimentos
    mo_service_position_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    mo_service_position_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Gerência e Operação de Supervisor
    mo_supervisor_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    mo_supervisor_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Gerência e Operação de Acompanhamento em Tempo Real
    mo_real_time_tracking_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    mo_real_time_tracking_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Gerência e Operação de Canal de Atendimento Automático e Mensagens
    mo_auto_answer_channel_and_messages_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    mo_auto_answer_channel_and_messages_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Gerência e Operação de Posição de Gravação
    mo_recording_position_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    mo_recording_position_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Gerência e Operação de Supervisor de Gravação
    mo_recording_supervisor_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    mo_recording_supervisor_amount = forms.IntegerField(
        label='Quantidade', required=False)

    class Meta:
        model = PriceTable
        fields = ['name']


class ServicePriceTableCreateForm(ServicePriceTableForm):

    pass


class ServicePriceTableUpdateForm(ServicePriceTableForm):

    class Meta:
        model = PriceTable
        fields = ['name', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        price_list = self.instance.price_set.active()
        for price in price_list:
            if price.basic_service not in PRICE_FIELDS_BASIC_SERVICE_MAP:
                continue
            price_field = PRICE_FIELDS_BASIC_SERVICE_MAP[price.basic_service]
            self.fields[f'{price_field}_amount'].initial = price.basic_service_amount
            self.fields[f'{price_field}_price'].initial = price.value

    def clean_status(self):
        status = self.cleaned_data.get('status')
        if status == INACTIVE_STATUS:
            if self.instance.company_set.all().exists():
                raise forms.ValidationError('Não é possivel inativar uma tabela de preço que '
                                            'ainda esteja vinculada a algum Centro de Custo')
        return status


class CallPriceTableForm(forms.ModelForm):

    # Serviços de Comunicação

    # Discagem Local
    LOCAL_price = forms.DecimalField(
        label='Ligações locais para fixo',
        widget=forms.TextInput(attrs={'placeholder': 'R$'}))

    VC1_price = forms.DecimalField(
        label='Ligações para telefones móveis',
        widget=forms.TextInput(attrs={'placeholder': 'R$'}))

    # Longa Distância Nacional


    LDN_price = forms.DecimalField(
        label='Ligações DDD para fixo',
        widget=forms.TextInput(attrs={'placeholder': 'R$'}))

    # Longa Distância Internacial
    LDI_price = forms.DecimalField(
        label='Ligação internacional',
        widget=forms.TextInput(attrs={'placeholder': 'R$'}))

    class Meta:
        model = PriceTable
        fields = ['name']


class CallPriceTableCreateForm(CallPriceTableForm):

    pass


class CallPriceTableUpdateForm(CallPriceTableForm):

    class Meta:
        model = PriceTable
        fields = ['name', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        price_list = self.instance.price_set.active()
        for price in price_list:
            if price.calltype not in PRICE_FIELDS_CALLTYPE_MAP:
                continue
            price_field = PRICE_FIELDS_CALLTYPE_MAP[price.calltype]
            self.fields[f'{price_field}_price'].initial = price.value

    def clean_status(self):
        status = self.cleaned_data.get('status')
        if status == INACTIVE_STATUS:
            if self.instance.company_set.all().exists():
                raise forms.ValidationError('Não é possivel inativar uma tabela de preço que '
                                            'ainda esteja vinculada a algum cliente')
        return status


class OtherPriceTableForm(forms.ModelForm):

    # Serviços Diversos

    UST_price = forms.DecimalField(
        label='Serviços especializados de comunicação VoIP por demanda',
        widget=forms.TextInput(attrs={'placeholder': 'R$'}))

    KM_price = forms.DecimalField(
        label='Serviço de deslocamento para prestar serviço fora da Região Metropolitana de Fortaleza',
        widget=forms.TextInput(attrs={'placeholder': 'R$'}))


    class Meta:
        model = PriceTable
        fields = ['name']


class OtherPriceTableCreateForm(OtherPriceTableForm):

    pass


class OtherPriceTableUpdateForm(OtherPriceTableForm):

    class Meta:
        model = PriceTable
        fields = ['name', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        price_list = self.instance.price_set.active()
        for price in price_list:
            if price.othertype not in PRICE_FIELDS_OTHERTYPE_MAP:
                continue
            price_field = PRICE_FIELDS_OTHERTYPE_MAP[price.othertype]
            self.fields[f'{price_field}_price'].initial = price.value

    def clean_status(self):
        status = self.cleaned_data.get('status')
        if status == INACTIVE_STATUS:
            if self.instance.company_set.all().exists():
                raise forms.ValidationError('Não é possivel inativar uma tabela de preço que '
                                            'ainda esteja vinculada a algum cliente')
        return status
