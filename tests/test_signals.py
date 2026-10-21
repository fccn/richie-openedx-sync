"""
Tests for the richie_openedx_sync.signals module.
"""

from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.test import override_settings

from common.djangoapps.student.models import EnrollStatusChange
from richie_openedx_sync.signals import (
    ENROLLMENT_SYNC_COUNTDOWN_MARGIN,
    ENROLLMENT_SYNC_PENDING_KEY,
    sync_openedx_to_richie_after_course_published,
    sync_openedx_to_richie_after_enrollment_status_change,
)

COURSE_ID = "course-v1:ORG+CODE+RUN"
OTHER_COURSE_ID = "course-v1:ORG+OTHER+RUN"
TASK = "richie_openedx_sync.tasks.sync_course_run_information_to_richie"


def enroll(course_id=COURSE_ID, event=None):
    """Send the enrollment status change the way Open edX does."""
    return sync_openedx_to_richie_after_enrollment_status_change(
        sender=None,
        event=EnrollStatusChange.enroll if event is None else event,
        course_id=course_id,
    )


@pytest.fixture(autouse=True)
def clean_cache():
    """The debounce markers live in the cache, start every test without any."""
    cache.clear()
    yield
    cache.clear()


class TestEnrollmentSyncWithoutDebounce:
    """The debounce is off by default, every enrollment queues its own task as before."""

    @patch(TASK)
    def test_every_enrollment_queues_a_task(self, mock_task):
        for _ in range(3):
            enroll()

        assert mock_task.delay.call_count == 3
        mock_task.delay.assert_called_with(course_id=COURSE_ID)
        mock_task.apply_async.assert_not_called()

    @patch(TASK)
    @pytest.mark.parametrize("value", [0, "0", None, "", "abc", -5])
    def test_invalid_or_non_positive_window_disables_the_debounce(self, mock_task, value):
        with override_settings(RICHIE_OPENEDX_SYNC_ENROLLMENT_DEBOUNCE_SECONDS=value):
            enroll()
            enroll()

        assert mock_task.delay.call_count == 2
        mock_task.apply_async.assert_not_called()

    @patch(TASK)
    def test_other_status_changes_are_ignored(self, mock_task):
        result = enroll(event=EnrollStatusChange.unenroll)

        assert "skipped" in result
        mock_task.delay.assert_not_called()
        mock_task.apply_async.assert_not_called()


class TestEnrollmentSyncWithDebounce:
    """With a window the first enrollment of a course schedules one task, the next ones are skipped."""

    @pytest.fixture(autouse=True)
    def debounce_window(self):
        with override_settings(RICHIE_OPENEDX_SYNC_ENROLLMENT_DEBOUNCE_SECONDS=60):
            yield

    @patch(TASK)
    def test_a_burst_of_enrollments_queues_a_single_delayed_task(self, mock_task):
        results = [enroll() for _ in range(50)]

        mock_task.apply_async.assert_called_once_with(
            kwargs={"course_id": COURSE_ID}, countdown=60 + ENROLLMENT_SYNC_COUNTDOWN_MARGIN
        )
        mock_task.delay.assert_not_called()
        assert "triggered" in results[0]
        assert all("already pending" in result for result in results[1:])

    @patch(TASK)
    def test_the_task_starts_after_the_marker_expires(self, mock_task):
        """An enrollment saved while the marker expires must not be missed by the task."""
        with patch("richie_openedx_sync.signals.cache") as mock_cache:
            mock_cache.add.return_value = True
            enroll()

        mock_cache.add.assert_called_once_with(
            ENROLLMENT_SYNC_PENDING_KEY.format(course_id=COURSE_ID), 1, timeout=60
        )
        countdown = mock_task.apply_async.call_args.kwargs["countdown"]
        assert countdown > 60

    @patch(TASK)
    def test_each_course_has_its_own_window(self, mock_task):
        enroll(COURSE_ID)
        enroll(OTHER_COURSE_ID)
        enroll(COURSE_ID)
        enroll(OTHER_COURSE_ID)

        assert mock_task.apply_async.call_count == 2
        queued = {call.kwargs["kwargs"]["course_id"] for call in mock_task.apply_async.call_args_list}
        assert queued == {COURSE_ID, OTHER_COURSE_ID}

    @patch(TASK)
    def test_a_new_task_is_queued_once_the_marker_expired(self, mock_task):
        enroll()
        cache.delete(ENROLLMENT_SYNC_PENDING_KEY.format(course_id=COURSE_ID))
        enroll()

        assert mock_task.apply_async.call_count == 2

    @patch(TASK)
    def test_an_unavailable_cache_never_loses_the_synchronization(self, mock_task):
        with patch("richie_openedx_sync.signals.cache") as mock_cache:
            mock_cache.add.side_effect = ConnectionError("cache is down")
            result = enroll()

        assert "triggered" in result
        mock_task.apply_async.assert_called_once()

    @patch(TASK)
    def test_other_status_changes_are_still_ignored(self, mock_task):
        enroll(event=EnrollStatusChange.unenroll)

        mock_task.apply_async.assert_not_called()
        mock_task.delay.assert_not_called()

    @patch(TASK)
    def test_course_published_is_never_debounced(self, mock_task):
        for _ in range(3):
            sync_openedx_to_richie_after_course_published(sender=None, course_key=COURSE_ID)

        assert mock_task.delay.call_count == 3
        mock_task.delay.assert_called_with(course_id=COURSE_ID)
        mock_task.apply_async.assert_not_called()
