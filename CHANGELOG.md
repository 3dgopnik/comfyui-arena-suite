# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- **Bootstrap Scripts v2.0**: New `arena_bootstrap_cache_v2.bat` and `arena_bootstrap_cache_v2.ps1` with Debug/Prod profiles for easy configuration. / **RU:** Новые скрипты `arena_bootstrap_cache_v2.bat` и `arena_bootstrap_cache_v2.ps1` с профилями Debug/Prod для простой настройки.
- **Progress Indicator**: Real-time copy progress display in terminal with percentage and status messages. / **RU:** Индикатор прогресса копирования в терминале с процентами и статусными сообщениями.
- **MB Size Support**: Added `ARENA_CACHE_MIN_SIZE_MB` environment variable for fine-grained size filtering (default: 1024 MB). / **RU:** Поддержка размера в МБ: добавлена переменная `ARENA_CACHE_MIN_SIZE_MB` для точной фильтрации по размеру (по умолчанию: 1024 МБ).
- **NAS Availability Check**: Automatic detection of NAS connectivity before cache operations. / **RU:** Проверка доступности NAS: автоматическое определение подключения к NAS перед операциями кеширования.
- **Cache Permissions Check**: Validation of write permissions to cache directory. / **RU:** Проверка прав кеша: валидация прав записи в папку кеша.
- **Quick Tips System**: Built-in troubleshooting hints and solutions for common issues. / **RU:** Система быстрых подсказок: встроенные советы по устранению неполадок и решениям типичных проблем.

### Fixed
- **Critical Copy Bug**: Fixed `_copy_into_cache_lru() missing 1 required positional argument: 'category'` error that prevented model caching. / **RU:** Критическая ошибка копирования: исправлена ошибка `_copy_into_cache_lru() missing 1 required positional argument: 'category'`, которая препятствовала кешированию моделей.
- **Hardcoded Path Filter**: Debug mode now properly disables `ARENA_CACHE_SKIP_HARDCODED=0` to allow NAS model caching. / **RU:** Фильтр жестко прописанных путей: Debug режим теперь правильно отключает `ARENA_CACHE_SKIP_HARDCODED=0` для разрешения кеширования моделей с NAS.
- **Size Filter Logic**: Updated `_should_skip_by_size()` to support both GB and MB thresholds simultaneously. / **RU:** Логика фильтра размера: обновлена функция `_should_skip_by_size()` для поддержки порогов ГБ и МБ одновременно.

### Changed
- **Node Versioning**: ArenaAutoCacheSmart updated to v2.17 with improved error handling and progress reporting. / **RU:** Версионирование узлов: ArenaAutoCacheSmart обновлен до v2.17 с улучшенной обработкой ошибок и отчетностью о прогрессе.
- **Bootstrap Profiles**: 
  - **Debug Mode**: `ARENA_CACHE_SKIP_HARDCODED=0`, `ARENA_CACHE_MIN_SIZE_GB=0.0`, `ARENA_CACHE_VERBOSE=1` for troubleshooting. / **RU:** Debug режим: отключены фильтры, включены подробные логи для диагностики.
  - **Production Mode**: `ARENA_CACHE_SKIP_HARDCODED=0`, `ARENA_CACHE_MIN_SIZE_GB=1.0`, `ARENA_CACHE_VERBOSE=0` for daily work. / **RU:** Production режим: включены фильтры, обычные логи для повседневной работы.
  - **Default Mode**: `ARENA_CACHE_SKIP_HARDCODED=1`, `ARENA_CACHE_MIN_SIZE_GB=1.0` for safe settings. / **RU:** Default режим: безопасные настройки по умолчанию.

### Added
- **Visual Copy Status Indicator**: New `ArenaAutoCache Copy Status` node displays real-time copy progress with speed, ETA, and filter settings. / **RU:** Новый узел `ArenaAutoCache Copy Status` показывает прогресс копирования в реальном времени со скоростью, оставшимся временем и настройками фильтров.
- **Model Size Filter**: Skip caching models smaller than 1GB (configurable via `ARENA_CACHE_MIN_SIZE_GB`). Small auxiliary models remain on NAS to save cache space. / **RU:** Фильтр размера моделей: пропускать модели меньше 1 ГБ (настраивается через `ARENA_CACHE_MIN_SIZE_GB`). Маленькие вспомогательные модели остаются на NAS для экономии места в кеше.
- **Hardcoded Path Filter**: Skip caching models with fixed paths (ControlNet, InsightFace, etc.) that only work in their specific directories. / **RU:** Фильтр жестко прописанных путей: пропускать модели с фиксированными путями (ControlNet, InsightFace и др.), которые работают только в своих папках.
- **Enhanced Config Node**: `ArenaAutoCache Config` now supports size and path filter settings with environment variable overrides. / **RU:** Улучшенный узел конфигурации: `ArenaAutoCache Config` теперь поддерживает настройки фильтров размера и путей с переопределением через переменные окружения.

### Removed
- Arena AutoCache web overlay (experimental) has been removed from the package by default to prioritize stability across ComfyUI Desktop builds. The feature is tracked for a future iteration in the roadmap.
### Fixed
- Ensure AutoCache workflow parsing assigns CLIP Vision, IPAdapter, InsightFace, CLIP-G, and CLIP-L hints to their dedicated ComfyUI categories before falling back to the generic CLIP bucket.
- Overlay now also listens to execution events (`onAfterExecute`/`onExecuted`) in addition to `onNodeOutputsUpdated` to support ComfyUI Desktop builds that don't emit the outputs-updated callback consistently.
- Overlay polling fallback: periodically reads node outputs (~500 ms) for Dashboard/Ops/Audit nodes to keep the UI in sync even when no frontend events are fired (Desktop compatibility).
- Desktop execution store fallback: when `getOutputData()` returns nothing, the overlay now attempts to read outputs from the Desktop `executionStore` (supports Map/object containers and locator ids like `subgraph:localId`).
- Subscribe to `api.executed` events (via `/scripts/api.js`) and update overlay directly from execution payloads; improves reliability across Desktop frontends.
- Arena AutoCache overlay tests now skip when the web asset bundle is missing, preventing false negatives on minimal installations.
- Legacy preview bridge now reuses cached identifiers for repeated node/file pairs so duplicate entries no longer accumulate.

