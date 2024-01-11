# django
from django.db import models
from django.db.models.signals import post_save

# third party
from django_extensions.db.models import TimeStampedModel
from organizations.models import Organization

# project
from centers.models import Center
from centers.models import Company
from centers.models import Sector

# local
from .constants import SOLICITATION_APPROVED
from .constants import SOLICITATION_OPENED
from .constants import SOLICITATION_STATUS_CHOICES
from .utils import make_extension_list


class ExtensionLine(TimeStampedModel):
    """
    Ramal
    Modelo para associar ramais à centros de custo e organizações
    Contém dados de identificação do ramal, organização, empresa, centro de custo e setor
    """

    organization = models.ForeignKey(
        Organization, verbose_name='Organização', on_delete=models.SET_NULL, blank=True, null=True)

    company = models.ForeignKey(  # through='CompanyExtLine'
        Company, verbose_name='Empresa', on_delete=models.SET_NULL, blank=True, null=True)

    center = models.ForeignKey(
        Center, verbose_name='Centro de Custo', on_delete=models.SET_NULL, blank=True, null=True)

    sector = models.ForeignKey(
        Sector, verbose_name='Setor', on_delete=models.SET_NULL, blank=True, null=True)

    extension = models.CharField(
        'Ramal', max_length=50, unique=True)

    def __str__(self):
        return self.extension

    class Meta:
        verbose_name = 'Ramal'
        verbose_name_plural = 'Ramais'


# TODO histórico de ramais
# class CompanyExtLine(ActivatorModel):

#     company = models.ForeignKey(
#         Company, verbose_name='Empresa', on_delete=models.CASCADE)

#     extension = models.ForeignKey(
#         ExtensionLine, verbose_name='Ramal', on_delete=models.CASCADE)


class ExtensionAssigned(TimeStampedModel):
    """
    Ramais associados ao sistema
    Modelo para registro de ramais disponíveis
    Contém dados de ranges de ramais
    """

    extension_range = models.CharField('Faixa de Ramais', max_length=100)

    class Meta:
        verbose_name = 'Faixa de ramal atribuido ao sistema'
        verbose_name_plural = 'Faixa de ramais atribuidos ao sistema'

    def __str__(self):
        return self.extension_range

    @staticmethod
    def post_save(sender, instance, created, *args, **kwargs):
        if created:
            extension_list = make_extension_list(instance.extension_range)
            ExtensionLine.objects.bulk_create([
                ExtensionLine(extension=extension) for extension in extension_list])


class ExtensionSolicitation(TimeStampedModel):
    """
    Solicitação de Ramais
    Modelo para registro de solicitações de ramais
    Contém dados do range de ramais, centro de custo, organização e status da solicitação
    """

    organization = models.ForeignKey(
        Organization, verbose_name='Organização', on_delete=models.CASCADE, blank=True, null=True)

    company = models.ForeignKey(
        Company, verbose_name='Empresa', on_delete=models.CASCADE, blank=True, null=True)

    extension_range = models.CharField(
        'Faixa de Ramais', max_length=600)

    status = models.IntegerField(
        'Status da Solicitação', choices=SOLICITATION_STATUS_CHOICES, default=SOLICITATION_OPENED)

    class Meta:
        verbose_name = 'Solicitação de Ramais'
        verbose_name_plural = 'Solicitações de Ramais'

    def __str__(self):
        return f'{self.organization} - {self.extension_range}'

    @staticmethod
    def post_save(sender, instance, created, *args, **kwargs):
        if instance.status == SOLICITATION_APPROVED:
            extension_list = make_extension_list(instance.extension_range)
            ExtensionLine.objects \
                .filter(extension__in=extension_list) \
                .update(organization=instance.organization, company=instance.company)


post_save.connect(ExtensionAssigned.post_save, sender=ExtensionAssigned)
post_save.connect(ExtensionSolicitation.post_save, sender=ExtensionSolicitation)
