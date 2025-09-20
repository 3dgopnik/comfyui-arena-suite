# ComfyUI_Arena

Single-package for all **Arena** nodes.

- `legacy/` - migrated from local install.
- `autocache/` - SSD auto-cache.
- `updater/` - model updater (WIP).

> Python bytecode and `__pycache__` are excluded by `.gitignore`.

## AutoCache nodes

### ArenaAutoCacheConfig

**RU**

Помощник для настройки SSD-кэша без перезапуска ComfyUI. Расположите узел в начале графа и укажите желаемые параметры.

- **Входы**
  - `cache_root` (`STRING`, по умолчанию активное значение) — путь к каталогу кэша. Пустая строка сохраняет текущую настройку.
  - `max_size_gb` (`INT`, ≥ 0) — лимит размера кэша в гигабайтах (GiB).
  - `enable` (`BOOLEAN`) — включает или выключает патч LRU-кэша.
  - `verbose` (`BOOLEAN`) — печатает отладочные сообщения о работе кэша.
- **Выходы**
  - `STRING` — JSON с флагом `ok`, эффективными настройками и полями `error`/`note` при необходимости.

**EN**

Runtime helper that updates the SSD cache without restarting ComfyUI. Drop it near the workflow start and feed the desired settings.

- **Inputs**
  - `cache_root` (`STRING`, defaults to the current value) — cache directory path. An empty string keeps the previous root.
  - `max_size_gb` (`INT`, ≥ 0) — cache size limit in GiB.
  - `enable` (`BOOLEAN`) — toggles the Arena LRU cache on or off.
  - `verbose` (`BOOLEAN`) — enables verbose console logging.
- **Outputs**
  - `STRING` — JSON object exposing the `ok` flag, effective settings and optional `error`/`note` fields.

### ArenaAutoCacheStats

**RU**

Совместимый с ранними версиями узел, возвращающий агрегированную статистику по одной категории кэша. При выключенном кэше отдаёт заглушку с `ok=false`.

- **Входы**
  - `category` (`STRING`, по умолчанию `"checkpoints"`) — имя каталога внутри кэша.
- **Выходы**
  - `STRING` — JSON с полями `category`, `cache_root`, `enabled`, `items`, `total_bytes`, `total_gb`, `max_size_gb`, `last_op`, `last_path` и дополнительной `note`.

**EN**

Legacy-compatible stats node that keeps the original single-JSON output. When the cache is disabled it emits a stub with `ok=false`.

- **Inputs**
  - `category` (`STRING`, default `"checkpoints"`) — cache category/folder name.
- **Outputs**
  - `STRING` — JSON payload exposing `category`, `cache_root`, `enabled`, `items`, `total_bytes`, `total_gb`, `max_size_gb`, `last_op`, `last_path` and an optional `note`.

### ArenaAutoCacheStatsEx

**RU**

Расширенная версия статистики с отдельными сокетами для числовых значений и счётчиков сессии.

- **Входы**
  - `category` (`STRING`, по умолчанию `"checkpoints"`).
- **Выходы**
  - `STRING` (`json`) — тот же JSON, что и у `ArenaAutoCacheStats`.
  - `INT` (`items`) — количество записей в кэше.
  - `FLOAT` (`total_gb`) — общий объём данных в гигабайтах.
  - `STRING` (`cache_root`) — путь к корню кэша.
  - `INT` (`session_hits`) — количество попаданий за сессию.
  - `INT` (`session_misses`) — количество промахов за сессию.
  - `INT` (`session_trims`) — количество ручных либо автоматических очисток за сессию.

**EN**

Extended statistics with dedicated sockets for numeric values and session counters.

- **Inputs**
  - `category` (`STRING`, default `"checkpoints"`).
- **Outputs**
  - `STRING` (`json`) — same JSON payload as `ArenaAutoCacheStats`.
  - `INT` (`items`) — number of cached entries.
  - `FLOAT` (`total_gb`) — total cache size in GiB.
  - `STRING` (`cache_root`) — resolved cache root path.
  - `INT` (`session_hits`) — cache hits recorded during the session.
  - `INT` (`session_misses`) — cache misses recorded during the session.
  - `INT` (`session_trims`) — manual or automatic trims executed during the session.

### ArenaAutoCacheTrim

**RU**

Запускает ручное обслуживание LRU-кэша для указанной категории. Полезно для освобождения места без изменения конфигурации.

- **Входы**
  - `category` (`STRING`, по умолчанию `"checkpoints"`).
- **Выходы**
  - `STRING` — JSON с полями `ok`, `category`, `trimmed`, `items`, `total_bytes`, `total_gb`, `max_size_gb` и `note` о результате.

