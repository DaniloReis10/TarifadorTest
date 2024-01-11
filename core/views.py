# Django Imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic.base import RedirectView


class HomeRedirectView(LoginRequiredMixin, RedirectView):

    pattern_name = 'centers:list'

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_superuser:
            self.pattern_name = 'organization_list'
        else:
            org = self.request.user.organizations_organization.first()
            if org.is_admin(self.request.user):
                self.pattern_name = 'organization_detail'
            kwargs.update({'org_slug': org.slug})
        return super().get_redirect_url(*args, **kwargs)


class SuperuserRequiredMixin(LoginRequiredMixin):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(
                request, 'Você não tem a permissão necessária para executar a operação solicitada')
            return redirect(settings.LOGIN_URL)
        return super().dispatch(request, *args, **kwargs)
