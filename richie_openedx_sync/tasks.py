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
from richie_openedx_sync.utils import transform_language
from xmodule.modulestore.django import modulestore
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.course_modes.models import CourseMode

log = logging.getLogger(__name__)

RICHIE_OFFER_FREE = "free"
RICHIE_OFFER_PARTIALLY_FREE = "partially_free"
RICHIE_OFFER_PAID = "paid"


def _parse_boolean_setting(value):
    """
    Coerce a setting to a boolean, site configuration values can arrive as strings.
    """
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def _get_course_payment_fields(course_key):
    """
    Build the Richie payment fields out of the Open edX course modes of a course.

    | Open edX course modes | offer          | price | certificate_offer | certificate_price |
    | --------------------- | -------------- | ----- | ----------------- | ----------------- |
    | honor                 | free           | -     | free              | -                 |
    | audit + verified      | partially_free | -     | paid              | verified price    |
    | honor + verified      | free           | -     | paid              | verified price    |
    | verified              | paid           | price | free              | -                 |

    `audit` and `honor` are both free of charge, but only `honor` is eligible for a
    certificate. So a course that can be completed on `honor` is entirely `free`, while the
    same course on `audit` is only `partially_free`.

    When there is a free way in, whatever is paid buys the certificate. When there isn't, the
    price buys the course itself and the certificate comes along with it at no extra cost.

    Returns:
        dict: the Richie course run payment fields. `price_currency` is only present when
        there is a price to go with it, because Richie doesn't accept a null currency.
    """
    modes = CourseMode.modes_for_course(course_id=course_key)
    paid_modes = [mode for mode in modes if mode.min_price > 0]
    free_modes = [mode for mode in modes if mode.min_price <= 0]

    # The cheapest paid mode is the one advertised on Richie.
    cheapest_paid_mode = min(paid_modes, key=lambda mode: mode.min_price, default=None)

    if cheapest_paid_mode is None:
        return {
            "offer": RICHIE_OFFER_FREE,
            "price": None,
            "certificate_offer": RICHIE_OFFER_FREE,
            "certificate_price": None,
        }

    if free_modes:
        offer = (
            RICHIE_OFFER_FREE
            if any(CourseMode.is_eligible_for_certificate(mode.slug) for mode in free_modes)
            else RICHIE_OFFER_PARTIALLY_FREE
        )
        fields = {
            "offer": offer,
            "price": None,
            "certificate_offer": RICHIE_OFFER_PAID,
            "certificate_price": cheapest_paid_mode.min_price,
        }
    else:
        fields = {
            "offer": RICHIE_OFFER_PAID,
            "price": cheapest_paid_mode.min_price,
            "certificate_offer": RICHIE_OFFER_FREE,
            "certificate_price": None,
        }

    currency = (cheapest_paid_mode.currency or "").upper()
    if currency:
        fields["price_currency"] = currency

    return fields


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
        getattr(settings, "RICHIE_OPENEDX_SYNC_COURSE_HOOKS", []),
    )
    if not hooks:
        log.info("No richie course hook found for organization '%s'. Please configure the "
            "'RICHIE_OPENEDX_SYNC_COURSE_HOOKS' setting or as site configuration", org)
        return {}

    include_payment_fields = configuration_helpers.get_value_for_org(
        org,
        "RICHIE_OPENEDX_SYNC_INCLUDE_PAYMENT_FIELDS",
        getattr(settings, "RICHIE_OPENEDX_SYNC_INCLUDE_PAYMENT_FIELDS", False),
    )
    include_payment_fields = _parse_boolean_setting(include_payment_fields)

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

    enrollment_count = CourseEnrollment.objects.filter(course_id=course_id).count()
    languages = [transform_language(org, course.language or settings.LANGUAGE_CODE)]
    payment_fields = _get_course_payment_fields(course_key) if include_payment_fields else {}

    result = {}

    for hook in hooks:
        resource_link = hook.get(
            "resource_link_template", "https://{lms_domain}/courses/{course_id}/info"
        ).format(lms_domain=lms_domain, course_id=str(course_id))

        data = {
            "resource_link": resource_link,
            "start": course_start,
            "end": course_end,
            "enrollment_start": enrollment_start,
            "enrollment_end": enrollment_end,
            "languages": languages,
            "enrollment_count": enrollment_count,
            "catalog_visibility": course.catalog_visibility,
            **payment_fields,
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

            log.info(
                "Synchronized the course %s to richie site %s it returned the HTTP status code %d response content: %s",
                course_id,
                richie_url,
                response.status_code,
                response.content,
            )
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
