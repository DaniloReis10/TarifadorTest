# django
from django import forms

# project
from core.constants import INACTIVE_STATUS
from phonecalls.models import PriceTable

# local
from .constants import PRICE_FIELDS_BASIC_SERVICE_MAP
from .constants import PRICE_FIELDS_BASIC_SERVICE_MAP_NEW
from .constants import PRICE_FIELDS_CALLTYPE_MAP_NEW
from .constants import PRICE_FIELDS_CALLTYPE_MAP
from .constants import PRICE_FIELDS_OTHERTYPE_MAP
from phonecalls.constants import NEW_CONTRACT



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

    # Serviço de Acesso Wifi
    wifi_access_service_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    wifi_access_service_amount = forms.IntegerField(
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
    # Gerência e Operação de Qualidade de Gravação
    mo_quality_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    mo_quality_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Gerência e Operação de Detecção de Emoção
    mo_emotion_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    mo_emotion_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Gerência e Operação de Tradução para Texto
    mo_translation_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    mo_translation_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Gerência e Operação de Aprendizagem e Avaliação
    mo_learning_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    mo_learning_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Assistente Virtual Cognitivo
    CHATBOT_LICENSE_SERVICE_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    CHATBOT_LICENSE_SERVICE_amount = forms.IntegerField(
        label='Quantidade', required=False)

    # Sustentação e Atualização da Solução de Chatbot
    CHATBOT_MAINTENANCE_SERVICE_price = forms.DecimalField(
        label='Valor', widget=forms.TextInput(attrs={'placeholder': 'R$'}), required=False)

    CHATBOT_MAINTENANCE_SERVICE_amount = forms.IntegerField(
        label='Quantidade', required=False)

    class Meta:
        model = PriceTable
        fields = ['name']



class ServicePriceTableCreateForm(ServicePriceTableForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ServicePriceTableUpdateForm(ServicePriceTableForm):

    class Meta:
        model = PriceTable
        fields = ['name', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        price_list = self.instance.price_set.active()

# The master (ETICE-SEATIC) has no company pointing to it


        if (self.instance.service_company_set.first() is None or self.instance.service_company_set.first().is_new_contract == NEW_CONTRACT):
            price_basic_service_map =  PRICE_FIELDS_BASIC_SERVICE_MAP_NEW
            del self.fields['level_6_access_service_price']
            del self.fields['level_6_access_service_amount']
        else:
            price_basic_service_map = PRICE_FIELDS_BASIC_SERVICE_MAP
            del self.fields['wifi_access_service_price']
            del self.fields['wifi_access_service_amount']
        for price in price_list:
            if price.basic_service not in price_basic_service_map:
                continue
            price_field = price_basic_service_map[price.basic_service]
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

    VC2_price = forms.DecimalField(
        label='Ligações para celular na mesma região (VC2)',
        widget=forms.TextInput(attrs={'placeholder': 'R$'}))

    VC3_price = forms.DecimalField(
        label='Ligações para celular em outra área (VC3)',
        widget=forms.TextInput(attrs={'placeholder': 'R$'}))

    VC2_PMF_price = forms.DecimalField(
        label='Ligações para 0800 de fixo',
        widget=forms.TextInput(attrs={'placeholder': 'R$'}))

    VC3_PMF_price = forms.DecimalField(
        label='Ligações para 0800 de móvel',
        widget=forms.TextInput(attrs={'placeholder': 'R$'}))

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
    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(CallPriceTableCreateForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['VC2_price'].required = False
        self.fields['VC3_price'].required = False
        self.fields['VC2_PMF_price'].required = False
        self.fields['VC3_PMF_price'].required = False


class CallPriceTableUpdateForm(CallPriceTableForm):

    class Meta:
        model = PriceTable
        fields = ['name', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        price_list = self.instance.price_set.active()
        if ( self.instance.call_company_set.first() is None or self.instance.call_company_set.first().is_new_contract == NEW_CONTRACT):
            call_service_map = PRICE_FIELDS_CALLTYPE_MAP_NEW
            del self.fields['VC2_price']
            del self.fields['VC3_price']
        else:
            call_service_map = PRICE_FIELDS_CALLTYPE_MAP

        for price in price_list:
            if price.calltype not in call_service_map:
                continue
            price_field = call_service_map[price.calltype]
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
