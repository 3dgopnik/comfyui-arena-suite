# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Introduce dedicated Audit and Warmup nodes together with a companion CLI utility so users can inspect and prefill Arena caches directly from ComfyUI or automation scripts.
- Add Arena AutoCache audit/warmup helpers with unified item spec parsing and JSON reports.
- Add regression tests covering Arena AutoCache audit and warmup flows.
### Changed
- Extend Arena AutoCache index metadata to expose byte totals and the last HIT/MISS/TRIM/COPY event.
- Prefix Arena AutoCache and legacy tiles node display names with the 🅰️ marker for consistent UI grouping.
- Localize AutoCache node labels and I/O names based on the `ARENA_LANG` environment variable.
- Enrich Arena AutoCache nodes with localized descriptions, tooltips, and output metadata for ComfyUI.
- Allow `COMFYUI_LANG` to override the AutoCache localization fallback before `ARENA_LANG`.
- Set the legacy tiles segmentation node category to `Arena/Tiles` for improved UI grouping.
### Docs
- Surface an AutoCache TL;DR environment setup block in the README, node README, and RU/EN overview docs.
- Expand the Audit/Warmup node docs with bilingual multiline/JSON examples and `workflow_json` guidance, and mention the nodes in the root README.
- Publish bilingual node reference covering AutoCache and legacy tiles nodes in `custom_nodes/ComfyUI_Arena/README.md` and `docs/{ru,en}/nodes.md`.
- Document the Impact Pack dependency and credit ltdrdata in the README install instructions.
- Note that autocache nodes return disabled stubs when `ARENA_CACHE_ENABLE=0`.
- Describe the expanded AutoCache stats and trim JSON payloads in `custom_nodes/ComfyUI_Arena/README.md`.
- Reorganize documentation under `docs/ru` (with navigation and quickstart/config guides) and add English placeholders linked from the README.
- Restructure `docs/ROADMAP.md` with detailed release milestones, ownership, and planning horizons.
- Normalize `README.md` encoding and restore Russian workflow/docs text without mojibake.
- Highlight the Arena suite goals in the README introduction for English and Russian readers.
- Refresh README and bilingual docs to mention the 🅰️-prefixed display names for AutoCache and legacy tiles nodes.
- Add Dashboard/Ops coverage with compatibility table, status-line examples, and benchmarking guidance in the AutoCache README.
### Fixed
- Aggregate Arena node and display mapping exports at the package root so ComfyUI can discover nodes even when optional submodules fail to import.
- Allow cache lookups to fall back to source files when `.copying` locks persist and clean up stale locks before retrying copies.
- Retry cache population after clearing stale `.copying` locks so the cache path is reused on the next request.
- Recreate cache entries when stale files with mismatched sizes are detected during reuse.
- Prevent cache readers from using files protected by `.copying` locks to avoid partial reads.
- Ensure cache copy failures clean up partial files and surface errors for retry.
- Serialize cache index updates to prevent data races during concurrent access.
- Restore package-level exports so ComfyUI can import `comfyui-arena-suite` from `custom_nodes`.
- Keep cache helpers importable and return stub responses when the cache is disabled.
- Avoid recording cache hits when `.copying` locks disappear but the cached file is missing by falling back to the source path.