**EN**

Triggers manual LRU maintenance for the selected category so you can reclaim space without adjusting the global settings.

- **Inputs**
  - `category` (`STRING`, default `"checkpoints"`).
- **Outputs**
  - `STRING` — JSON containing `ok`, `category`, `trimmed`, `items`, `total_bytes`, `total_gb`, `max_size_gb` and a descriptive `note`.

### ArenaAutoCacheManager

**RU**

Комбинированный узел: применяет конфигурацию, при необходимости запускает `Trim` и возвращает отчёты для дашбордов.

- **Входы**
  - `cache_root` (`STRING`, по умолчанию активное значение).
  - `max_size_gb` (`INT`, ≥ 0).
  - `enable` (`BOOLEAN`).
  - `verbose` (`BOOLEAN`).
  - `category` (`STRING`, по умолчанию `"checkpoints"`).
  - `do_trim` (`BOOLEAN`, по умолчанию `false`) — выполняет очистку сразу после изменения настроек.
- **Выходы**
  - `STRING` (`stats_json`) — тот же JSON, что и у `ArenaAutoCacheStatsEx`.
  - `STRING` (`action_json`) — журнал операции с вложенными объектами `config` и, при `do_trim=true`, `trim`.

**EN**

Convenience combo node that applies configuration changes, optionally runs a trim and returns ready-to-plot JSON blobs.

- **Inputs**
  - `cache_root` (`STRING`, defaults to the active value).
  - `max_size_gb` (`INT`, ≥ 0).
  - `enable` (`BOOLEAN`).
  - `verbose` (`BOOLEAN`).
  - `category` (`STRING`, default `"checkpoints"`).
  - `do_trim` (`BOOLEAN`, default `false`) — triggers trimming right after updating the settings.
- **Outputs**
  - `STRING` (`stats_json`) — same JSON payload as `ArenaAutoCacheStatsEx`.
  - `STRING` (`action_json`) — execution log containing the `config` result and optional `trim` details when enabled.

## Legacy node

### Arena_MakeTilesSegs

**RU**

Инструмент генерации сегментов (SEGS) для тайлового апскейла. Требует установленного Impact Pack: при отсутствии зависимостей узел завершится ошибкой `IMPACT_MISSING_MESSAGE`.

- **Входы**
  - `images` (`IMAGE`) — батч исходных изображений.
  - `width` (`INT`, 64–4096, шаг 8) — ширина тайла.
  - `height` (`INT`, 64–4096, шаг 8) — высота тайла.
  - `crop_factor` (`FLOAT`, 1.0–10.0, шаг 0.01) — коэффициент расширения маски при нарезке.
  - `min_overlap` (`INT`, 0–512, шаг 1) — минимальное перекрытие тайлов.
  - `filter_segs_dilation` (`INT`, −255…255, шаг 1) — дилатация для входных масок фильтрации.
  - `mask_irregularity` (`FLOAT`, 0–1.0, шаг 0.01) — интенсивность случайных неровностей маски.
  - `irregular_mask_mode` (`STRING`, один из `Reuse fast`, `Reuse quality`, `All random fast`, `All random quality`).
  - `filter_in_segs_opt` (`SEGS`, опционально) — маски включения.
  - `filter_out_segs_opt` (`SEGS`, опционально) — маски исключения.
- **Выходы**
  - `SEGS` — кортеж из исходного размера изображения и списка сегментов `SEG`, пригодных для узлов Impact.

**EN**

Tile segmentation helper for Impact Pack workflows. The node raises `IMPACT_MISSING_MESSAGE` if the dependency is not installed.

- **Inputs**
  - `images` (`IMAGE`) — input image batch.
  - `width` (`INT`, 64–4096, step 8) — tile width.
  - `height` (`INT`, 64–4096, step 8) — tile height.
  - `crop_factor` (`FLOAT`, 1.0–10.0, step 0.01) — crop padding multiplier.
  - `min_overlap` (`INT`, 0–512, step 1) — minimum overlap between tiles.
  - `filter_segs_dilation` (`INT`, −255…255, step 1) — dilation applied to filter masks.
  - `mask_irregularity` (`FLOAT`, 0–1.0, step 0.01) — strength of random mask irregularities.
  - `irregular_mask_mode` (`STRING`, one of `Reuse fast`, `Reuse quality`, `All random fast`, `All random quality`).
  - `filter_in_segs_opt` (`SEGS`, optional) — inclusion masks.
  - `filter_out_segs_opt` (`SEGS`, optional) — exclusion masks.
- **Outputs**
  - `SEGS` — tuple containing the original image size and a list of Impact-compatible `SEG` segments.
