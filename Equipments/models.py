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

from charges.constants import BASIC_SERVICE_CHOICES
from extensions.models import ExtensionLine
from centers.models import Company
from phonecalls.models import PriceTable

# Class to support multiple contracts
# Needs to be populatd first with the IDs that were hard coded but later can modify
# Needs to check how to interact with price tables.
# If company is null refers to master contract with organization else refers for subcontracts
# enable multiple contracts with the same organization
# It is used to print the right description for the considered contract
class ContractBasicServices(TimeStampedModel, ActivatorModel):
    organization = models.ForeignKey(
        Organization, verbose_name='Organização', on_delete=models.SET_NULL, blank=True, null=True)
    company = models.ForeignKey(  # through='CompanyExtLine'
        Company, verbose_name='Empresa', on_delete=models.SET_NULL, blank=True, null=True)
    legacyID = models.IntegerField(
        verbose_name='ID Legado do Tipo de Serviço')
    contractID = models.IntegerField(
        verbose_name='ID do contrato')
    description = models.CharField(
        verbose_name='Descrição do Serviço', max_length=255)
    org_price_table = models.ForeignKey(
        PriceTable, related_name='org_contract',
        verbose_name='Tabela de Valores para Organização',
        on_delete=models.SET_NULL, blank=True, null=True)

    def __unicode__(self):
        return u'%s' % (self.description)

class typeofphone(TimeStampedModel, ActivatorModel):
    servicetype = models.ForeignKey(
        ContractBasicServices, verbose_name='Organização', on_delete=models.SET_NULL, blank=True, null=True)
    manufacturer = models.CharField(
        verbose_name='Fabricante', max_length=255)
    phoneModel = models.CharField(
        verbose_name='Modelo', max_length=255)
    organization = models.ForeignKey(
        Organization, verbose_name='Organização', on_delete=models.SET_NULL, blank=True, null=True)

class Equipment(TimeStampedModel, ActivatorModel):
    equiptype = models.ForeignKey(
        typeofphone, verbose_name='Tipo do Equipamento', on_delete=models.CASCADE, null=True, blank=True)
    extensionNumber = models.ForeignKey(
        ExtensionLine, verbose_name='Ramal', on_delete=models.CASCADE, null=True, blank=True)
    Dateinstalled = models.DateField(
        verbose_name='Data da Instalacao')
    OSNumber =  models.CharField(
        verbose_name='Numero da '
                     'OS', max_length=255)
    TagNumber = models.CharField(
        verbose_name='Tombamento', max_length=255)
    MACAdress = models.CharField(
        verbose_name='Endereco MAC', max_length=255)
    IPAddress=models.CharField(
        verbose_name='Endereco IP', max_length=255)
    organization = models.ForeignKey(
        Organization, verbose_name='Organização', on_delete=models.SET_NULL, blank=True, null=True)
    company = models.ForeignKey(
        Company, verbose_name='Empresa', on_delete=models.CASCADE, blank=True, null=True)