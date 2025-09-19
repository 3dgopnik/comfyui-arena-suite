# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Docs
- Document the Impact Pack dependency and credit ltdrdata in the README install instructions.
### Fixed
- Allow cache lookups to fall back to source files when `.copying` locks persist and clean up stale locks before retrying copies.
- Retry cache population after clearing stale `.copying` locks so the cache path is reused on the next request.
- Recreate cache entries when stale files with mismatched sizes are detected during reuse.
- Prevent cache readers from using files protected by `.copying` locks to avoid partial reads.
- Ensure cache copy failures clean up partial files and surface errors for retry.
- Serialize cache index updates to prevent data races during concurrent access.
- Restore package-level exports so ComfyUI can import `comfyui-arena-suite` from `custom_nodes`.
