"""
URL configuration for TestDjango project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include

# project
from charges.views import AdmCallPriceTableCreateView
from charges.views import AdmCallPriceTableDetailView
from charges.views import AdmCallPriceTableListView
from charges.views import AdmCallPriceTableUpdateView
from charges.views import AdmServicePriceTableCreateView
from charges.views import AdmServicePriceTableDetailView
from charges.views import AdmServicePriceTableListView
from charges.views import AdmServicePriceTableUpdateView
from charges.views import AdmOtherPriceTableCreateView
from charges.views import AdmOtherPriceTableDetailView
from charges.views import AdmOtherPriceTableListView
from charges.views import AdmOtherPriceTableUpdateView
from core.views import HomeRedirectView
from extensions.views import ExtensionAssignedCreateView
from extensions.views import ExtensionAssignedListView
from phonecalls.views import AdmPhonecallCSVReportView
from phonecalls.views import AdmPhonecallListView
from phonecalls.views import AdmPhonecallResumePDFReportView
from phonecalls.views import AdmPhonecallResumeView
from phonecalls.views import AdmPhonecallUSTPDFReportView
from phonecalls.views import AdmPhonecallUSTView
from phonecalls.views import TotalReportPDFMasterOrg

from Equipments.views import OSListView, EquipmentListView, EquipmentCreateView

urlpatterns = [
    path('admin/', admin.site.urls),

# third party
    path('accounts/',
         include('allauth.urls')),
    path('accounts/',
         include('accounts.urls')),

    # project
    path('<slug:org_slug>/companies/',
         include(('centers.urls', 'centers'), namespace='centers')),

    path('<slug:org_slug>/',
         include(('charges.urls', 'charges'), namespace='charges')),

    path('<slug:org_slug>/',
         include(('extensions.urls', 'extensions'), namespace='extensions')),

    path('<slug:org_slug>/',
         include(('phonecalls.urls', 'phonecalls'), namespace='phonecalls')),

    #-----------------------------------------
    # NEW URLs
    path('<slug:org_slug>/',
        include(('Equipments.urls', 'Equipments'), namespace='Equipments')),
    #-----------------------------------------------------

    # extensions
    path('extensions/',
         ExtensionAssignedListView.as_view(), name='extension_list'),

    path('extensions/create/',
         ExtensionAssignedCreateView.as_view(), name='extension_create'),

    # phonecalls
    path('phonecalls/',
         AdmPhonecallListView.as_view(), name='adm_phonecall_list'),

    path('phonecalls/report/csv/',
         AdmPhonecallCSVReportView.as_view(), name='adm_phonecall_report_csv'),

    path('phonecalls/resume/',
         AdmPhonecallResumeView.as_view(), name='adm_phonecall_resume'),

    path('phonecalls/resume/report/',
         AdmPhonecallResumePDFReportView.as_view(), name='adm_phonecall_resume_report_pdf'),

    path('phonecalls/ust/',
         AdmPhonecallUSTView.as_view(), name='adm_phonecall_ust'),

    path('phonecalls/ust/report/',
         AdmPhonecallUSTPDFReportView.as_view(), name='adm_phonecall_ust_report_pdf'),
    path('phonecalls/monthlyreport/',
         TotalReportPDFMasterOrg.as_view(), name='master_phonecall_reports'),


    # charges
    path('pricetable/call/',
         AdmCallPriceTableListView.as_view(), name='adm_call_pricetable_list'),

    path('pricetable/call/<int:pk>/detail/',
         AdmCallPriceTableDetailView.as_view(), name='adm_call_pricetable_detail'),

    path('pricetable/call/create/',
         AdmCallPriceTableCreateView.as_view(), name='adm_call_pricetable_create'),

    path('pricetable/call/<int:pk>/update/',
         AdmCallPriceTableUpdateView.as_view(), name='adm_call_pricetable_update'),

    path('pricetable/service/',
         AdmServicePriceTableListView.as_view(), name='adm_service_pricetable_list'),

    path('pricetable/service/<int:pk>/detail/',
         AdmServicePriceTableDetailView.as_view(), name='adm_service_pricetable_detail'),

    path('pricetable/service/create/',
         AdmServicePriceTableCreateView.as_view(), name='adm_service_pricetable_create'),

    path('pricetable/service/<int:pk>/update/',
         AdmServicePriceTableUpdateView.as_view(), name='adm_service_pricetable_update'),

    path('pricetable/other/',
         AdmOtherPriceTableListView.as_view(), name='adm_other_pricetable_list'),

    path('pricetable/other/<int:pk>/detail/',
         AdmOtherPriceTableDetailView.as_view(), name='adm_other_pricetable_detail'),

    path('pricetable/other/create/',
         AdmOtherPriceTableCreateView.as_view(), name='adm_other_pricetable_create'),

    path('pricetable/other/<int:pk>/update/',
         AdmOtherPriceTableUpdateView.as_view(), name='adm_other_pricetable_update'),

    # home
    path('',
         HomeRedirectView.as_view(), name='home')



]
