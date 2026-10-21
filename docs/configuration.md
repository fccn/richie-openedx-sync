# Configuration

## Settings

- `INSTALLED_APPS` need to include `richie_openedx_sync` to install this application
- `RICHIE_OPENEDX_SYNC_COURSE_HOOKS` the most important configuration. Could be configured globally on using Django settings or per organization using multi-site site configuration. This hooks consists of a list of configurations. It is required the `secret` and `url`, the other are optional - `timeout` and `resource_link_template`.

Python:
```python
RICHIE_OPENEDX_SYNC_COURSE_HOOKS=[
    {
        "secret": "changeme",
        "url": "http://richie.local.dev:8070/api/v1.0/course-runs-sync/",
        "timeout": "6",
        "resource_link_template": "http://{lms_domain}/courses/{course_id}/info",
    },
]
```

JSON on site configuration:
```json
"RICHIE_OPENEDX_SYNC_COURSE_HOOKS": [
    {
        "secret": "changeme",
        "url": "http://richie.local.dev:8070/api/v1.0/course-runs-sync/",
        "timeout": "6",
        "resource_link_template": "http://{lms_domain}/courses/{course_id}/info"
    }
]
```

- `RICHIE_OPENEDX_SYNC_INCLUDE_PAYMENT_FIELDS` optional, defaults to `False`. When enabled, the
  price information of the course is also sent to Richie. Like the hooks, it can be configured
  globally using Django settings or per organization using multi-site site configuration.

The payment fields are computed from the Open edX course modes of the course, the cheapest paid
mode being the one advertised on Richie:

| Open edX course modes | `offer`          | `price` | `certificate_offer` | `certificate_price` |
| --------------------- | ---------------- | ------- | ------------------- | ------------------- |
| honor                 | `free`           | -       | `free`              | -                   |
| audit + verified      | `partially_free` | -       | `paid`              | verified price      |
| honor + verified      | `free`           | -       | `paid`              | verified price      |
| verified              | `paid`           | price   | `free`              | -                   |

`audit` and `honor` are both free of charge, but only `honor` is eligible for a certificate, so a
course that can be completed on `honor` is entirely `free` while the same course on `audit` is only
`partially_free`. When there is a free mode, whatever is paid buys the certificate. When there
isn't, the price buys the course itself and the certificate comes with it at no extra cost.

`price_currency` is sent in ISO 4217 format, uppercased from the course mode currency, and is only
sent when there is a price to go with it. Richie has no notion of the `subscription` offer in Open
edX, so that value is never sent.

Note that this requires a Richie version that supports these fields on the course runs sync API,
Richie 3.4.0 or newer.

- `RICHIE_OPENEDX_SYNC_ENROLLMENT_DEBOUNCE_SECONDS` optional, defaults to `0` (disabled). Every
  enrollment queues a synchronization of its course, so a burst of enrollments, for example when a
  course starts, queues hundreds of tasks that send the same course data to Richie. With a value
  above `0` the first enrollment of a course schedules a single synchronization that starts after
  that many seconds (plus a few seconds of margin) and the next enrollments of the same course are
  skipped until the window ends. The task reads the course data when it runs, so it sends the
  final `enrollment_count`. It is configured globally, using Django settings or the `ENV_TOKENS`
  of the production mode, not per organization.
  - The window is kept in the Django cache, so it is shared by all the LMS processes when the
    cache is shared. If the cache is not available the synchronization is queued without a
    debounce, it is never lost.
  - Keep it well below the visibility timeout of the broker. With Redis, a delayed task that a
    worker held when it stopped only returns to the queue after that timeout.
  - The synchronization triggered by a course publish is never debounced.

## Multi site
If you have a multi site instance, you can configure a specific hook for that Organization.

Example of Open edX [Site Configuration](http://localhost:18000/admin/site_configuration/siteconfiguration/1/change/)
Django administration page add the next configurations:

```json
"RICHIE_OPENEDX_SYNC_COURSE_HOOKS": [
    {
        "secret": "changeme",
        "url": "http://richie.local.dev:8070/api/v1.0/course-runs-sync/",
        "timeout": "6",
        "resource_link_template": "http://{lms_domain}/courses/{course_id}/info"
    }
]
```