from django.dispatch import receiver

from xmodule.modulestore.django import SignalHandler


@receiver(SignalHandler.course_published, dispatch_uid='richie_openedx_sync.signals.update_courses')
def update_course_meta_data_on_studio_publish(sender, course_key, **kwargs):
    from .tasks import update_course_on_publish
    # course_key is a CourseKey object and course_id its sting representation
    #update_course_on_publish.delay(course_id=str(course_key))
    update_course_on_publish(course_id=str(course_key))
    return 'Open edX synchronization of courses meta data to Richie has been triggered.'
