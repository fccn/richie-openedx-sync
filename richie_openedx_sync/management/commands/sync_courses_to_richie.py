"""
Script for synchronize courses to Richie marketing site
"""


from django.core.management.base import BaseCommand
from six import text_type

from xmodule.modulestore.django import modulestore
from richie_openedx_sync.tasks import update_course_on_publish
from opaque_keys.edx.keys import CourseKey


class Command(BaseCommand):
    """
    Synchronize courses from mongo to the Richie marketing site
    """
    help = (
        'Synchronize courses from mongo to the Richie marketing site, all courses '
        'or a specific course'
    )

    def add_arguments(self, parser):
        parser.add_argument('--course_id', type=str, default=None, 
            help='Course id to synchronize, otherwise all courses would be sync')

    def handle(self, *args, **kwargs):
        """
        Execute the command
        """
        course_id = kwargs['course_id']
        courses, failed_courses = synchronize_courses(course_id=course_id)

        print("=" * 80)
        print("=" * 30 + "> Synchronization summary")
        print(u"Total number of courses to sync: {0}".format(len(courses)))
        print(u"Total number of courses which failed to sync: {0}".format(len(failed_courses)))
        print("List of sync failed courses ids:")
        print("\n".join(failed_courses))
        print("=" * 80)


def synchronize_courses(course_id=None):
    """
    Export all courses to target directory and return the list of courses which failed to export
    """
    if not course_id:
        module_store = modulestore()
        courses = module_store.get_courses()
        course_ids = [x.id for x in courses]
    else:
        course_key = CourseKey.from_string(course_id)
        course = modulestore().get_course(course_key)
        courses = [course]
        course_ids = [course_id]

    failed_courses = []

    for course_id in course_ids:
        print("-" * 80)
        print(u"Synchronizing to Richie course id = {0}".format(course_id))
        try:
            update_course_on_publish(course_id=str(course_id))
        except Exception as err:  # pylint: disable=broad-except
            failed_courses.append(text_type(course_id))
            print(u"=" * 30 + u"> Oops, failed to sync {0}".format(course_id))
            print("Error:")
            print(err)

    return courses, failed_courses
