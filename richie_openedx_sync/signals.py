from django.dispatch import receiver

from xmodule.modulestore.django import SignalHandler
# from student.signals import ENROLL_STATUS_CHANGE
from student.models import CourseEnrollment, EnrollStatusChange
from django.db.models.signals import post_save


@receiver(SignalHandler.course_published, dispatch_uid='richie_openedx_sync.signals.update_courses')
def update_course_meta_data_on_studio_publish(sender, course_key, **kwargs):
    from .tasks import update_course_on_publish
    # course_key is a CourseKey object and course_id its sting representation
    update_course_on_publish.delay(course_id=str(course_key))
    return (
        'Open edX synchronization of a course data to Richie has been triggered, '
        'from course_published signal.'
    )


# @receiver(ENROLL_STATUS_CHANGE)
# def sync_openedx_to_richie_from_enrollment_status_change(
#     sender, 
#     event=None, 
#     course_id=None, 
#     **kwargs):

#     if event == EnrollStatusChange.enroll:
#         return (
#             'Open edX synchronization of a course data to Richie has been skipped, '
#             'because the event status change is not about enroll'
#         )

#     from .tasks import update_course_on_publish
#     update_course_on_publish.delay(course_id=str(course_id))
#     return (
#         'Open edX synchronization of a course data to Richie has been triggered, '
#         'from enrollment status change signal.'
#     )

# ENROLL_STATUS_CHANGE.connect(sync_openedx_to_richie_from_enrollment_status_change)

@receiver(post_save, sender=CourseEnrollment)
def update_course_from_enrollment_change(sender, **kwargs): # course_id,
    from .tasks import update_course_on_publish
    course_enrollment = kwargs['instance']
    course_id = course_enrollment.course_id
    update_course_on_publish.delay(course_id=str(course_id))
    return (
        'Open edX synchronization of a course data to Richie has been triggered, '
        'from enrollment status change signal.'
    )
