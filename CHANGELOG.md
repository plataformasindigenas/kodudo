# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-19

### Added
- Multi-output batch rendering via `outputs` config field (renders multiple files from one config)
- Per-record rendering via `foreach` config field with `{var.field}` path interpolation
- Cartesian product of `outputs` x `foreach` for locale x record rendering
- `cook_from_config()` now accepts `context` and `output` keyword overrides for runtime customization
- New types: `BatchConfig`, `OutputSpec`
- New functions: `expand_config()`, `interpolate_path()`

### Changed
- **Breaking**: `cook()` returns `list[Path]` instead of `Path`
- **Breaking**: `cook_from_config()` returns `list[Path]` instead of `Path`
- **Breaking**: `load_config()` returns `BatchConfig` instead of `Config`
- CLI prints each output path when multi-output configs produce multiple files

## [0.1.1] - 2026-01-23

### Added
- CLI support for cooking multiple config files at once (`kodudo cook config1.yaml config2.yaml`)

### Fixed
- Linting and type errors in tests
- Updated README with badges, improved CLI usage examples, and detailed configuration guide matching the Aptoro project structure
