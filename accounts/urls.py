# Django Imports
from django.urls import path, include

# Project Imports
from . import views


urlpatterns = [
    path("organization/",
         views.OrganizationList.as_view(), name="organization_list"),

    path("organization/add/",
         views.OrganizationCreate.as_view(), name="organization_add"),

    path("organization/<int:organization_pk>/", include([
        path("",
             views.OrganizationDetail.as_view(), name="organization_detail"),

        path("update/",
             views.OrganizationUpdate.as_view(), name="organization_edit"),

        path("users/", include([
            # path("",
            #      views.OrganizationUserList.as_view(), name="organization_user_list"),

            path("add/",
                 views.OrganizationUserCreate.as_view(), name="organization_user_add"),

            # path("<int:user_pk>/remind/",
            #      views.OrganizationUserRemind.as_view(), name="organization_user_remind"),

            path("<int:user_pk>/",
                 views.OrganizationUserDetail.as_view(), name="organization_user_detail"),

            path("<int:user_pk>/update/",
                 views.OrganizationUserUpdate.as_view(), name="organization_user_edit"),

            path("<int:user_pk>/delete/",
                 views.OrganizationUserDelete.as_view(), name="organization_user_delete"),

            path("profile/<int:pk>/update/",
                 views.OrganizationProfileUpdateView.as_view(), name="org_profile_update")
        ]))
    ])),

    path("profile/update/",
         views.ProfileUpdateView.as_view(), name="profile_update")
]
