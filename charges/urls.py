# django
from django.urls import path

# project
from . import views


urlpatterns = [
    path('pricetable/call/',
         views.CallPriceTableListView.as_view(), name='call_pricetable_list'),

    path('pricetable/call/<int:pk>/detail/',
         views.CallPriceTableDetailView.as_view(), name='call_pricetable_detail'),

    path('pricetable/call/create/',
         views.CallPriceTableCreateView.as_view(), name='call_pricetable_create'),

    path('pricetable/call/<int:pk>/update/',
         views.CallPriceTableUpdateView.as_view(), name='call_pricetable_update'),

    path('pricetable/basicservice/',
         views.ServicePriceTableListView.as_view(), name='service_pricetable_list'),

    path('pricetable/basicservice/<int:pk>/detail/',
         views.ServicePriceTableDetailView.as_view(), name='service_pricetable_detail'),

    path('pricetable/basicservice/create/',
         views.ServicePriceTableCreateView.as_view(), name='service_pricetable_create'),

    path('pricetable/basicservice/<int:pk>/update/',
         views.ServicePriceTableUpdateView.as_view(), name='service_pricetable_update'),

    path('pricetable/other/',
         views.OtherPriceTableListView.as_view(), name='other_pricetable_list'),

    path('pricetable/other/create/',
         views.OtherPriceTableCreateView.as_view(), name='other_pricetable_create'),

    path('pricetable/other/<int:pk>/detail/',
         views.OtherPriceTableDetailView.as_view(), name='other_pricetable_detail'),

    path('pricetable/other/<int:pk>/update/',
         views.OtherPriceTableUpdateView.as_view(), name='other_pricetable_update')
]
