from django.conf import settings

# Load `RICHIE_OPENEDX_SYNC_COURSE_HOOKS` setting using the open edX `ENV_TOKENS` production mode.
# This requires the `RICHIE_OPENEDX_SYNC_COURSE_HOOKS` should be added to the `EDXAPP_ENV_EXTRA`
# on the ansible deployment configuration.
settings.RICHIE_OPENEDX_SYNC_COURSE_HOOKS = getattr(settings, "ENV_TOKENS", {}).get(
    "RICHIE_OPENEDX_SYNC_COURSE_HOOKS",
    getattr(settings, "RICHIE_OPENEDX_SYNC_COURSE_HOOKS", None),
)

# Load `RICHIE_ROOT_URL` setting using the open edX `ENV_TOKENS` production mode.
# This requires the `RICHIE_ROOT_URL` should be added to the `EDXAPP_ENV_EXTRA` on the
# ansible deployment configuration.
settings.RICHIE_ROOT_URL = getattr(settings, "ENV_TOKENS", {}).get(
    "RICHIE_ROOT_URL",
    getattr(settings, "RICHIE_ROOT_URL", None),
)
