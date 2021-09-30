import hashlib
import hmac
import json
import requests
import logging

from celery import shared_task
from django.conf import settings
from xmodule.modulestore.django import modulestore
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment


log = logging.getLogger(__name__)


@shared_task
def sync_course_run_information_to_richie(*args, **kwargs):
    """
    Synchronize an OpenEdX course run, identified by its course key, to all Richie instances.
    """
    log.info("Entering richie update course on publish")

    course_id = kwargs["course_id"]
    course_key = CourseKey.from_string(course_id)
    course = modulestore().get_course(course_key)

    if not course:
        raise ValueError("No course found with the course_id '{}'".format(course_id))

    org = course_key.org
    edxapp_domain = configuration_helpers.get_value_for_org(
        org, 
        "LMS_BASE", 
        settings.LMS_BASE
    )

    data = {
        "resource_link": "https://{:s}/courses/{!s}/info".format(
            edxapp_domain, course_key
        ),
        "start": course.start and course.start.isoformat(),
        "end": course.end and course.end.isoformat(),
        "enrollment_start": course.enrollment_start and course.enrollment_start.isoformat(),
        "enrollment_end": course.enrollment_end and course.enrollment_end.isoformat(),
        "languages": [course.language or settings.LANGUAGE_CODE],
        "enrollment_count" : CourseEnrollment.objects.filter(course_id=course_id).count()
    }

    hooks = configuration_helpers.get_value_for_org(
        org,
        'RICHIE_OPENEDX_SYNC_COURSE_HOOKS',
        getattr(settings, "RICHIE_OPENEDX_SYNC_COURSE_HOOKS", [])
    )
    if len(hooks) == 0:
        msg = (
            "No richie course hook found for organization '{}'. Please configure the "
            "'RICHIE_OPENEDX_SYNC_COURSE_HOOKS' setting or as site configuration"
        ).format(org)
        log.info(msg)
        return msg

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
                headers={"Authorization": "SIG-HMAC-SHA256 {:s}".format(signature)},
                timeout=timeout,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            status_code = response.status_code
            log.debug(e, exc_info=True)
            msg = "Error synchronizing course {} to richie site {} it returned the HTTP status code {}".format(course_key, richie_url, status_code)
            log.error(msg)
            raise e
        except requests.exceptions.RequestException as e:
            log.debug(e, exc_info=True)
            msg = "Error synchronizing course {} to richie site {}".format(course_key, richie_url)
            log.error(msg)
            raise e

