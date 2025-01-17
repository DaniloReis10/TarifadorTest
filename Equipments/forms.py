# django
from django import forms
from django.db.models import Q
from django.db.models import BigIntegerField
from django.db.models import F
from django.db.models.functions import Cast

from phonecalls.models import PriceTable, Price
# local
from .models import Equipment, typeofphone, ContractBasicServices
from extensions.models import ExtensionLine


class OSAssignedForm(forms.ModelForm):  # SUPERUSER

    extension_type = forms.ModelChoiceField(queryset=typeofphone.objects.all().order_by('servicetype').values())
    extension_number = forms.ModelChoiceField(queryset=ExtensionLine.objects.values_list('extension', flat=True).order_by('extension').values())
    class Meta:
        model = Equipment
        fields = ['Dateinstalled', 'OSNumber', 'TagNumber', 'MACAdress', 'IPAddress']
        labels = {
            'Dateinstalled': 'Data de Instalação'
        }
        help_texts = {
            'Dateinstalled': 'Selecione a Data de Instalação'
        }




class typeofphoneAssigned(forms.ModelForm):  # SUPERUSER

    servicetypeNameandContract = forms.ChoiceField(label='Tipo de Serviço e Contrato')
    class Meta:
        model = typeofphone
        fields = [ 'manufacturer', 'phoneModel', 'servicetype']

    def __init__(self,  *args, **kwargs):
        self.organization = kwargs.pop('organization')
        super(typeofphoneAssigned, self).__init__(*args, **kwargs)
        choicelist = []
        try:
            contractlist = ContractBasicServices.objects.filter(organization=self.organization)
            for contract in contractlist:
                choicelist.append((contract.id, contract.description + "  Contract: " + str(contract.contractID)))
        except ContractBasicServices.DoesNotExist:
            pass
        self.fields["servicetypeNameandContract"].choices = choicelist

    def clean(self):
        cleaned_data = super(typeofphoneAssigned, self).clean()
        service = cleaned_data.get("servicetypeNameandContract")
        try:
            servicetp = ContractBasicServices.objects.get(id=service)
            cleaned_data['servicetype'] = servicetp
        except ContractBasicServices.DoesNotExist:
            pass
        return cleaned_data
class contractAssigned(forms.ModelForm):  # SUPERUSER

    org_price_table = forms.ModelChoiceField(queryset=PriceTable.objects.none(), to_field_name="name", label="Tabela de Preço")
    org_price_value = forms.FloatField(label='Preço')
    class Meta:
        model = ContractBasicServices
        fields = ['legacyID', 'contractID', 'description', 'org_price_table']

    def __init__(self,  *args, **kwargs):
        self.organization = kwargs.pop('organization')
        IsUpdate = kwargs.pop('IsUpdate')
        if IsUpdate:
            basiccontract = kwargs['instance']
            try:
                price = Price.objects.get(
                    Q(status=1) & Q(table=basiccontract.org_price_table) & Q(basic_service=basiccontract.legacyID))
                kwargs.update(initial={'org_price_table': basiccontract.org_price_table,
                                   'org_price_value': price.value})
            except Price.DoesNotExist:
                pass
        super(contractAssigned, self).__init__(*args, **kwargs)
        self.fields["org_price_table"].queryset = PriceTable.objects.filter(organization=self.organization)


    def clean(self):
        cleaned_data = super(contractAssigned, self).clean()
        org_price_table = cleaned_data.get("org_price_table")
        if not org_price_table:
            raise forms.ValidationError(
                {'org_price_table': 'Precisa selecionar uma tabela de preços'})
        org_price_value = cleaned_data.get("org_price_value")
        if org_price_value == 0.0:
            raise forms.ValidationError(
                {'org_price_value': 'Precisa ter um valor diferente de 0'})
        legacyID = cleaned_data.get("legacyID")
        try:
            current_org_value = Price.objects.get(Q(status=1) & Q(table=org_price_table) & Q(basic_service=legacyID))
        except Price.DoesNotExist or Price.MultipleObjectsReturned:
            raise forms.ValidationError(
                {'org_price_value': 'Multiplos objetos?'})
        if current_org_value.value != org_price_value:
            current_org_value.value = org_price_value
            current_org_value.save()
        return cleaned_data