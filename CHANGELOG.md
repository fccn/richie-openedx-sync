# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic
Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.4.0] - 2024-05-29

### Added

- Added the `resource_link_template` configuration on hooks, to change the default format
  link for each course.

### Changed

- Removed the `RICHIE_OPENEDX_SYNC_LOG_REQUESTS` setting with lazy logging.

## [1.3.0] - 2024-04-18

### Changed

- Increase default timeout.
- Change logging integration to Richie from ERROR to WARNING level.

## [1.2.0] - 2022-08-25

### Fixed

- Refactor Open edX code imports.
  Related with the removal of custom config of edx-platform sys.path.
  Change code to run on Open edX Lilac and following releases.

### Added

- Add setting that allow to log richie requests

## [1.1.1] - 2022-03-23

### Fixed

- Fix fallback Richie enrollment start from course start

## [1.1.0] - 2022-01-27

### Fixed

- Fix readme
- Fix missing failed messages on log
- When configured with multiple Richie sites, don't stop on the 1st error.

### Added

- Send course `catalog_visibility` to richie

## [1.0.0] - 2021-11-26

### Added

- Added a CHANGELOG.md to register the changes of the project
- Added release and tag scripts
- Added Github actions continuous integration
- Automatically publish the package to pypi if building a tag

## [0.1.0] - 2021-09-30

### Added

- Initial release
