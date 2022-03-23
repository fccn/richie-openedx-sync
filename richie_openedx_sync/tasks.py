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
from student.models import CourseEnrollment
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
        raise ValueError(
            "No course found with the course_id '{}'".format(course_id))

    org = course_key.org
    edxapp_domain = configuration_helpers.get_value_for_org(
        org, "LMS_BASE", settings.LMS_BASE
    )
    course_start = course.start and course.start.isoformat()
    course_end = course.end and course.end.isoformat()
    enrollment_start = course.enrollment_start and course.enrollment_start.isoformat()
    enrollment_end = course.enrollment_end and course.enrollment_end.isoformat()

    # Enrollment start date should fallback to course start date, by default Open edX uses the
    # course start date for the enrollment start date when the enrollment start date isn't defined.
    enrollment_start = enrollment_start or course_start

    data = {
        "resource_link": "https://{:s}/courses/{!s}/info".format(
            edxapp_domain, course_key
        ),
        "start": course_start,
        "end": course_end,
        "enrollment_start": enrollment_start,
        "enrollment_end": enrollment_end,
        "languages": [course.language or settings.LANGUAGE_CODE],
        "enrollment_count": CourseEnrollment.objects.filter(
            course_id=course_id
        ).count(),
        "catalog_visibility": course.catalog_visibility,
    }

    hooks = configuration_helpers.get_value_for_org(
        org,
        "RICHIE_OPENEDX_SYNC_COURSE_HOOKS",
        getattr(settings, "RICHIE_OPENEDX_SYNC_COURSE_HOOKS", []),
    )
    if not hooks:
        msg = (
            "No richie course hook found for organization '{}'. Please configure the "
            "'RICHIE_OPENEDX_SYNC_COURSE_HOOKS' setting or as site configuration"
        ).format(org)
        log.info(msg)
        return {}

    result = {}

    for hook in hooks:
        signature = hmac.new(
            hook["secret"].encode("utf-8"),
            msg=json.dumps(data).encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        richie_url = hook.get("url")
        timeout = int(hook.get("timeout", 5))

        try:
            response = requests.post(
                richie_url,
                json=data,
                headers={
                    "Authorization": "SIG-HMAC-SHA256 {:s}".format(signature)},
                timeout=timeout,
            )
            response.raise_for_status()
            result[richie_url] = True
        except requests.exceptions.HTTPError as e:
            status_code = response.status_code
            msg = "Error synchronizing course {} to richie site {} it returned the HTTP status code {}".format(
                course_key, richie_url, status_code
            )
            log.error(e, exc_info=True)
            log.error(msg)
            log.error(response.content)
            result[richie_url] = False

        except requests.exceptions.RequestException as e:
            msg = "Error synchronizing course {} to richie site {}".format(
                course_key, richie_url
            )
            log.error(e, exc_info=True)
            log.error(msg)
            result[richie_url] = False

    return result
