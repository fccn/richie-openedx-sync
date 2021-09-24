# -*- coding: utf-8 -*-
""" Configuration as explained on tutorial
github.com/edx/edx-platform/tree/master/openedx/core/djangoapps/plugins"""
from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class RichieOpenEdxSyncConfig(AppConfig):
    """Richie Open Edx Synchronization Django Application"""

    name = "richie_openedx_sync"
    verbose_name = "Richie Open edX Sync"
    # plugin_app = {
    #     "settings_config": {
    #         'cms.djangoapp': {
    #             'common': {'relative_path': 'settings.common'},
    #             'test': {'relative_path': 'settings.test'},
    #             "production": {"relative_path": "settings.production"},
    #         },
    #     },

    #     # Configuration setting for Plugin Signals for this app.
    #     'signals_config': {

    #         # Configure the Plugin Signals for each Project Type, as needed.
    #         'cms.djangoapp': {

    #             # List of all plugin Signal receivers for this app and project type.
    #             'receivers': [{

    #                 # The name of the app's signal receiver function.
    #                 'receiver_func_name': 'update_course_meta_data_on_studio_publish',

    #                 # The full path to the module where the signal is defined.
    #                 'signal_path': 'xmodule.modulestore.django.SignalHandler',

    #                 # The value for dispatch_uid to pass to Signal.connect to prevent duplicate signals.
    #                 # Optional; Defaults to full path to the signal's receiver function.
    #                 # 'dispatch_uid': 'richie_openedx_sync.studio.signals.update_course_on_publish',

    #             }],
    #         }
    #     },
    # }

    def ready(self):
        """
        Method to perform actions after apps registry is ended
        """
        # super.ready()
    #     #from richie_openedx_sync.permissions import load_permissions
    #     #load_permissions()

        # from .signals import update_course_meta_data_on_studio_publish

        # from xmodule.modulestore.django import SignalHandler
        # SignalHandler.course_published.connect(update_course_meta_data_on_studio_publish)

        # print("Richie sync ready 22!")

        import richie_openedx_sync.signals

        # import xmodule.modulestore.django
        # from xmodule.modulestore.django import SignalHandler
        # from .signals import update_course_meta_data_on_studio_publish
        # SignalHandler.course_published.connect(update_course_meta_data_on_studio_publish)


