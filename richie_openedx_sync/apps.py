# -*- coding: utf-8 -*-
""" Configuration as explained on tutorial
github.com/edx/edx-platform/tree/master/openedx/core/djangoapps/plugins"""
from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class RichieOpenEdxSyncConfig(AppConfig):
    """Richie Open Edx Synchronization Django Application"""

    name = "richie_openedx_sync"
    verbose_name = "Richie Open edX Sync"

    # This app can not be configured using the normal way of adding plugin application to Open edX
    # because this app uses the `SignalHandler.course_published` signal. Currently this signal is
    # not using the recommended way of configuring open edX signal so they could be used by 
    # external applications - `ENROLLMENT_TRACK_UPDATED = Signal(...)`
    # plugin_app = { ... }

    def ready(self):
        """
        Method to perform actions after apps registry is ended
        """
        # Register signals
        import richie_openedx_sync.signals

        # Load default settings configuration
        import richie_openedx_sync.settings
