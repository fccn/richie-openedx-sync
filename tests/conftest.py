"""
Pytest configuration for richie_openedx_sync tests.
"""

import logging
import os
import sys
import django
from django.conf import settings
from unittest.mock import MagicMock

log = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def pytest_configure():
    """Configure Django settings before running tests."""
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
                'django.contrib.sessions',
                'django.contrib.messages',
            ],
            MIDDLEWARE=[],
            ROOT_URLCONF='',
            SECRET_KEY='test-secret-key',
            USE_TZ=True,
            LANGUAGE_CODE='en-us',
            # Add required settings for tests
            RICHIE_OPENEDX_SYNC_COURSE_HOOKS=[],
            RICHIE_OPENEDX_SYNC_LANGUAGE_MAPPING={},
            LMS_BASE='lms.example.com',
        )
        # Note: pytest-django will call django.setup() for us


# Pre-populate sys.modules with mock modules to prevent import errors
import sys

# Mock out the Open edX modules to prevent import cascades
sys.modules['common.djangoapps.student.models'] = MagicMock()
sys.modules['common.djangoapps.course_modes.models'] = MagicMock()
sys.modules['xmodule.modulestore.django'] = MagicMock()
sys.modules['openedx.core.djangoapps.site_configuration.helpers'] = MagicMock()


