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

### Making a release

Making a release is automated. The choice between a minor or a revision type of release is
determined by the presence of an addition, a change or a removal. A revision release is made
if only fixes are present in the changelog, otherwise a minor release is made.

For example, to release and commit all changes:

```
bin/release --commit
```

If you consider that the changelog contains breaking changes, you can force a major release
by passing the parameter `--major`.


To release but without committing the changes:

```
bin/release --major
```

To release and committing the changes:

```
bin/release --commit
```

After merging release commits to the master branch, you can tag them automatically by running:

```
bin/tag -c
```

## Contributions / Acknowledgments

- FUN-MOOC [fun-apps courses](https://github.com/openfun/fun-apps)
- [Richie](https://richie.education/) and on [Github](https://github.com/openfun/richie)

## License

This work is released under the AGPL-3.0 License (see [LICENSE](./LICENSE)).