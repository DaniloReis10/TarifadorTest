# third party
from organizations.models import Organization


def organization(request):
    user = request.user
    if not user.is_authenticated:
        return {}
    if user.is_superuser:
        return {'organizations': Organization.active.all()}
    else:
        return {'organization': user.organizations_organization.first()}
