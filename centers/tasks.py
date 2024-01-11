from __future__ import absolute_import, unicode_literals

# third party
#from celery import shared_task

# project
from extensions.utils import make_extension_list

# local
from .models import Center
from .models import Sector


#@shared_task
def update_center_phonecalls(center_id, created):
    instance = Center.objects.get(id=center_id)
    company = instance.company
    extension_list = make_extension_list(instance.extension_range)

    # limpar ramais e chamadas que não pertencem mais ao centro de custo
    if not created:
        center_ext_set = instance.extensionline_set.exclude(extension__in=extension_list)
        # atualizar chamadas de forma retroativa
        instance.phonecall_set.filter(extension__in=center_ext_set).update(center=None, sector=None)
        # atualizar ramais
        center_ext_set.update(center=None, sector=None)

    # associar ramais e chamadas ao centro de custo
    company_ext_set = company.extensionline_set.filter(extension__in=extension_list)
    company_ext_set.update(center=instance, sector=None)

    # atualizar chamadas de forma retroativa
    company.phonecall_set.filter(extension__in=company_ext_set).update(center=instance, sector=None)


#@shared_task
def update_sector_phonecalls(sector_id, created):
    instance = Sector.objects.get(id=sector_id)
    center = instance.center
    extension_list = make_extension_list(instance.extension_range)

    if not created:
        # limpar ramais e chamadas que não pertencem mais ao setor
        sector_ext_set = instance.extensionline_set.exclude(extension__in=extension_list)
        # atualizar chamadas de forma retroativa
        instance.phonecall_set.filter(extension__in=sector_ext_set).update(sector=None)
        # atualizar ramais
        sector_ext_set.update(sector=None)

    # associar ramais e chamadas ao setor
    center_ext_set = center.extensionline_set.filter(extension__in=extension_list)
    center_ext_set.update(sector=instance)

    # atualizar chamadas de forma retroativa
    center.phonecall_set.filter(extension__in=center_ext_set).update(sector=instance)
