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
-- edxapp/richie_openedx_sync


cd /edx/src/edxapp/

git clone git@
cd richie_openedx_sync
pip install -e .


To access host port from the Studio docker container run this on the host machine
```bash
ip addr show docker0 | grep -Po 'inet \K[\d.]+'
```

Then use put that IP on the host machine on the file /etc/hosts like this:
```
<IP> richie.local.dev
```

## Installation on production

Add this Django app on the `ADDL_INSTALLED_APPS` open edX environment variable.
