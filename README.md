# Richie Open edX Synchronization application

## Overview

The aim of this Django application is to synchronize the Open edX courses to the Richie marketing site.
Whenever a course schedule or details are updated on Studio a hook is run that sends the updated information to Richie.
There is also a Django command that permit to synchronize all existing courses.

## Installation

1. [Instructions](docs/installation_devstack.md) to install on a running Open edX [devstack](https://github.com/edx/devstack)
2. [Instructions](docs/installation_production.md) to install on a production grade Open edX using ansible - [configuration](https://github.com/edx/configuration)

## Open edX compatibility

This app has been tested with Open edX Juniper, but it should run on newer versions.

## Contributions / Acknowledgments

- FUN-MOOC [fun-apps courses](https://github.com/openfun/fun-apps)
- [Richie](https://richie.education/) and on [Github](https://github.com/openfun/richie)

## License

This work is released under the AGPL-3.0 License (see [LICENSE](./LICENSE)).