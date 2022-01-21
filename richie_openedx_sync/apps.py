# -*- coding: utf-8 -*-
"""
Richie Open Edx Synchronization Django Application.
Configuration as explained on tutorial:
https://github.com/openedx/edx-django-utils/blob/master/edx_django_utils/plugins/README.rst
"""
from __future__ import absolute_import, unicode_literals
from openedx.core.djangoapps.plugins.constants import (
    PluginSettings, 
    PluginURLs, 
    ProjectType, 
    SettingsType
)
from django.apps import AppConfig


class RichieOpenEdxSyncConfig(AppConfig):
    """Richie Open Edx Synchronization Django Application"""

    name = "richie_openedx_sync"
    verbose_name = "Richie Open edX Sync"

    # Open edX plugin docs:
    # https://github.com/openedx/edx-django-utils/blob/master/edx_django_utils/plugins/README.rst
    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: "richie",
                PluginURLs.REGEX: r"^richie/",
                PluginURLs.RELATIVE_PATH: "urls",
            }
            ProjectType.CMS: {
                PluginURLs.NAMESPACE: "richie",
                PluginURLs.REGEX: r"^richie/",
                PluginURLs.RELATIVE_PATH: "urls",
            }
        },
    }

    # This app can not be configured using the normal way of adding plugin application to Open edX
    # because this app uses the `SignalHandler.course_published` signal. Currently this signal is
    # not using the recommended way of configuring open edX signal so they could be used by 
    # external applications - `ENROLLMENT_TRACK_UPDATED = Signal(...)`
    # plugin_app = { ... }

    def ready(self):
        """
        Method to perform actions after apps registry is ended
        """
        # Load default settings configuration
        # pylint: disable=unused-import
        from . import settings

        # Register signals
        # pylint: disable=unused-import
        from . import signals

        # pylint: disable=unused-import
        from . import management.commands
