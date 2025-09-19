# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Fixed
- Prevent cache readers from using files protected by `.copying` locks to avoid partial reads.
- Ensure cache copy failures clean up partial files and surface errors for retry.
- Serialize cache index updates to prevent data races during concurrent access.
