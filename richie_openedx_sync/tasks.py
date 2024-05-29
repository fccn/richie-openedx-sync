import hashlib
import hmac
import json
import logging
from typing import Dict

import requests
from celery import shared_task
from django.conf import settings
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from common.djangoapps.student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)


@shared_task
def sync_course_run_information_to_richie(*args, **kwargs) -> Dict[str, bool]:
    """
    Synchronize an OpenEdX course run, identified by its course key, to all Richie instances.

    Raises:
        ValueError: when course if not found

    Returns:
        dict: where the key is the richie url and the value is a boolean if the synchronization
        was ok.
    """

    log.debug("Entering richie update course on publish")

    course_id = kwargs["course_id"]
    course_key = CourseKey.from_string(course_id)
    course = modulestore().get_course(course_key)

    if not course:
        raise ValueError("No course found with the course_id '{}'".format(course_id))

    org = course_key.org

    hooks = configuration_helpers.get_value_for_org(
        org,
        "RICHIE_OPENEDX_SYNC_COURSE_HOOKS",
        getattr(settings, "RICHIE_OPENEDX_SYNC_COURSE_HOOKS"),
    )
    if len(hooks) == 0:
        log.info("No richie course hook found for organization '%s'. Please configure the "
            "'RICHIE_OPENEDX_SYNC_COURSE_HOOKS' setting or as site configuration", org)
        return {}

    lms_domain = configuration_helpers.get_value_for_org(
        org, "LMS_BASE", settings.LMS_BASE
    )
    course_start = course.start and course.start.isoformat()
    course_end = course.end and course.end.isoformat()
    enrollment_start = course.enrollment_start and course.enrollment_start.isoformat()
    enrollment_end = course.enrollment_end and course.enrollment_end.isoformat()

    # Enrollment start date should fallback to course start date, by default Open edX uses the
    # course start date for the enrollment start date when the enrollment start date isn't defined.
    enrollment_start = enrollment_start or course_start

    enrollment_count = None

    result = {}

    for hook in hooks:
        # calculate enrollment count just once per hook
        if not enrollment_count:
            enrollment_count = CourseEnrollment.objects.filter(
                course_id=course_id
            ).count()

        resource_link = hook.get(
            "resource_link_template", "https://{lms_domain}/courses/{course_id}/info"
        ).format(lms_domain=lms_domain, course_id=str(course_id))

        data = {
            "resource_link": resource_link,
            "start": course_start,
            "end": course_end,
            "enrollment_start": enrollment_start,
            "enrollment_end": enrollment_end,
            "languages": [course.language or settings.LANGUAGE_CODE],
            "enrollment_count": enrollment_count,
            "catalog_visibility": course.catalog_visibility,
        }

        signature = hmac.new(
            hook["secret"].encode("utf-8"),
            msg=json.dumps(data).encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        richie_url = str(hook.get("url"))
        timeout = int(hook.get("timeout", 20))

        try:
            log.info("Sending to Richie %s the data %s", richie_url, str(data))
            response = requests.post(
                richie_url,
                json=data,
                headers={"Authorization": "SIG-HMAC-SHA256 {signature}".format(signature=signature)},
                timeout=timeout,
            )
            response.raise_for_status()
            result[richie_url] = True

            log.info("Synchronized the course %s to richie site %s it returned the HTTP status code %d response content: %s".format(
                course_id, richie_url, response.status_code, response.content
            ))
        except requests.exceptions.HTTPError as e:
            log.warning("Error synchronizing course %s to richie site %s it returned the HTTP status code %d with response content of %s",
                course_id, richie_url, response.status_code, response.content
            )
            log.warning(e, exc_info=True)
            result[richie_url] = False

        except requests.exceptions.RequestException as e:
            log.warning("Error synchronizing course %s to richie site %s", course_id, richie_url)
            log.warning(e, exc_info=True)
            result[richie_url] = False

    return result
