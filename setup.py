#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import os
import re

from setuptools import setup


def load_requirements(*requirements_paths):
    """
    Load all requirements from the specified requirements files.
    Returns a list of requirement strings.
    """
    requirements = set()
    for path in requirements_paths:
        requirements.update(
            line.split('#')[0].strip() for line in open(path).readlines()
            if is_requirement(line)
        )
    return list(requirements)


def is_requirement(line):
    """
    Return True if the requirement line is a package requirement;
    that is, it is not blank, a comment, or editable.
    """
    # Remove whitespace at the start/end of the line
    line = line.strip()

    # Skip blank lines, comments, and editable installs
    return not (
        line == '' or
        line.startswith('-r') or
        line.startswith('#') or
        line.startswith('-e') or
        line.startswith('git+') or
        line.startswith('-c')
    )


def get_version(*file_paths):
    """Retrieves the version from the main app __init__.py"""
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


version = get_version("richie_openedx_sync", "__init__.py")

# Read the contents of your README.md file to long_description variable
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="richie-openedx-sync",
    version=version,
    author="FCT|FCCN NAU",
    author_email="info@nau.edu.pt",
    url="https://github.com/fccn/richie-openedx-sync",
    description="NAU openedX extensions",
    long_description=long_description,
    install_requires=load_requirements('requirements.txt'),
    scripts=[],
    license="AGPL 3.0",
    keywords="Django, Open edX, MOOC, Richie",
    python_requires=">=3.5",
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 3 - Alpha",

        # Should match the Django minor version on requirements
        "Framework :: Django",
        "Framework :: Django :: 2.2",

        # License - should match "license" above
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",

        # Specify the Python versions - should match python_requires above
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
    ],
    platforms=["any"],
    zip_safe=False,
    packages=[
        'richie_openedx_sync',
    ],
    include_package_data=True,
    entry_points={
        "cms.djangoapp": [
            "richie_openedx_sync = richie_openedx_sync.apps:RichieOpenEdxSyncConfig",
        ],
    }
)
