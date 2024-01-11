# django
from django.contrib import admin

# local
from .models import Center
from .models import Company
from .models import CompanyUser
from .models import Sector


class CompanyAdmin(admin.ModelAdmin):

    list_display = [
        'name', 'code', 'organization', 'service_pricetable', 'call_pricetable',
        'created', 'modified', 'status', 'activate_date', 'deactivate_date']
    list_filter = ['code', 'status', 'service_pricetable', 'call_pricetable']
    prepopulated_fields = {
        'slug': ['name']
    }
    search_fields = ['name']


class CompanyUserAdmin(admin.ModelAdmin):

    search_fields = ['user__username']
    list_display = ['user', 'company']
    list_filter = ['company']


class CenterAdmin(admin.ModelAdmin):

    list_display = [
        'name', 'extension_range', 'company', 'organization', 'created', 'modified']
    list_filter = ['company']
    search_fields = ['name']


class SectorAdmin(admin.ModelAdmin):

    list_display = [
        'name', 'extension_range', 'center', 'company', 'organization', 'created', 'modified']
    list_filter = ['center', 'company']
    search_fields = ['name']


admin.site.register(Company, CompanyAdmin)
admin.site.register(CompanyUser, CompanyUserAdmin)
admin.site.register(Center, CenterAdmin)
admin.site.register(Sector, SectorAdmin)
