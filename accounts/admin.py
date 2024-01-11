from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Profile
from .models import OrganizationSetting


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


class OrganizationSettingsAdmin(admin.ModelAdmin):

    list_display = ['organization', 'email', 'service_pricetable', 'call_pricetable',
                    'created', 'modified']
    list_filter = ['service_pricetable', 'call_pricetable']


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(OrganizationSetting, OrganizationSettingsAdmin)
