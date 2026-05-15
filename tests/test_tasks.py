"""
Tests for the richie_openedx_sync.tasks module.
"""

import hashlib
import hmac
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest
from requests.exceptions import HTTPError, RequestException

from richie_openedx_sync.tasks import sync_course_run_information_to_richie


class TestSyncCourseRunInformationToRichie:
    """Test cases for the sync_course_run_information_to_richie function."""

    @patch("richie_openedx_sync.tasks.requests.post")
    @patch("richie_openedx_sync.tasks.CourseEnrollment")
    @patch("richie_openedx_sync.tasks.configuration_helpers.get_value_for_org")
    @patch("richie_openedx_sync.tasks.modulestore")
    def test_sync_successful(self, mock_modulestore, mock_get_value, mock_enrollment, mock_post):
        """Test successful synchronization to Richie."""
        # Setup course mock
        mock_course = MagicMock()
        mock_course.start = datetime(2024, 1, 1)
        mock_course.end = datetime(2024, 12, 31)
        mock_course.enrollment_start = datetime(2024, 1, 1)
        mock_course.enrollment_end = datetime(2024, 12, 1)
        mock_course.language = "en"
        mock_course.catalog_visibility = "both"

        mock_modulestore_instance = MagicMock()
        mock_modulestore_instance.get_course.return_value = mock_course
        mock_modulestore.return_value = mock_modulestore_instance

        # Setup configuration
        def get_value_side_effect(org, key, default):
            if key == "RICHIE_OPENEDX_SYNC_COURSE_HOOKS":
                return [
                    {
                        "url": "https://richie.example.com/api/hook",
                        "secret": "test-secret",
                        "timeout": 20,
                    }
                ]
            elif key == "LMS_BASE":
                return "lms.example.com"
            return default

        mock_get_value.side_effect = get_value_side_effect

        # Setup enrollment mock
        mock_enrollment.objects.filter.return_value.count.return_value = 42

        # Setup response mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = "OK"
        mock_post.return_value = mock_response

        # Execute
        result = sync_course_run_information_to_richie(course_id="course-v1:org+course+run")

        # Verify
        assert result == {"https://richie.example.com/api/hook": True}
        mock_post.assert_called_once()

        # Verify the request was made with correct data
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://richie.example.com/api/hook"
        assert call_args[1]["json"]["resource_link"] == "https://lms.example.com/courses/course-v1:org+course+run/info"
        assert call_args[1]["json"]["enrollment_count"] == 42
        assert "Authorization" in call_args[1]["headers"]

    @patch("richie_openedx_sync.tasks.requests.post")
    @patch("richie_openedx_sync.tasks.CourseEnrollment")
    @patch("richie_openedx_sync.tasks.configuration_helpers.get_value_for_org")
    @patch("richie_openedx_sync.tasks.modulestore")
    def test_sync_with_http_error(self, mock_modulestore, mock_get_value, mock_enrollment, mock_post):
        """Test handling of HTTP errors during synchronization."""
        # Setup course mock
        mock_course = MagicMock()
        mock_course.start = datetime(2024, 1, 1)
        mock_course.end = None
        mock_course.enrollment_start = None
        mock_course.enrollment_end = None
        mock_course.language = "en"
        mock_course.catalog_visibility = "both"

        mock_modulestore_instance = MagicMock()
        mock_modulestore_instance.get_course.return_value = mock_course
        mock_modulestore.return_value = mock_modulestore_instance

        # Setup configuration
        def get_value_side_effect(org, key, default):
            if key == "RICHIE_OPENEDX_SYNC_COURSE_HOOKS":
                return [{"url": "https://richie.example.com/api/hook", "secret": "test-secret"}]
            elif key == "LMS_BASE":
                return "lms.example.com"
            return default

        mock_get_value.side_effect = get_value_side_effect
        mock_enrollment.objects.filter.return_value.count.return_value = 0

        # Setup response mock to raise HTTPError
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.content = "Internal Server Error"
        mock_response.raise_for_status.side_effect = HTTPError("500 Server Error")
        mock_post.return_value = mock_response

        # Execute
        result = sync_course_run_information_to_richie(course_id="course-v1:org+course+run")

        # Verify
        assert result == {"https://richie.example.com/api/hook": False}
        mock_post.assert_called_once()

    @patch("richie_openedx_sync.tasks.requests.post")
    @patch("richie_openedx_sync.tasks.CourseEnrollment")
    @patch("richie_openedx_sync.tasks.configuration_helpers.get_value_for_org")
    @patch("richie_openedx_sync.tasks.modulestore")
    def test_sync_with_request_exception(self, mock_modulestore, mock_get_value, mock_enrollment, mock_post):
        """Test handling of request exceptions during synchronization."""
        # Setup course mock
        mock_course = MagicMock()
        mock_course.start = datetime(2024, 1, 1)
        mock_course.end = None
        mock_course.enrollment_start = None
        mock_course.enrollment_end = None
        mock_course.language = None
        mock_course.catalog_visibility = "both"

        mock_modulestore_instance = MagicMock()
        mock_modulestore_instance.get_course.return_value = mock_course
        mock_modulestore.return_value = mock_modulestore_instance

        # Setup configuration
        def get_value_side_effect(org, key, default):
            if key == "RICHIE_OPENEDX_SYNC_COURSE_HOOKS":
                return [{"url": "https://richie.example.com/api/hook", "secret": "test-secret"}]
            elif key == "LMS_BASE":
                return "lms.example.com"
            return default

        mock_get_value.side_effect = get_value_side_effect
        mock_enrollment.objects.filter.return_value.count.return_value = 0

        # Setup post to raise RequestException
        mock_post.side_effect = RequestException("Connection timeout")

        # Execute
        result = sync_course_run_information_to_richie(course_id="course-v1:org+course+run")

        # Verify
        assert result == {"https://richie.example.com/api/hook": False}

    @patch("richie_openedx_sync.tasks.modulestore")
    def test_sync_course_not_found(self, mock_modulestore):
        """Test handling when course is not found."""
        mock_modulestore_instance = MagicMock()
        mock_modulestore_instance.get_course.return_value = None
        mock_modulestore.return_value = mock_modulestore_instance

        # Execute and verify exception
        with pytest.raises(ValueError, match="No course found"):
            sync_course_run_information_to_richie(course_id="course-v1:org+course+run")

    @patch("richie_openedx_sync.tasks.requests.post")
    @patch("richie_openedx_sync.tasks.CourseEnrollment")
    @patch("richie_openedx_sync.tasks.configuration_helpers.get_value_for_org")
    @patch("richie_openedx_sync.tasks.modulestore")
    def test_sync_no_hooks_configured(self, mock_modulestore, mock_get_value, mock_enrollment, mock_post):
        """Test when no hooks are configured for the organization."""
        # Setup course mock
        mock_course = MagicMock()
        mock_modulestore_instance = MagicMock()
        mock_modulestore_instance.get_course.return_value = mock_course
        mock_modulestore.return_value = mock_modulestore_instance

        # Setup configuration
        def get_value_side_effect(org, key, default):
            if key == "RICHIE_OPENEDX_SYNC_COURSE_HOOKS":
                return []
            return default

        mock_get_value.side_effect = get_value_side_effect

        # Execute
        result = sync_course_run_information_to_richie(course_id="course-v1:org+course+run")

        # Verify
        assert result == {}
        mock_post.assert_not_called()

    @patch("richie_openedx_sync.tasks.requests.post")
    @patch("richie_openedx_sync.tasks.CourseEnrollment")
    @patch("richie_openedx_sync.tasks.configuration_helpers.get_value_for_org")
    @patch("richie_openedx_sync.tasks.modulestore")
    def test_sync_with_hmac_signature(self, mock_modulestore, mock_get_value, mock_enrollment, mock_post):
        """Test that HMAC signature is correctly generated and sent."""
        # Setup course mock
        mock_course = MagicMock()
        mock_course.start = datetime(2024, 1, 1)
        mock_course.end = None
        mock_course.enrollment_start = None
        mock_course.enrollment_end = None
        mock_course.language = "en"
        mock_course.catalog_visibility = "both"

        mock_modulestore_instance = MagicMock()
        mock_modulestore_instance.get_course.return_value = mock_course
        mock_modulestore.return_value = mock_modulestore_instance

        # Setup configuration
        secret = "test-secret-key"
        def get_value_side_effect(org, key, default):
            if key == "RICHIE_OPENEDX_SYNC_COURSE_HOOKS":
                return [{"url": "https://richie.example.com/api/hook", "secret": secret}]
            elif key == "LMS_BASE":
                return "lms.example.com"
            return default

        mock_get_value.side_effect = get_value_side_effect
        mock_enrollment.objects.filter.return_value.count.return_value = 0

        # Setup response mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Execute
        result = sync_course_run_information_to_richie(course_id="course-v1:org+course+run")

        # Verify
        assert result == {"https://richie.example.com/api/hook": True}

        # Verify HMAC signature
        call_args = mock_post.call_args
        sent_data = call_args[1]["json"]
        sent_signature = call_args[1]["headers"]["Authorization"].replace("SIG-HMAC-SHA256 ", "")

        expected_signature = hmac.new(
            secret.encode("utf-8"),
            msg=json.dumps(sent_data).encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        assert sent_signature == expected_signature
