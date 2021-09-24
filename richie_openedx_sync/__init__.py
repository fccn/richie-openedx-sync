"""
Init for main richie openedx synchronization application
"""
from __future__ import unicode_literals

# Django signal receiver modules must imported early so that the signal
# handling gets registered before any signals need to be sent.
#from .signals import update_course_meta_data_on_studio_publish

__version__ = "0.1.0"

default_app_config = 'richie_openedx_sync.apps.RichieOpenEdxSyncConfig'
