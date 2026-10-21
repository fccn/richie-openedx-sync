"""
Signals reveivers of Richie Open edX synchronization
"""
import logging

from django.conf import settings
from django.core.cache import cache
from django.dispatch import receiver

from xmodule.modulestore.django import SignalHandler
from common.djangoapps.student.signals import ENROLL_STATUS_CHANGE
from common.djangoapps.student.models import EnrollStatusChange

log = logging.getLogger(__name__)

# The sync task reads the course data when it runs, so a single pending task already covers every
# enrollment made before it starts.
ENROLLMENT_SYNC_PENDING_KEY = "richie_openedx_sync.enrollment_sync_pending.{course_id}"
# The pending marker expires before the task starts, so an enrollment that is still being saved
# when the marker expires schedules its own sync instead of being missed.
ENROLLMENT_SYNC_COUNTDOWN_MARGIN = 5


def _get_enrollment_debounce_seconds():
    """
    Read `RICHIE_OPENEDX_SYNC_ENROLLMENT_DEBOUNCE_SECONDS`, anything that is not a positive number
    disables the debounce.
    """
    value = getattr(settings, "RICHIE_OPENEDX_SYNC_ENROLLMENT_DEBOUNCE_SECONDS", 0)
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        log.warning(
            "Invalid RICHIE_OPENEDX_SYNC_ENROLLMENT_DEBOUNCE_SECONDS %r, the debounce is disabled", value
        )
        return 0


def _schedule_enrollment_sync(course_id):
    """
    Queue the synchronization of a course after an enrollment.

    Without a debounce window every enrollment queues its own task. With a window, the first
    enrollment of a course schedules one task that starts after the window and the next ones
    are skipped until the marker expires.

    Returns:
        bool: `False` when a pending synchronization of the course already covers this enrollment.
    """
    from .tasks import sync_course_run_information_to_richie

    window = _get_enrollment_debounce_seconds()
    if not window:
        sync_course_run_information_to_richie.delay(course_id=course_id)
        return True

    try:
        is_first = cache.add(ENROLLMENT_SYNC_PENDING_KEY.format(course_id=course_id), 1, timeout=window)
    except Exception:  # pylint: disable=broad-except
        # An unavailable cache must never lose a synchronization.
        log.exception("Could not debounce the synchronization of the course %s", course_id)
        is_first = True

    if is_first:
        sync_course_run_information_to_richie.apply_async(
            kwargs={"course_id": course_id},
            countdown=window + ENROLLMENT_SYNC_COUNTDOWN_MARGIN,
        )
    return is_first


@receiver(
    SignalHandler.course_published, 
    dispatch_uid='richie_openedx_sync.signals.sync_openedx_to_richie_after_course_published')
def sync_openedx_to_richie_after_course_published(sender, course_key, **kwargs):
    """
    On updating course schedule and details on studio, update course run information on richie
    """
    from .tasks import sync_course_run_information_to_richie
    # course_key is a CourseKey object and course_id its sting representation
    sync_course_run_information_to_richie.delay(course_id=str(course_key))
    return (
        'Open edX synchronization of a course data to Richie has been triggered, '
        'from course_published signal.'
    )

@receiver(
    ENROLL_STATUS_CHANGE, 
    dispatch_uid='richie_openedx_sync.signals.sync_openedx_to_richie_after_enrollment_status_change')
def sync_openedx_to_richie_after_enrollment_status_change(
    sender,
    event=None,
    course_id=None,
    **kwargs):
    """
    On updating course enrollment changes and the change is of `enroll` type, then update course
    run information on richie
    """

    if event != EnrollStatusChange.enroll:
        return (
            'Open edX synchronization of a course data to Richie has been skipped, '
            'because the event status change is not about enroll'
        )

    if not _schedule_enrollment_sync(str(course_id)):
        return (
            'Open edX synchronization of a course data to Richie has been skipped, '
            'because a synchronization of this course is already pending'
        )
    return (
        'Open edX synchronization of a course data to Richie has been triggered, '
        'from enrollment status change signal.'
    )