### Added
- Emit AutoCache copy lifecycle events (start/complete/skip/fail) to the console and PromptServer so overlays receive updates even with verbose logging disabled. / **RU:** Добавлены события копирования (start/complete/skip/fail) в консоль и PromptServer, теперь они доступны даже при отключённом `ARENA_CACHE_VERBOSE`.
- Declare setuptools metadata with explicit package listings and bundle docs/web assets into distributions so wheels ship the Arena overlay.
- Add a CI smoke test that runs `python -m build` on Python 3.10 and 3.11 to guard packaging regressions.
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
- ArenaAutoCache Warmup/Ops nodes expose an optional `log_context` input that forwards node identifiers into copy events for overlay synchronisation. / **RU:** Узлы Warmup/Ops получили необязательный вход `log_context`, передающий ID узла в события копирования для синхронизации с оверлеем.
- Offload Arena AutoCache LRU copies to a background queue so `get_full_path` returns immediately while the worker syncs files. / **RU:** Перенесено LRU-копирование Arena AutoCache в фоновую очередь, теперь `get_full_path` мгновенно отдаёт исходный путь, а воркер копирует файл параллельно.
- Gate AutoCache LRU copies behind workflow allowlists so only registered category/name pairs trigger cache sync. / **RU:** Ограничено LRU-копирование AutoCache allowlist-списком из workflow, теперь синхронизация выполняется только для зарегистрированных пар категория/файл.
- Mark ArenaAutoCache Dashboard/Ops/Audit as OUTPUT_NODE so they execute as graph targets by default (improves Desktop/queue behaviour and overlay updates).
- AutoCache Audit/Warmup/Ops nodes now fall back to the active `PromptServer` workflow when `workflow_json` is empty, keeping allowlists aligned with the current graph. / **RU:** Узлы Audit/Warmup/Ops автоматически берут активный workflow из `PromptServer`, если вход `workflow_json` пуст, чтобы allowlist оставался в актуальном состоянии.
- Update the Arena web directory fallback to prefer package-local assets for portable installs. / **RU:** Обновлён резервный путь веб-ресурсов Arena, теперь используется каталог рядом с пакетом для переносимых сборок.
- Auto-detect the Arena AutoCache web overlay from `ComfyUI/custom_nodes/comfyui-arena-suite/web`, eliminating manual copy steps. / **RU:** Автоматически определяем веб-оверлей Arena AutoCache из `ComfyUI/custom_nodes/comfyui-arena-suite/web`, ручное копирование больше не требуется.
- Register the Arena AutoCache web overlay as an ESM module while falling back to the legacy global `app` lookup and logging a clear status message. / **RU:** Регистрируем веб-оверлей Arena AutoCache как ESM-модуль с откатом к глобальному `app` и понятным сообщением о статусе загрузки.
- Log legacy module import failures as warnings so the package loads without those nodes instead of aborting.
- Launch `arena_bootstrap_cache.bat` with the WinForms helper when PowerShell is available and fall back to CLI prompts otherwise.
- Expose Arena AutoCache Ops mode selection as a validated dropdown and document the available options.
- Prepare the AutoCache Audit node to accept extended stats and settings override arguments without altering current behaviour.
- Extend Arena AutoCache index metadata to expose byte totals and the last HIT/MISS/TRIM/COPY event.
- Prefix Arena AutoCache and legacy tiles node display names with the 🅰️ marker for consistent UI grouping.
- Drop experimental AutoCache localization support; node labels now remain in English regardless of environment variables.
- Set the legacy tiles segmentation node category to `Arena/Tiles` for improved UI grouping.
- Enrich audit and warmup payloads with `ui`/`timings` metadata and extend ops execution to cover audit, warmup, and trim modes.
- Record audit summaries with explicit action feedback so UI widgets can confirm applied settings and trims.
- Prefill Arena AutoCache overlay state on node creation so idle nodes render their headline and palette without waiting for outputs.
- Reorder Arena Ops mode constant declarations ahead of the node class definition to clarify initialization ordering.
### Docs
- Document the new copy notification channel and `log_context` behaviour in the RU/EN node references. / **RU:** Описан канал уведомлений и вход `log_context` в справочниках узлов (RU/EN).
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
- Document that AutoCache nodes are English-only and remove references to the `ARENA_LANG` override in RU/EN guides.
- Add Dashboard/Ops coverage with compatibility table, status-line examples, and benchmarking guidance in the AutoCache README.
- Document the new dashboard/ops nodes and timing fields in the bilingual node references.
- Clarify Windows cache bootstrap vs. session overrides in the quickstart/config guides (RU/EN).
### Fixed
- Log a warning when Arena web assets are missing instead of exposing a fake `web` directory so ComfyUI skips registration.
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
- Keep the AutoCache overlay in sync on Desktop builds by falling back to node execution events when `graph.onNodeOutputsUpdated` is unavailable. / **RU:** Поддерживаем актуальность оверлея AutoCache в Desktop-сборках, подписываясь на выполнение узлов при отсутствии `graph.onNodeOutputsUpdated`.
