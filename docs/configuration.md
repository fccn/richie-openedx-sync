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