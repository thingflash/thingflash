# Changelog

All notable changes to this project are documented in this file.

## [0.0.2] - Unreleased

### Added

- `thingflash doctor` command that checks AWS credentials, region, and permissions.
- `thingflash permissions` command that prints the least-privilege IAM policy
  ThingFlash needs, together with the commands to create and attach it.
- `thingflash doctor --fix` flag that creates and attaches that policy for you
  when the caller has IAM write access.

## [0.0.1] - 2026-07-19

### Added

- `thingflash init` command that generates a starter `thingflash.yaml` manifest.
- Initial release: project skeleton, packaging, and the `thingflash` CLI entry point.
