"""
Utility functions for the Richie Open edX Sync app.
"""

import ast
import json
from django.conf import settings
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


DEFAULT_LANGUAGE_MAPPING = {'pt_PT': 'pt'}


def transform_language(org: str, language: str) -> str:
    """
    The platform can use a default language that isn't compatible on Richie side.
    In this case we need to transform the language to a compatible one.
    This function acts as a transformer for the language to be sent to Richie, it can be used as a hook in the configuration.
    Other cases it should default to the original/input language.

    Read a setting with the value of:
    ```
    {'pt_PT': 'pt'}
    ```
    Cases:
    - input: `pt_PT` -> output: `pt`
    - input: `pt` -> output: `pt`
    - input: `es` -> output: `es`
    - input: `es_ES` -> output: `es_ES`

    Or
    ```
    {'pt': 'pt_PT', 'fr_CA': 'fa'}
    ```
    Cases:
    - input: `pt_PT` -> output: `pt`
    - input: `pt` -> output: `pt`
    - input: `es` -> output: `es`
    - input: `es_ES` -> output: `es_ES`
    - input: `fr_CA` -> output: `fr`
    """

    language_mapping = configuration_helpers.get_value_for_org(
        org,
        "RICHIE_OPENEDX_SYNC_LANGUAGE_MAPPING",
        getattr(settings, "RICHIE_OPENEDX_SYNC_LANGUAGE_MAPPING", DEFAULT_LANGUAGE_MAPPING),
    )

    # Convert string representation to dict if needed
    if isinstance(language_mapping, str):
        try:
            language_mapping = json.loads(language_mapping)
        except (ValueError, TypeError):
            try:
                language_mapping = ast.literal_eval(language_mapping)
            except (ValueError, SyntaxError):
                language_mapping = {}

    if not language_mapping:
        language_mapping = DEFAULT_LANGUAGE_MAPPING

    language_mapping = dict(language_mapping)

    # Try to find a mapping for the language, if not found return the original language
    return language_mapping.get(language, language)
