"""
Signals reveivers of Richie Open edX synchronization
"""
from django.dispatch import receiver

from xmodule.modulestore.django import SignalHandler
from student.signals import ENROLL_STATUS_CHANGE
from student.models import EnrollStatusChange


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

    from .tasks import sync_course_run_information_to_richie
    sync_course_run_information_to_richie.delay(course_id=str(course_id))
    return (
        'Open edX synchronization of a course data to Richie has been triggered, '
        'from enrollment status change signal.'
    )
