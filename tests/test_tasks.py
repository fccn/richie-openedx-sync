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


HOOK = {
    "url": "https://richie.example.com/api/hook",
    "secret": "test-secret",
    "timeout": 20,
}


class TestSyncCourseRunInformationToRichie:
    """Test cases for the sync_course_run_information_to_richie function."""

    @staticmethod
    def _make_course():
        """Build a stand-in for a course loaded from the modulestore."""
        course = MagicMock()
        course.start = datetime(2024, 1, 1)
        course.end = datetime(2024, 12, 31)
        course.enrollment_start = datetime(2024, 1, 1)
        course.enrollment_end = datetime(2024, 12, 1)
        course.language = "en"
        course.catalog_visibility = "both"
        return course

    @staticmethod
    def _make_response(status_code=200):
        """Build a stand-in for the response returned by Richie."""
        response = MagicMock()
        response.status_code = status_code
        response.content = "OK"
        return response

    @staticmethod
    def _config(include_payment_fields=False):
        """Build a `get_value_for_org` side effect returning a single configured hook."""

        def get_value_side_effect(org, key, default):
            if key == "RICHIE_OPENEDX_SYNC_COURSE_HOOKS":
                return [HOOK]
            elif key == "LMS_BASE":
                return "lms.example.com"
            elif key == "RICHIE_OPENEDX_SYNC_INCLUDE_PAYMENT_FIELDS":
                return include_payment_fields
            return default

        return get_value_side_effect

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

    @staticmethod
    def _course_mode(slug, min_price, currency="eur"):
        """Build a stand-in for an Open edX `CourseMode` named tuple."""
        mode = MagicMock()
        mode.slug = slug
        mode.min_price = min_price
        mode.currency = currency
        return mode

    @pytest.mark.parametrize(
        "modes,expected",
        [
            pytest.param(
                [("honor", 0)],
                {
                    "offer": "free",
                    "price": None,
                    "certificate_offer": "free",
                    "certificate_price": None,
                },
                id="honor",
            ),
            pytest.param(
                [("audit", 0), ("verified", 10)],
                {
                    "offer": "partially_free",
                    "price": None,
                    "price_currency": "EUR",
                    "certificate_offer": "paid",
                    "certificate_price": 10,
                },
                id="audit-and-verified",
            ),
            pytest.param(
                [("honor", 0), ("verified", 10)],
                {
                    "offer": "free",
                    "price": None,
                    "price_currency": "EUR",
                    "certificate_offer": "paid",
                    "certificate_price": 10,
                },
                id="honor-and-verified",
            ),
            pytest.param(
                [("verified", 10)],
                {
                    "offer": "paid",
                    "price": 10,
                    "price_currency": "EUR",
                    "certificate_offer": "free",
                    "certificate_price": None,
                },
                id="verified",
            ),
            pytest.param(
                [("audit", 0), ("verified", 25), ("professional", 10)],
                {
                    "offer": "partially_free",
                    "price": None,
                    "price_currency": "EUR",
                    "certificate_offer": "paid",
                    "certificate_price": 10,
                },
                id="cheapest-paid-mode-wins",
            ),
        ],
    )
    @patch("richie_openedx_sync.tasks.requests.post")
    @patch("richie_openedx_sync.tasks.CourseMode")
    @patch("richie_openedx_sync.tasks.CourseEnrollment")
    @patch("richie_openedx_sync.tasks.configuration_helpers.get_value_for_org")
    @patch("richie_openedx_sync.tasks.modulestore")
    def test_sync_payment_fields_from_course_modes(
        self,
        mock_modulestore,
        mock_get_value,
        mock_enrollment,
        mock_course_mode,
        mock_post,
        modes,
        expected,
    ):
        """The Open edX course modes are mapped to the Richie payment fields."""
        mock_modulestore.return_value.get_course.return_value = self._make_course()
        mock_get_value.side_effect = self._config(include_payment_fields=True)
        mock_enrollment.objects.filter.return_value.count.return_value = 42
        mock_post.return_value = self._make_response()

        mock_course_mode.modes_for_course.return_value = [
            self._course_mode(slug, min_price) for slug, min_price in modes
        ]
        # Only `audit` is not eligible for a certificate, see `CourseMode.AUDIT_MODES`.
        mock_course_mode.is_eligible_for_certificate.side_effect = (
            lambda slug, status=None: slug != "audit"
        )

        result = sync_course_run_information_to_richie(course_id="course-v1:org+course+run")

        assert result == {"https://richie.example.com/api/hook": True}
        sent_data = mock_post.call_args[1]["json"]
        for field, value in expected.items():
            assert sent_data[field] == value, field
        # The currency is omitted rather than sent as null, Richie rejects a null currency.
        if "price_currency" not in expected:
            assert "price_currency" not in sent_data
        # Enabling the payment fields must not disturb the other fields.
        assert sent_data["enrollment_count"] == 42

    @patch("richie_openedx_sync.tasks.requests.post")
    @patch("richie_openedx_sync.tasks.CourseMode")
    @patch("richie_openedx_sync.tasks.CourseEnrollment")
    @patch("richie_openedx_sync.tasks.configuration_helpers.get_value_for_org")
    @patch("richie_openedx_sync.tasks.modulestore")
    def test_sync_excludes_payment_fields_when_disabled(
        self, mock_modulestore, mock_get_value, mock_enrollment, mock_course_mode, mock_post
    ):
        """Test that payment fields are not included when the setting is disabled."""
        mock_modulestore.return_value.get_course.return_value = self._make_course()
        mock_get_value.side_effect = self._config(include_payment_fields=False)
        mock_enrollment.objects.filter.return_value.count.return_value = 42
        mock_post.return_value = self._make_response()

        result = sync_course_run_information_to_richie(course_id="course-v1:org+course+run")

        assert result == {"https://richie.example.com/api/hook": True}
        sent_data = mock_post.call_args[1]["json"]
        for field in (
            "price",
            "price_currency",
            "offer",
            "certificate_price",
            "certificate_offer",
        ):
            assert field not in sent_data
        mock_course_mode.modes_for_course.assert_not_called()

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
