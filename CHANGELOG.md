# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0-alpha] - 2025-09-25

### Added
- Complete repository restart with clean structure
- ArenaAutoCacheSimple node for automatic model caching
- Web extensions for ComfyUI integration
- Comprehensive documentation and CI/CD setup
- Modern Python project structure with pyproject.toml

### Changed
- Migrated from legacy codebase to modern architecture
- Simplified node structure and API
- Updated documentation to reflect new structure

### Removed
- Legacy autocache implementation
- Outdated documentation and scripts
- Moved to clean, maintainable codebase

## [2.17.0] - 2025-09-24

### Fixed
- Fixed `_copy_into_cache_lru()` missing required positional argument 'category'
- Updated ArenaAutoCacheSmart to v2.17
- Improved error handling in cache operations

### Changed
- Enhanced cache management with better parameter handling
- Updated model caching workflow for better reliability

## [2.16.0] - 2025-09-23

### Added
- New ArenaAutoCacheSmart node with advanced caching features
- Support for multiple model types (checkpoints, loras, vaes, clips)
- Automatic cache directory management
- Progress tracking for cache operations

### Changed
- Improved cache performance and reliability
- Better error handling and user feedback
- Enhanced documentation and examples