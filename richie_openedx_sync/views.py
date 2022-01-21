from urllib.parse import urljoin

from django.conf import settings
from django.shortcuts import redirect
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def redirect_to_richie(request, subpath):
    """
    Redirect to Richie CMS.

    This view is used after login from Richie, with a "?next=richie/en"
    parameter.
    """
    # use configuration helpers so it would be possible to have different Richie sites one for
    # each different LMS domains.
    richie_root_url = configuration_helpers.get_value(
        "RICHIE_ROOT_URL", settings.RICHIE_ROOT_URL
    )
    return redirect(urljoin(richie_root_url, subpath))
