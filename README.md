# Richie Open edX Synchronization application
This Django application is to be installed with an existing Open edX installation.
It registers a Django signal that when a course staff changes the schedule of a course it will
update the Richie marketing site.

## Devstack installation

Start a open edx devstack.

Open a shell to studio docker container devstack.

```python
make studio-shell
```

Clone this project to the `src` parent folder where you have put the open edx devstack.

- devstack
- edx-plaform
... other edx repositories

- src
- - edxapp/richie_openedx_sync

cd /edx/src/edxapp/

git clone git@github.com:fccn/richie-openedx-sync.git
cd richie_openedx_sync
pip install -e .

Active the Djanto app. On the open edX devstack edit the file and add the `richie_openedx_sync` app
to the INSTALLED_APPS on the file `cms/envs/devstack.py` within edx-platform.

Add to /etc/hosts of the STUDIO open edX container
```bash
make studio-shell
vim /etc/hosts
```

The line:
```bash
<Your local IP Address like 192.168....> richie.local.dev
```

Start the richie development with this variables on the `env.d/development/dev` file that contains
the environment variables.
Don't forget to replace the secret.
```
EDX_BASE_URL=https://localhost:18000
EDX_BACKEND=richie.apps.courses.lms.edx.EdXLMSBackend
EDX_COURSE_REGEX=^.*/courses/(?P<course_id>.*)/info$

DJANGO_RICHIE_COURSE_RUN_SYNC_SECRETS=changeme
```

Add this configuration to your Open edX site configuration. The secret value should have the same
previous secret value.
```
"RICHIE_OPENEDX_SYNC_COURSE_HOOKS": [
    {
        "secret": "changeme",
        "url": "http://richie.local.dev:8070/api/v1.0/course-runs-sync/",
        "timeout": "6"
    }
]
```

On Richie Django you can add this setting so you can view errors on log.
```
DEBUG_PROPAGATE_EXCEPTIONS = True
```

## Installation on production

This is the steps that you need to execute if you are deploying open edX using the ansible way (using [configuration](https://github.com/edx/configuration) repository).

Add this current repository to your `EDXAPP_EXTRA_REQUIREMENTS`.

```yml
EDXAPP_EXTRA_REQUIREMENTS:
    - name: 'git+https://github.com/fccn/richie-openedx-sync@xxxxxxxxxxxxxxxxx#egg=richie_openedx_sync'
      extra_args: -e
```

Add this Django app to the `ADDL_INSTALLED_APPS` on the open edX extra environment configuration.

```yml
EDXAPP_ENV_EXTRA:
    # ...
    ADDL_INSTALLED_APPS:
        - richie_openedx_sync
    # ...
```
