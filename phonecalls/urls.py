# django
from django.urls import path

# project
from . import views


urlpatterns = [
    path('phonecalls/',
         views.OrgPhonecallListView.as_view(), name='org_phonecall_list'),

    path('phonecalls/resume/',
         views.OrgPhonecallResumeView.as_view(), name='org_phonecall_resume'),

    path('phonecalls/ust/',
         views.OrgPhonecallUSTView.as_view(), name='org_phonecall_ust'),

    path('phonecalls/report/',
         views.OrgPhonecallReportRedirectView.as_view(), name='org_phonecall_report'),

    path('phonecalls/report/csv/',
         views.OrgPhonecallCSVReportView.as_view(), name='org_phonecall_report_csv'),

    path('phonecalls/report/xlsx/',
         views.OrgPhonecallXLSXReportView.as_view(), name='org_phonecall_report_xlsx'),

    path('phonecalls/resume/report/',
         views.OrgPhonecallResumeReportRedirectView.as_view(), name='org_phonecall_resume_report'),

    path('phonecalls/resume/report/xlsx/',
         views.OrgPhonecallResumeXLSXReportView.as_view(), name='org_phonecall_resume_report_xlsx'),

    path('phonecalls/resume/report/pdf/',
         views.OrgPhonecallResumePDFReportView.as_view(), name='org_phonecall_resume_report_pdf'),

    path('phonecalls/resume/ust/report/',
         views.OrgPhonecallUSTResumeReportRedirectView.as_view(), name='org_phonecall_ust_resume_report'),

    path('phonecalls/resume/ust/report/xlsx/',
         views.OrgPhonecallUSTResumeXLSXReportView.as_view(), name='org_phonecall_ust_resume_report_xlsx'),

    path('phonecalls/resume/ust/report/pdf/',
         views.OrgPhonecallUSTResumePDFReportView.as_view(), name='org_phonecall_ust_resume_report_pdf'),

    path('<slug:company_slug>/phonecalls/',
         views.CompanyPhonecallListView.as_view(), name='list'),

    path('<slug:company_slug>/phonecalls/resume/',
         views.CompanyPhonecallResumeView.as_view(), name='resume'),

    path('<slug:company_slug>/phonecalls/report/',
         views.CompanyPhonecallReportRedirectView.as_view(), name='report'),

    path('<slug:company_slug>/phonecalls/report/csv/',
         views.CompanyPhonecallCSVReportView.as_view(), name='report_csv'),

    path('<slug:company_slug>/phonecalls/report/xlsx/',
         views.CompanyPhonecallXLSXReportView.as_view(), name='report_xlsx'),

    path('<slug:company_slug>/phonecalls/report/pdf/',
         views.CompanyPhonecallPDFReportView.as_view(), name='report_pdf'),

    path('<slug:company_slug>/phonecalls/resume/report/',
         views.CompanyPhonecallResumeReportRedirectView.as_view(), name='resume_report'),

    path('<slug:company_slug>/phonecalls/resume/report/xlsx/',
         views.CompanyPhonecallResumeXLSXReportView.as_view(), name='resume_report_xlsx'),

    path('<slug:company_slug>/phonecalls/resume/report/pdf/',
         views.CompanyPhonecallResumePDFReportView.as_view(), name='resume_report_pdf')
]
