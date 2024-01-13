# python
import pytz

from decimal import Decimal

# django
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

# third party
from django_extensions.db.models import TimeStampedModel
from django_extensions.db.models import ActivatorModel
from organizations.models import Organization

# project
from centers.models import Center
from centers.models import Company
from centers.models import Sector
from charges.constants import BASIC_SERVICE_CHOICES
from charges.constants import SERVICE_TYPE_CHOICES
from core.constants import INACTIVE_STATUS
from extensions.models import ExtensionLine

# local
from .constants import CALLTYPE_CHOICES
from .constants import OTHERTYPE_CHOICES
from .constants import PABX_CHOICES
from .constants import SERVICE_CHOICES
from .constants import VC1, VC2, VC3, LOCAL, LDN, LDI


class PriceTable(TimeStampedModel, ActivatorModel):
    """
    Tabela de Valores
    Modelo para agrupar valores e associar a um centro de custo e/ou organização
    Contém dados de identificação da organização, tipo de serviço
    """

    organization = models.ForeignKey(
        Organization, verbose_name='Organização', on_delete=models.CASCADE, null=True, blank=True)

    name = models.CharField(
        verbose_name='Nome', max_length=255)

    servicetype = models.IntegerField(
        verbose_name='Tipo de Serviço', choices=SERVICE_TYPE_CHOICES)

    class Meta:
        verbose_name = 'Tabela de Valores'
        verbose_name_plural = 'Tabelas de Valores'

    def __str__(self):
        return self.name


class Price(TimeStampedModel, ActivatorModel):
    """
    Preço
    Modelo para registro de valores por tipo de chamada ou serviço
    Contém dados de identificação da tabela, tipo de chamada ou serviço e o valor
    """

    table = models.ForeignKey(
        PriceTable, verbose_name='Tabela de Valores', on_delete=models.CASCADE)

    calltype = models.IntegerField(
        'Tipo de Chamada', choices=CALLTYPE_CHOICES, null=True, blank=True)

    othertype = models.IntegerField(
        'Tipo de Serviço Diverso', choices=OTHERTYPE_CHOICES, null=True, blank=True)

    basic_service = models.IntegerField(
        'Tipo de Serviço Básico', choices=BASIC_SERVICE_CHOICES, null=True, blank=True)

    basic_service_amount = models.IntegerField(
        'Quantidade de Serviço Básico', null=True, blank=True)

    value = models.DecimalField(
        'Preço', max_digits=20, decimal_places=4)

    class Meta:
        verbose_name = 'Preço'
        verbose_name_plural = 'Preços'

    def __str__(self):
        return f"{self.table} - {self.value}"

    def inactive(self):
        self.status = INACTIVE_STATUS
        self.deactivate_date = timezone.now()
        self.save()


