# django
from django.urls import path

# local
from . import views


urlpatterns = [
    path('<slug:company_slug>/os/',
         views.CompanyOSListView.as_view(), name='company_os_list'),
    path('<slug:company_slug>/os/create',
         views.CompanyOSCreateView.as_view(), name='company_os_create'),
    path('<slug:company_slug>/<int:pk>/os/edit',
         views.CompanyOSUpdateView.as_view(), name='company_os_edit'),
    path('equipments/',
         views.OrgEquipmentListView.as_view(), name='org_equipment_list'),
    path('equipments/create',
         views.OrgEquipmentCreateView.as_view(), name='org_equipment_create'),
    path('<int:pk>/equipments/edit',
         views.OrgEquipmentUpdateView.as_view(), name='org_equipment_edit'),
    path('contracts/',
         views.OrgContractListView.as_view(), name='org_contract_list'),
    path('contracts/create',
         views.OrgContractCreateView.as_view(), name='org_contract_create'),
    path('<int:pk>/contracts/edit',
         views.OrgContractUpdateView.as_view(), name='org_contract_edit'),
    path('contracts/filter',
         views.OrgContractFilterListView.as_view(), name='org_contract_filter_list'),
    path('equipments/filter',
         views.OrgEquipmentFilterListView.as_view(), name='org_equipment_filter_list'),
]