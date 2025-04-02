# django
from django import forms
from django.db.models import Q
import datetime
from django.db.models import BigIntegerField
from django.db.models import F
from django.db.models.functions import Cast

from phonecalls.models import PriceTable, Price
from centers.models import Center, Sector
# local
from .models import Equipment, typeofphone, ContractBasicServices
from extensions.models import ExtensionLine


class OSAssignedForm(forms.ModelForm):  # SUPERUSER

    basic_service = forms.ChoiceField(label='Tipo de serviço', required=False)
    contract_number = forms.ChoiceField(label='Contrato', required=False)
    extensionNumber = forms.ModelChoiceField(queryset=ExtensionLine.objects\
                                              .all()\
                                              .order_by('extension'), to_field_name="extension", label='Ramal')
    center = forms.ModelChoiceField(queryset=Center.objects.none(), to_field_name="name", label='Centro de Custo', required=False)
    #contract = forms.ModelChoiceField(queryset=ContractBasicServices.objects.all(),  required=False)
    sector = Sector.objects.none()
    class Meta:
        model = Equipment
        fields = [ 'extensionNumber', 'Dateinstalled', 'OSNumber', 'TagNumber', 'MACAdress', 'IPAddress', 'equiptype', 'center']
        labels = {
            'Dateinstalled': 'Data de Instalação'
        }
        help_texts = {
            'Dateinstalled': 'Selecione a Data de Instalação'
        }

    def __init__(self,  *args, **kwargs):
        self.organization = kwargs.pop('organization')
        self.company = kwargs.pop('company')
        super(OSAssignedForm, self).__init__(*args, **kwargs)
        #if self.is_bound:
        #    descript = typeofphone.objects.get(id=int(kwargs['data']['typeofservice']))
        #    servicetp = ContractBasicServices.objects.get(contract_number=kwargs['data']['contract'], description=descript.servicetype.description)
        #    phone = typeofphone.objects.get(servicetype=servicetp)
        #    self.fields['equiptype'] = phone
        #    return
        self.fields["center"].queryset = Center.objects.filter(Q(organization=self.organization)& \
                                                  Q(company=self.company))
        choicelist = []
        try:
            contractlist = (ContractBasicServices.objects.filter(organization=self.organization)\
                            .order_by('contractID').values_list('contractID', flat=True).distinct())
            for contract in contractlist:
                choicelist.append((contract, contract))
        except ContractBasicServices.DoesNotExist:
            pass
        self.fields["contract_number"].choices = choicelist
        choicelist_desc = []
        try:
            contractlist = ContractBasicServices.objects.all().order_by('contractID')\
                .values_list('description', flat=True).distinct()
            n = 0
            for contract in contractlist:
                choicelist_desc.append((n, contract))
                n += 1
        except ContractBasicServices.DoesNotExist:
            pass
        self.fields["Dateinstalled"].required = False
        #self.fields["contract"].required = False
        #self.fields["contract"].initial = ContractBasicServices.objects.all().first()
        self.fields["basic_service"].choices = choicelist_desc

    def clean(self):
        cleaned_data = super(OSAssignedForm, self).clean()
        contract_number = self.data["typeofservice"]
        equip = self.data["equipservice"]
        cleaned_data['Dateinstalled'] = datetime.datetime.fromisoformat(self.data["install_date"])
        # Will need to check validation Errors Here
        try:
            contractobj = ContractBasicServices.objects.get(id=contract_number)
            cleaned_data['contract'] = contractobj
        except ContractBasicServices.DoesNotExist:
            raise forms.ValidationError(
                {'contract_number': 'Este contrato não possue esta linha de tipo'})
        try:
            phone = typeofphone.objects.get(id=equip)
            cleaned_data['equiptype'] = phone
        except typeofphone.DoesNotExist:
            raise forms.ValidationError(
                {'contract_number': 'Este contrato não possue esta linha de tipo'})
        extension = cleaned_data['extensionNumber']
        extension.organization = self.organization
        extension.company = self.company
        if cleaned_data["center"]:
            extension.center = cleaned_data["center"]
        extension.save()        # Obs: If I do like this I lose info about the past. Anyway ....
        return cleaned_data




class typeofphoneAssigned(forms.ModelForm):  # SUPERUSER

    servicetypeNameandContract = forms.MultipleChoiceField( label='Tipo de Serviço e Contrato')
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
        services = self.cleaned_data['servicetypeNameandContract']
        try:
            servicetp = ContractBasicServices.objects.filter(id__in=services)
            self.cleaned_data['servicetype'] = servicetp
        except ContractBasicServices.DoesNotExist:
            raise forms.ValidationError(
                {'servicetype': 'Este contrato não possue esta linha de tipo'})
        return cleaned_data






class contractAssigned(forms.ModelForm):  # SUPERUSER

    org_price_table = forms.ModelChoiceField(queryset=PriceTable.objects.none(), to_field_name="name", label="Tabela de Preço")
    org_price_value = forms.FloatField(label='Preço')
    class Meta:
        model = ContractBasicServices
        fields = ['legacyID', 'contractID', 'description', 'org_price_table', 'is_subcontract']

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
        self.fields['is_subcontract'].label = 'Subcontrato'
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