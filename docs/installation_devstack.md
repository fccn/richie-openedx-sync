# Devstack installation of Richie Open edX Synchronization

This document describes how you can develop this module on a running Open edX [devstack](https://github.com/edx/devstack).

Steps:

## Start an Open edX [devstack](https://github.com/edx/devstack)

## Install richie_openedx_sync Django application

Open a shell on studio docker container devstack.

```python
make studio-shell
```

Clone this project to the `src` parent folder where you have put the Open edX devstack.

```python
cd /edx/src/edxapp/
git clone https://github.com/fccn/richie-openedx-sync.git
pip install -e /edx/src/edxapp/richie-openedx-sync
```

So you should have your folders like this on your machine:
```
.. devstack
.. edx-plaform
.. (...) other edx repositories
.. src
.... edxapp
...... richie_openedx_sync
```

## Active the `richie_openedx_sync` Django application
On the Open edX devstack edit the file and add the `richie_openedx_sync` app
to the `INSTALLED_APPS` on the file `cms/envs/devstack.py` within edx-platform.

## Hosts
When your are developing the connection between Open edX and Richie, because both stacks aren't
on the same docker-compose then it isn't easy connect both docker containers.
Next it is described an easy approach for rapid development and verification.

You need to add the `richie.local.dev` virtual host with your local IP address to the hosts
file on your host machine or to the Studio hosts.

Find your local IP Address, eg. like 192.168....

Add the next line to the `/etc/hosts` file of your host machine:
```bash
<Your local IP Address> richie.local.dev
```

## Open edX site configuration

Open your Open edX devstack, eg. http://localhost:18000, on the 
[Site Configuration](http://localhost:18000/admin/site_configuration/siteconfiguration/1/change/)
Django administration page add the next configurations ( don't forget to replace the secret! ):

```json
"RICHIE_OPENEDX_SYNC_COURSE_HOOKS": [
    {
        "secret": "changeme",
        "url": "http://richie.local.dev:8070/api/v1.0/course-runs-sync/",
        "timeout": "6"
    }
]
```

By default Open edX devstack uses those credentials:
- user: edx
- pass: edx


## Richie env variables
Start the richie development with this variables on the `env.d/development/dev` file that contains
the environment variables.
Don't forget to replace the secret, it should need to have the same value configured on previous
step.

File `env.d/development/dev` should contain:
```
EDX_BASE_URL=https://localhost:18000
EDX_BACKEND=richie.apps.courses.lms.edx.EdXLMSBackend
EDX_COURSE_REGEX=^.*/courses/(?P<course_id>.*)/info$
DJANGO_RICHIE_COURSE_RUN_SYNC_SECRETS=changeme
```

## Troubleshooting

On Richie Django you can add this setting so you can view errors on log.
```
DEBUG_PROPAGATE_EXCEPTIONS = True
```
