"""
Script to synchronize courses to Richie marketing site
"""

import logging

from typing import Dict
from django.core.management.base import BaseCommand
from six import text_type

from xmodule.modulestore.django import modulestore
from richie_openedx_sync.tasks import sync_course_run_information_to_richie
from opaque_keys.edx.keys import CourseKey
from django.conf import settings

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command that synchronizes the Open edX courses to the Richie marketing site
    """

    help = (
        "Synchronize courses to the Richie marketing site, by default all courses "
        "or a specific course"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--course_id",
            type=str,
            default=None,
            help="Course id to synchronize, otherwise all courses would be sync",
        )

    def handle(self, *args, **kwargs):
        """
        Synchronize courses to the Richie marketing site, print to console its sync progress.
        """
        course_id = kwargs["course_id"]

        if not course_id:
            log.info(settings.CONTENTSTORE) 
            log.info(settings.CONTENTSTORE['ENGINE'])
            module_store = modulestore()             
            courses = module_store.get_courses() 
            log.info("courses", courses)
            course_ids = [x.id for x in courses]
        else:
            course_key = CourseKey.from_string(course_id)
            course = modulestore().get_course(course_key)
            courses = [course]
            course_ids = [course_id]

        course_ids_count = len(course_ids)
        total_sync_ok_count = 0
        total_sync_not_ok_count = 0

        for course_id in course_ids:
            log.info("-" * 80)
            log.info("Synchronizing to Richie course id = {0}".format(course_id))
            sync_result = sync_course_run_information_to_richie(
                course_id=str(course_id)
            )
            ok_count = len(list(filter(lambda e: e[1], sync_result.items())))
            not_ok_count = len(list(filter(lambda e: not e[1], sync_result.items())))
            if ok_count > 0:
                log.info("  ok count: {0}".format(ok_count))
            if not_ok_count > 0:
                log.info("  not ok count: {0}".format(not_ok_count))

            richie_failed_backends = str(
                list(
                    map(
                        lambda e: e[0],
                        (filter(lambda e: not e[1], sync_result.items())),
                    )
                )
            )
            log.info("  failed backends: {0}".format(richie_failed_backends))

            total_sync_ok_count += ok_count
            total_sync_not_ok_count += not_ok_count

        log.info("=" * 80)
        log.info("Synchronization summary")
        print("Total number of courses synchronized: {0}".format(course_ids_count))
        log.info("Total number of synchronizations ok: {0}".format(total_sync_ok_count))
        log.info(
            "Total number of synchronizations not ok (error): {0}".format(total_sync_not_ok_count)
        )
