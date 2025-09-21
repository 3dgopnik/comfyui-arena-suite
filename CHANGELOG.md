# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Add Arena AutoCache web overlay extension that parses `summary_json`/`warmup_json`/`trim_json` sockets and surfaces live node status, progress bars, and warnings inside the ComfyUI graph.
- Introduce dedicated Audit and Warmup nodes together with a companion CLI utility so users can inspect and prefill Arena caches directly from ComfyUI or automation scripts.
- Add Arena AutoCache audit/warmup helpers with unified item spec parsing and JSON reports.
- Add regression tests covering Arena AutoCache audit and warmup flows.
- Add Arena AutoCache dashboard and ops nodes with mode selection, benchmarking toggles, and dedicated smoke tests.
- Extend the Arena AutoCache Audit node with optional `summary_json` output, runtime overrides, and multi-category extended stats plus trim execution feedback.
- Add a snapshot-backed test to lock the Arena AutoCache summary/warmup/trim JSON payload structure.
- Introduce `arena_bootstrap_cache.bat` to persist Arena AutoCache variables on Windows and prime the current session.
- Add a WinForms bootstrap helper (`scripts/arena_bootstrap_cache.ps1`) for selecting the cache folder and limit on Windows.
### Changed
- Auto-detect the Arena AutoCache web overlay from `ComfyUI/custom_nodes/comfyui-arena-suite/web`, eliminating manual copy steps. / **RU:** Автоматически определяем веб-оверлей Arena AutoCache из `ComfyUI/custom_nodes/comfyui-arena-suite/web`, ручное копирование больше не требуется.
- Register the Arena AutoCache web overlay as an ESM module while falling back to the legacy global `app` lookup and logging a clear status message. / **RU:** Регистрируем веб-оверлей Arena AutoCache как ESM-модуль с откатом к глобальному `app` и понятным сообщением о статусе загрузки.
- Log legacy module import failures as warnings so the package loads without those nodes instead of aborting.
- Launch `arena_bootstrap_cache.bat` with the WinForms helper when PowerShell is available and fall back to CLI prompts otherwise.
- Expose Arena AutoCache Ops mode selection as a validated dropdown and document the available options.
- Prepare the AutoCache Audit node to accept extended stats and settings override arguments without altering current behaviour.
- Extend Arena AutoCache index metadata to expose byte totals and the last HIT/MISS/TRIM/COPY event.
- Prefix Arena AutoCache and legacy tiles node display names with the 🅰️ marker for consistent UI grouping.
- Localize AutoCache node labels and I/O names based on the `ARENA_LANG` environment variable.
- Enrich Arena AutoCache nodes with localized descriptions, tooltips, and output metadata for ComfyUI.
- Allow `COMFYUI_LANG` to override the AutoCache localization fallback before `ARENA_LANG`.
- Set the legacy tiles segmentation node category to `Arena/Tiles` for improved UI grouping.
- Enrich audit and warmup payloads with `ui`/`timings` metadata and extend ops execution to cover audit, warmup, and trim modes.
- Record audit summaries with explicit action feedback so UI widgets can confirm applied settings and trims.
- Prefill Arena AutoCache overlay state on node creation so idle nodes render their headline and palette without waiting for outputs.
### Docs
- Document the auto-discovery path and DevTools verification flow for the Arena web overlay in the README, RU/EN guides, and node reference. / **RU:** Задокументирован путь автообнаружения и проверка через DevTools для веб-оверлея Arena в README, русских/английских гайдах и справочнике узлов.
- Document the AutoCache web overlay behaviour and coverage in the bilingual node reference.
- Add step-by-step AutoCache web overlay enablement instructions with UI indicator summaries across the README and RU/EN docs.
- Surface an AutoCache TL;DR environment setup block in the README, node README, and RU/EN overview docs.
- Document the new Audit node summary output, runtime overrides, and trim behaviour in the AutoCache README and RU/EN node references.
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
- Document the new dashboard/ops nodes and timing fields in the bilingual node references.
- Clarify Windows cache bootstrap vs. session overrides in the quickstart/config guides (RU/EN).
### Fixed
- Prevent the bootstrap CLI fallback from hitting `Unexpected at this time` when cache paths end with a backslash or the limit prompt returns empty input.

- Normalize AutoCache overlay output aliases so localized socket names update the summary, warmup, and trim panels consistently.
- Escape trailing backslashes when persisting Windows cache variables so `setx` handles quoted paths without errors.
- Ensure `arena_set_cache.bat` leaves `ARENA_CACHE_*` variables available in the parent CMD session for subsequent launches.
- Trigger the Arena cache folder picker when no path is supplied and quote the PowerShell command so the selection populates `CACHE_ROOT` correctly.
- Point AutoCache web assets discovery at the repository-level `web` directory so the overlay loads without manual symlinks.
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
- Reset the AutoCache overlay palette and messages when node outputs are cleared so idle nodes no longer show stale highlights.
- Defer AutoCache web overlay registration until the ComfyUI app exposes `registerExtension`, preventing crashes when `app` is not ready yet. / **RU:** Откладываем регистрацию веб-оверлея AutoCache до появления метода `registerExtension` в ComfyUI, чтобы скрипт не падал при поздней инициализации `app`.
