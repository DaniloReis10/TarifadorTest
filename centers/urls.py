# django
from django.urls import path

# project
from . import views


urlpatterns = [
    # company
    path('',
         views.CompanyListView.as_view(), name='list'),

    path('create/',
         views.CompanyCreateView.as_view(), name='create'),

    path('<slug:slug>/update/',
         views.CompanyUpdateView.as_view(), name='update'),

    # centers
    path('<slug:company_slug>/centers/',
         views.CenterListView.as_view(), name='center_list'),

    path('<slug:company_slug>/sectors/<int:center_pk>/detail/',
         views.CenterDetailView.as_view(), name='center_detail'),

    path('<slug:company_slug>/centers/create/',
         views.CenterCreateView.as_view(), name='center_create'),

    path('<slug:company_slug>/centers/<int:center_pk>/update/',
         views.CenterUpdateView.as_view(), name='center_update'),

    path('<slug:company_slug>/centers/<int:center_pk>/delete/',
         views.CenterDeleteView.as_view(), name='center_delete'),

    # sectors
    path('<slug:company_slug>/sectors/',
         views.SectorListView.as_view(), name='sector_list'),

    path('<slug:company_slug>/sectors/create/',
         views.SectorCreateView.as_view(), name='sector_create'),

    path('<slug:company_slug>/sectors/<int:sector_pk>/update/',
         views.SectorUpdateView.as_view(), name='sector_update'),

    path('<slug:company_slug>/sectors/<int:sector_pk>/delete/',
         views.SectorDeleteView.as_view(), name='sector_delete')
]
