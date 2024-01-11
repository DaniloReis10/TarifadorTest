# -*- coding: utf-8 -*-
# django
from django.contrib import admin

# local
from .models import ExtensionAssigned
from .models import ExtensionLine
from .models import ExtensionSolicitation


@admin.register(ExtensionLine)
class ExtensionLineAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'organization',
        'extension',
    )
    list_filter = ('created', 'modified', 'organization', 'company')


@admin.register(ExtensionAssigned)
class ExtensionAssignedAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'modified', 'extension_range')
    list_filter = ('created', 'modified')


@admin.register(ExtensionSolicitation)
class ExtensionSolicitationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'organization',
        'company',
        'extension_range',
        'status',
    )
    list_filter = ('created', 'modified', 'organization', 'company')
