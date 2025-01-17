# django
from django.urls import path

# local
from . import views


urlpatterns = [
    path('os/',
         views.OSListView.as_view(), name='os_list'),
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
]