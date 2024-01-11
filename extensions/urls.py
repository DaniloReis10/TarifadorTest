# django
from django.urls import path

# local
from . import views


urlpatterns = [
    path('extension/',
         views.OrgExtensionLineListView.as_view(), name='org_extension_list'),

    path('solicitation/',
         views.OrgExtensionSolicitationListView.as_view(), name='org_solicitation_list'),

    path('solicitation/create/',
         views.OrgExtensionSolicitationCreateView.as_view(), name='org_solicitation_create'),

    path('solicitation/<int:pk>/update/',
         views.OrgExtensionSolicitationUpdateView.as_view(), name='org_solicitation_update'),

    path('<slug:company_slug>/extension/',
         views.CompanyExtensionLineListView.as_view(), name='company_extension_list'),

    path('<slug:company_slug>/solicitation/',
         views.CompanyExtensionSolicitationListView.as_view(), name='company_solicitation_list'),

    path('<slug:company_slug>/solicitation/create/',
         views.CompanyExtensionSolicitationCreateView.as_view(), name='company_solicitation_create'),

    path('<slug:company_slug>/solicitation/<int:pk>/update/',
         views.CompanyExtensionSolicitationUpdateView.as_view(), name='company_solicitation_update')
]
