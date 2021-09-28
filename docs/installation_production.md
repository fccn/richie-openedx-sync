# Instructions to install Richie Open edX Synchronization using ansible

The next steps describes how you can configure the synchronization between Richie and Open edX 
using [ansible](https://github.com/edx/configuration).

## Requirements

Add this current repository to your `EDXAPP_EXTRA_REQUIREMENTS`.

```yml
EDXAPP_EXTRA_REQUIREMENTS:
  - name: 'git+https://github.com/fccn/richie-openedx-sync@xxxxxxxxxxxxxxxxx#egg=richie_openedx_sync'
    extra_args: -e
```

## INSTALLED_APPS
To add this application on the Django `INSTALLED_APPS`, it is required that you add it to the `ADDL_INSTALLED_APPS` on `EDXAPP_ENV_EXTRA`.

```yml
EDXAPP_ENV_EXTRA:
  # ...
  ADDL_INSTALLED_APPS:
    - richie_openedx_sync
  # ...
```

## Configure Richie course hook
If you want to use synchronization using the `sync_courses_to_richie` Django command, 
then you need to add this configuration to the `ADDL_INSTALLED_APPS` on `EDXAPP_ENV_EXTRA`. 
Alternativelly you can add it to the Open edX Django administration Site Configuration, 
but you can't use the command.

Ansible:
```yml
EDXAPP_ENV_EXTRA:
  # ...
  RICHIE_OPENEDX_SYNC_COURSE_HOOKS: 
    - url: http://www.example.com/api/v1.0/course-runs-sync/
      secret: changeme
  # ...
```

JSON Site Configuration:
```json
"RICHIE_OPENEDX_SYNC_COURSE_HOOKS": [
    {
      "url": "http://www.example.com/api/v1.0/course-runs-sync/",
      "secret": "abcchangemed1234"
    }
]
```

## Richie env variables
On Richie site add the next environment variables. Depending on your configuration on a docker env.d file or directly on the docker-compose file. 
Don't forget to replace the secret with the same value configured on previous step.

```
EDX_BASE_URL=https://localhost:18000
EDX_BACKEND=richie.apps.courses.lms.edx.EdXLMSBackend
EDX_COURSE_REGEX=^.*/courses/(?P<course_id>.*)/info$
DJANGO_RICHIE_COURSE_RUN_SYNC_SECRETS=changeme
```
