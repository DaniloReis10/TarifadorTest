# django
from django.contrib import admin

# local
from .models import Phonecall


class PhonecallAdmin(admin.ModelAdmin):

    list_display = [
        'md_phonecall_id', 'organization', 'company', 'center', 'sector', 'extension',
        'chargednumber', 'dialednumber', 'calltype', 'pabx', 'inbound', 'internal',
        'description', 'price_table', 'price', 'billedamount', 'duration']
    
    list_filter = ['organization', 'company','startdate','stopdate']

    search_fields = ['chargednumber']

admin.site.register(Phonecall, PhonecallAdmin)
