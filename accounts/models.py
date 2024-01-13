# Django Imports
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# Third Party Imports
from cities_light.models import City
from cities_light.models import Country
from cities_light.models import Region
from django_extensions.db.models import TimeStampedModel
from organizations.models import Organization
from phonenumber_field.modelfields import PhoneNumberField


class Profile(TimeStampedModel):
    """
    Perfil do Usuário
    Modelo para personalização do usuário
    Contém dados de identidade e contato
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE)

    phone = PhoneNumberField(
        verbose_name='Telefone', blank=True, null=True)

    avatar = models.ImageField(
        upload_to='profile/', blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name() if self.user.get_full_name() else self.user.username


class OrganizationSetting(TimeStampedModel):
    """
    Perfil da Organização
    Modelo para personalização da organização
    Contém dados de identidade, endereço, contato,
      tabelas de valores por serviços
    """

    organization = models.OneToOneField(
        Organization, verbose_name='Organização', related_name='settings', on_delete=models.CASCADE)

    logo = models.ImageField(
        upload_to='organizations/', blank=True, null=True)

    email = models.EmailField(
        'E-mail', blank=True)

    service_pricetable = models.ForeignKey(
        'phonecalls.PriceTable', related_name='service_orgsettings_set',
        verbose_name='Tabela de Valores Serviços Básicos',
        on_delete=models.SET_NULL, blank=True, null=True)

    call_pricetable = models.ForeignKey(
        'phonecalls.PriceTable', related_name='call_orgsettings_set',
        verbose_name='Tabela de Valores Serviços de Comunicação',
        on_delete=models.SET_NULL, blank=True, null=True)

    other_pricetable = models.ForeignKey(
        'phonecalls.PriceTable', related_name='other_orgsettings_set',
        verbose_name='Tabela de Valores Serviços Diversos',
        on_delete=models.SET_NULL, blank=True, null=True)

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

    def __str__(self):
        email = f' - {self.email}' if self.email else ''
        return f'{self.organization}{email}'

    class Meta:
        verbose_name = 'Configuração da Organização'
        verbose_name_plural = 'Configurações da Organização'


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()


@receiver(post_save, sender=Organization)
def create_organization(sender, instance, created, **kwargs):
    from charges.constants import BASIC_SERVICE
    from phonecalls.models import PriceTable

    if created:
        pricetable = PriceTable.objects.create(
            name=f'{instance.name} Serviços Básicos',
            servicetype=BASIC_SERVICE)
        OrganizationSetting.objects.create(organization=instance, service_pricetable=pricetable)
