# Roadmap

## Release Milestones

### v0.1.0 — Foundation & Legacy Migration
Deliverables
- Package skeleton so `ComfyUI_Arena` ships as a single bundle.
- Migrate legacy nodes without behaviour changes.
- Document install paths and migration steps.

Acceptance Criteria
- Legacy users can install via documented steps without manual moves.
- Existing workflows continue to work.
- README/install docs reflect final package boundaries.

### v0.2.0 — ArenaAutoCache MVP ✅ **COMPLETED**
Deliverables
- ✅ Ship "Arena AutoCache: Stats" (`ArenaAutoCacheStats`) and "Arena AutoCache: Trim" (`ArenaAutoCacheTrim`).
- ✅ Expose toggles (e.g., `ARENA_CACHE_ENABLE`) and document them.
- ✅ Provide example cache workflows and troubleshooting notes.
- ✅ **NEW**: Visual copy status indicator with real-time progress
- ✅ **NEW**: Smart model filtering (size and hardcoded paths)

Acceptance Criteria
- ✅ Hit/miss statistics and trimming work end‑to‑end.
- ✅ Config variables toggle as documented.
- ✅ Troubleshooting covers top failure scenarios.
- ✅ **NEW**: Visual feedback for copy operations
- ✅ **NEW**: Intelligent model selection for cache optimization

### v0.2.1 — Enhanced UX & Smart Filtering ✅ **COMPLETED**
Deliverables
- ✅ Visual copy status indicator with real-time progress display
- ✅ Model size filtering (skip < 1GB models)
- ✅ Hardcoded path filtering (skip fixed-location models)
- ✅ Enhanced configuration with filter settings
- ✅ Updated documentation and examples

Acceptance Criteria
- ✅ Copy operations show real-time progress
- ✅ Small models remain on NAS automatically
- ✅ Fixed-path models are skipped intelligently
- ✅ All features documented with examples

### v0.3.0 — ArenaUpdater MVP
Deliverables
- Implement update flows for Hugging Face and CivitAI assets with CLI status hooks.
- Document scheduling, credentials, and rollback guidance.
- Integrate updater logs with cache status outputs.

Acceptance Criteria
- Automated jobs pull updates within configured windows.
- Manual refresh and progress observation documented.
- Rollback steps validated in staging.

### v0.4.0 — Benchmarks & UI Observability
Deliverables
- Benchmark I/O throughput and cache hit‑rate; publish results and tuning tips.
- (Deferred) Re‑introduce lightweight UI overlay for AutoCache with robust Desktop compatibility (no reliance on unstable events; graceful fallbacks).
- Guidance for exporting metrics to external dashboards.

Acceptance Criteria
- Benchmark suite runs with published results.
- UI nodes render real‑time state and handle disabled features gracefully.
- External monitoring validated against a Prometheus‑compatible target.

## Planning Horizons

### Short‑Term (Next Release)
- Solidify caching workflows, finalize config docs, and collect feedback.

### Mid‑Term (Following Release)
- Prepare updater (credentials, quotas, staging) and align telemetry.

### Long‑Term (Beyond v0.3.0)
- Explore benchmarks and UI enhancements once foundations stabilize.
- Evaluate backlog items (e.g., multi‑instance cache coordination).

## Идеи для развития

### Кэширование настроек (Приоритет: 0.7)
**Описание**: Добавить кэширование загруженных настроек из .env файла для ускорения повторного создания нод Arena AutoCache.

**Обоснование**: При создании множественных нод Arena на одном канвасе происходит повторная загрузка .env файла. Кэширование настроек в памяти ускорит создание нод и снизит нагрузку на файловую систему.

**Техническое решение**: 
- Создать глобальный кэш настроек с TTL
- Проверять модификацию .env файла для обновления кэша
- Использовать кэш в конструкторе ноды

### Валидация .env файла (Приоритет: 0.5)
**Описание**: Добавить проверку корректности .env файла при загрузке с предупреждениями о некорректных значениях.

**Обоснование**: Некорректные значения в .env файле могут привести к неожиданному поведению ноды. Валидация поможет пользователям быстро выявить проблемы с конфигурацией.

**Техническое решение**:
- Расширить существующую валидацию в `_load_env_file()`
- Добавить детальные сообщения об ошибках
- Предупреждения о неизвестных ключах и некорректных значениях