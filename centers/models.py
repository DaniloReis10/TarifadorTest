# django
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# third party
from cities_light.models import City
from cities_light.models import Country
from cities_light.models import Region
from django_extensions.db.models import ActivatorModel
from django_extensions.db.models import TimeStampedModel

# project
from organizations.models import Organization
from phonenumber_field.modelfields import PhoneNumberField


class Company(ActivatorModel, TimeStampedModel):
    """
    Empresa
    Modelo para personalização da empresa
    Contém dados de identidade, usuários associados,
      endereço, contato, tabelas de valores por serviço
    """

    organization = models.ForeignKey(
        Organization, verbose_name='Organização', on_delete=models.CASCADE)

    users = models.ManyToManyField(
        User, through='CompanyUser')

    name = models.CharField(
        'Nome', max_length=20)

    slug = models.SlugField(
        'Slug', unique=True)

    cnpj = models.CharField(
        'CNPJ', max_length=18, blank=True, null=True)

    code = models.CharField(
        'Código da Secretaria', max_length=20, unique=True)

    logo = models.ImageField(
        upload_to='centers/', blank=True, null=True)

    description = models.TextField(
        'Descrição', blank=True, null=True)

    service_pricetable = models.ForeignKey(
        'phonecalls.PriceTable', related_name='service_company_set',
        verbose_name='Tabela de Valores - Serviços Básicos',
        on_delete=models.SET_NULL, blank=True, null=True)

    call_pricetable = models.ForeignKey(
        'phonecalls.PriceTable', related_name='call_company_set',
        verbose_name='Tabela de Valores - Serviços de Comunicação',
        on_delete=models.SET_NULL, blank=True, null=True)

    phone = PhoneNumberField(
        verbose_name='Telefone', blank=True, null=True)

    zip_code = models.CharField(
        'CEP', max_length=8, blank=True, null=True)

    city = models.ForeignKey(
        City, verbose_name='Cidade', on_delete=models.SET_NULL, blank=True, null=True)

    state = models.ForeignKey(
        Region, verbose_name='Estado', on_delete=models.SET_NULL, blank=True, null=True)

    country = models.ForeignKey(
        Country, verbose_name='País', on_delete=models.SET_NULL, blank=True, null=True)

    street = models.CharField(
        'Rua', max_length=255, blank=True)

    street_number = models.CharField(
        'Número', max_length=20, blank=True)

    neighborhood = models.CharField(
        'Bairro', max_length=255, blank=True)

    complement = models.CharField(
        'Complemento', max_length=255, blank=True, null=True)

    latitude = models.FloatField(
        'Latitude', blank=True, null=True)

    longitude = models.FloatField(
        'Longitude', blank=True, null=True)

    def is_member(self, user):
        return True if user in self.users.all() else False

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'


class CompanyUser(TimeStampedModel):
    """
    Usuário do empresa
    Modelo para associar usuários à empresas
    Contém dados de identificação da empresa e usuário
    """

    company = models.ForeignKey(
        Company, verbose_name='Empresa', on_delete=models.CASCADE)

    user = models.ForeignKey(
        User, related_name='companies', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Usuário da Empresa'
        verbose_name_plural = 'Usuários da Empresa'

    def __str__(self):
        return f'{self.user} - {self.company}'


class Center(TimeStampedModel):
    """
    Centro de Custo
    Modelo para agrupar ramais dos centros de custo de uma empresa
    Contém dados de identificação de hierarquia, organização e empresa
    """

    organization = models.ForeignKey(
        Organization, verbose_name='Organização', on_delete=models.CASCADE)

    company = models.ForeignKey(
        Company, verbose_name='Empresa', on_delete=models.CASCADE)

    name = models.CharField(
        'Nome', max_length=200)

    extension_range = models.CharField(
        'Faixas de Ramais', max_length=600, blank=True, null=True)

    class Meta:
        verbose_name = 'Centro de Custo'
        verbose_name_plural = 'Centros de Custo'

    def __str__(self):
        return self.name


class Sector(TimeStampedModel):
    """
    Setor
    Modelo para agrupar ramais dos setores de um centro de custo
    Contém dados de identificação de hierarquia, organização, empresa e centro de custo
    """

    organization = models.ForeignKey(
        Organization, verbose_name='Organização', on_delete=models.CASCADE)

    company = models.ForeignKey(
        Company, verbose_name='Empresa', on_delete=models.CASCADE)

    center = models.ForeignKey(
        Center, verbose_name='Centro de Custo', on_delete=models.CASCADE)

    name = models.CharField(
        'Nome', max_length=200)

    extension_range = models.CharField(
        'Faixas de Ramais', max_length=600, blank=True, null=True)

    class Meta:
        verbose_name = 'Setor'
        verbose_name_plural = 'Setores'

    def __str__(self):
        return f'{self.center} - {self.name}'


@receiver(post_save, sender=Company)
def company_post_save(sender, instance, created, **kwargs):
    from charges.constants import BASIC_SERVICE
    from phonecalls.models import PriceTable

    if created:
        pricetable = PriceTable.objects.create(
            organization=instance.organization,
            name=f'{instance.name} Serviços Básicos',
            servicetype=BASIC_SERVICE)
        instance.service_pricetable = pricetable
        instance.save(update_fields=['service_pricetable'])
