# Django Imports
from django.contrib import admin

# Project Imports
from phonecalls.models import Price
from phonecalls.models import PriceTable


class PriceAdmin(admin.ModelAdmin):

    list_display = [
        'id', 'table', 'calltype', 'basic_service', 'basic_service_amount', 'value',
        'activate_date', 'deactivate_date', 'status']

    list_filter = (
        'table', 'calltype', 'basic_service', 'status'
    )


class PriceTableAdmin(admin.ModelAdmin):

    list_display = [
        'name', 'organization', 'servicetype',
        'activate_date', 'deactivate_date', 'status']


admin.site.register(Price, PriceAdmin)
admin.site.register(PriceTable, PriceTableAdmin)