class Phonecall(TimeStampedModel):
    """
    Chamada
    Modelo para registro de chamadas, sua classificação e identificação
    Contém dados da chamada com informações que vem da central,
      ramal associado, organização, empresa, centro de custo e setor,
      classificação por tipo de chamada e serviço, números, duração e tabela de valores
    """

    organization = models.ForeignKey(
        Organization, verbose_name='Organização', on_delete=models.SET_NULL, blank=True, null=True)

    company = models.ForeignKey(
        Company, verbose_name='Empresa', on_delete=models.SET_NULL, blank=True, null=True)

    center = models.ForeignKey(
        Center, verbose_name='Centro de Custo', on_delete=models.SET_NULL, blank=True, null=True)

    sector = models.ForeignKey(
        Sector, verbose_name='Setor', on_delete=models.SET_NULL, blank=True, null=True)

    extension = models.ForeignKey(
        ExtensionLine, verbose_name='Ramal', on_delete=models.SET_NULL, blank=True, null=True)

    # classificação
    pabx = models.IntegerField(
        'Classificação PABX', choices=PABX_CHOICES, db_index=True)

    inbound = models.BooleanField(
        'Chamada Entrante', default=True, db_index=True)

    internal = models.BooleanField(
        'Chamada Interna', default=False, db_index=True)

    calltype = models.IntegerField(
        'Tipo de Chamada', choices=CALLTYPE_CHOICES, db_index=True)

    service = models.IntegerField(
        'Serviço', choices=SERVICE_CHOICES, blank=True, null=True, db_index=True)

    description = models.CharField(
        'Descrição', max_length=600, blank=True, null=True)

    # valor da chamada
    price_table = models.ForeignKey(
        PriceTable, related_name='phonecalls', verbose_name='Tabela de Valores',
        on_delete=models.SET_NULL, blank=True, null=True)

    org_price_table = models.ForeignKey(
        PriceTable, related_name='org_phonecalls',
        verbose_name='Tabela de Valores para Organização',
        on_delete=models.SET_NULL, blank=True, null=True)

    price = models.DecimalField(
        'Preço', max_digits=20, decimal_places=4, default=Decimal('0.0'))

    org_price = models.DecimalField(
        'Preço para Organização', max_digits=20, decimal_places=4, default=Decimal('0.0'))

    billedamount = models.DecimalField(
        'Valor Faturado', max_digits=20, decimal_places=4, default=Decimal('0.0'))

    org_billedamount = models.DecimalField(
        'Valor Faturado para Organização', max_digits=20, decimal_places=4, default=Decimal('0.0'))

    billedtime = models.IntegerField(
        'Tempo Faturado')

    # MdPhonecall
    md_phonecall_id = models.IntegerField(
        blank=True, null=True)

    startdate = models.DateField(
        'Data de Início')

    starttime = models.TimeField(
        'Hora de Início')

    stopdate = models.DateField(
        'Data de Encerramento')

    stoptime = models.TimeField(
        'Hora de Encerramento')

    duration = models.IntegerField(
        'Duração')

    chargednumber = models.CharField(
        'Número Cobrado', max_length=40)

    connectednumber = models.CharField(
        'Número Conectado', max_length=40)

    dialednumber = models.CharField(
        'Número Discado', max_length=40)

    conditioncode = models.SmallIntegerField(
        'Código de Condição')

    class Meta:
        ordering = ['-md_phonecall_id']
        verbose_name = 'Chamada'
        verbose_name_plural = 'Chamadas'
        indexes = [
            models.Index(fields=['-startdate'],
                         name='phonecalls_date_idx'),
        ]

    @property
    def calltype_display(self):
        if self.calltype == VC1:
            return 'VC1'
        elif self.calltype == VC2:
            return 'VC2'
        elif self.calltype == VC3:
            return 'VC3'
        elif self.calltype == LOCAL:
            return 'LOCAL'
        elif self.calltype == LDN:
            return 'LDN'
        elif self.calltype == LDI:
            return 'LDI'
        return ''

    @staticmethod
    def make_datetime(_date, _time):
        year, month, day = _date.year, _date.month, _date.day
        hour, minute, second = _time.hour, _time.minute, _time.second
        utc_datetime = timezone.datetime(year, month, day, hour, minute, second, tzinfo=pytz.UTC)
        _datetime = utc_datetime.astimezone(pytz.timezone(settings.TIME_ZONE))
        return _datetime.date(), _datetime.time()

    def set_md_data(self, md_phonecall):
        self.md_phonecall_id = md_phonecall.id
        self.startdate, self.starttime = self.make_datetime(md_phonecall.startdate, md_phonecall.starttime)
        self.stopdate, self.stoptime = self.make_datetime(md_phonecall.stopdate, md_phonecall.stoptime)
        self.duration = md_phonecall.duration
        self.chargednumber = md_phonecall.chargednumber.strip()
        self.connectednumber = md_phonecall.connectednumber.strip()
        self.dialednumber = md_phonecall.dialednumber.strip()
        self.conditioncode = md_phonecall.conditioncode

    def make_billedtime(self):
        if not self.duration:
            return 0
        billedtime = 60
        if self.duration > 60:
            time = self.duration - 60
            billedtime += ((time // 6) + (0 if time % 6 == 0 else 1)) * 6
        return billedtime


@receiver(pre_save, sender=Phonecall)
def phonecall_pre_save(sender, instance, **kwargs):
    instance.billedtime = instance.make_billedtime()

    if not instance.extension or not instance.extension.organization:
        return

    instance.organization_id = instance.extension.organization_id
    instance.org_price_table = instance.organization.settings.call_pricetable
    try:
        instance.org_price = \
            instance.org_price_table.price_set.active().get(calltype=instance.calltype).value
    except Price.DoesNotExist:
        instance.org_price = 0.0
    instance.org_billedamount = round((instance.org_price / 60) * instance.billedtime, 2)

    if not instance.extension.company:
        return

    instance.company_id = instance.extension.company_id
    if instance.extension.center_id:
        instance.center_id = instance.extension.center_id
    if instance.extension.sector_id:
        instance.sector_id = instance.extension.sector_id
    instance.price_table_id = instance.company.call_pricetable_id
    try:
        instance.price = \
            instance.price_table.price_set.active().get(calltype=instance.calltype).value
    except Price.DoesNotExist:
        instance.price = 0.0
    instance.billedamount = round((instance.price / 60) * instance.billedtime, 2)
