# ComfyUI_Arena

> **TL;DR — AutoCache setup / Быстрый старт по переменным окружения**
> - Default cache root if `ARENA_CACHE_ROOT` is not set:
>   - Windows: `%LOCALAPPDATA%\ArenaAutoCache` (for example, `C:\Users\you\AppData\Local\ArenaAutoCache`)
>   - Linux/macOS: `<ComfyUI root>/ArenaAutoCache`
> - Set `ARENA_CACHE_ROOT=<path>` before launching ComfyUI so the SSD patch writes to your desired location. 🅰️ Arena AutoCache nodes (Config/Stats/Trim/Manager/Dashboard/Ops) will show the active directory. / Установите `ARENA_CACHE_ROOT=<путь>` до запуска ComfyUI, чтобы SSD-кэш писал туда, куда нужно.
> - Restart ComfyUI after changing environment variables. / После изменения переменных окружения перезапустите ComfyUI.
> - Examples:
>   - PowerShell: `$env:ARENA_CACHE_ROOT='D:\ComfyCache'; python main.py`
>   - CMD: `set ARENA_CACHE_ROOT=D:\ComfyCache && python main.py`
>   - bash: `ARENA_CACHE_ROOT=/mnt/ssd/cache python main.py`
> - Optional overrides: `ARENA_CACHE_ENABLE=0` temporarily disables the patch; `ARENA_CACHE_MAX_GB=512` caps the cache size (GiB); `ARENA_CACHE_VERBOSE=1` prints copy/hit logs for benchmarking. / Дополнительно: `ARENA_CACHE_ENABLE=0` отключает патч, `ARENA_CACHE_MAX_GB=512` ограничивает размер (ГиБ), `ARENA_CACHE_VERBOSE=1` включает подробные логи для бенчмарков.

> **📝 Inline note input / Встроенные заметки**
> - RU: В текстовом поле `items` можно оставлять комментарии и пометки (`# комментарий`), которые пропускаются при аудите/прогреве, но помогают объяснить, зачем элемент в списке.
> - EN: Use the multiline `items` field for inline notes (`# comment`). The parsers skip these lines during audit/warmup while keeping the list readable for operators.

Single-package for all **Arena** nodes.

- `legacy/` - migrated from local install.
- `autocache/` - SSD auto-cache.
- `updater/` - model updater (WIP).

> Python bytecode and `__pycache__` are excluded by `.gitignore`.

## Веб-оверлей AutoCache / AutoCache Web Overlay

**RU — Шаги подключения**

1. Убедитесь, что репозиторий установлен целиком: через ComfyUI Manager он попадает в `ComfyUI/custom_nodes/comfyui-arena-suite/`, и фронтенд автоматически ищет расширение в каталоге `web` этого пакета.
2. Перезапустите ComfyUI после установки или обновления, чтобы фронтенд подхватил расширение `arena_autocache.js`.
3. Добавьте на Canvas узел `ArenaAutoCacheDashboard`, `ArenaAutoCacheOps` или `ArenaAutoCacheAudit` и выполните граф, чтобы получить данные в сокетах `summary_json`/`warmup_json`/`trim_json`.
4. Откройте DevTools браузера → **Network** и проверьте, что ресурс `extensions/arena_autocache.js` загружен без ошибок; при проблемах ищите сообщения в консоли ComfyUI или браузера. После появления JSON заголовок и подписи обновятся автоматически: подсветка, полосы прогресса и подсказки станут активными.

**EN — Enablement steps**

1. Ensure the repository is installed as-is: ComfyUI Manager keeps it under `ComfyUI/custom_nodes/comfyui-arena-suite/`, and the front-end automatically looks for the overlay assets inside that package's `web` folder.
2. Restart ComfyUI after installing or updating so the front-end loads the `arena_autocache.js` extension.
3. Drop an `ArenaAutoCacheDashboard`, `ArenaAutoCacheOps`, or `ArenaAutoCacheAudit` node onto the canvas and run the workflow to emit `summary_json` / `warmup_json` / `trim_json` payloads.
4. Open DevTools → **Network** and confirm the `extensions/arena_autocache.js` asset loads without errors; if something fails, check the ComfyUI or browser consoles. Once the node outputs JSON, the overlay refreshes automatically with header highlights, progress bars, and inline hints.

**Интерфейс и подсказки / UI cues and hints**

- RU: Строка статуса берётся из `summary_json.ui.headline`; до первого ответа отображается заглушка «Arena AutoCache».
  EN: The status headline comes from `summary_json.ui.headline`; before the first update it falls back to “Arena AutoCache”.
- RU: Цвет заголовка показывает серьёзность (`ok` → зелёный, `warn` → янтарный, `error` → красный); при отсутствии данных сохраняются цвета ComfyUI.
  EN: Header colors match the severity (`ok` → green, `warn` → amber, `error` → red); while idle the default ComfyUI palette is preserved.
- RU: Полосы прогресса отображают аудит, прогрев, трим и заполненность кэша (`Capacity`), используя счётчики из JSON.
  EN: Progress bars surface audit, warmup, trim, and overall cache usage (`Capacity`) based on the reported counters.
- RU: Блок `ui.details` выводится списком до четырёх строк, позволяя оставить краткие комментарии в отчёте.
  EN: Up to four lines from `ui.details` are rendered, making it easy to surface inline notes from the report.
- RU: Предупреждения `⚠` появляются при пропущенных моделях, ошибках прогрева, заметках трима и ошибках парсинга JSON.
  EN: `⚠` warnings show up for missing models, warmup errors, trim notes, and JSON parsing issues.

## Совместимость AutoCache / AutoCache Compatibility

| Старый узел / Legacy node | Новый режим / New mode | Примечание / Notes |
| --- | --- | --- |
| 🅰️ Arena AutoCache: Config (`ArenaAutoCacheConfig`) | Без изменений; связывайте вывод с Dashboard/Ops как блок `config` | Используйте для настройки кэша во время сессии. / Tweak runtime cache settings. |
| 🅰️ Arena AutoCache: Stats (`ArenaAutoCacheStats`) | 🅰️ Dashboard → `stats_json` | Dashboard добавляет статусную строку и метаданные. / Dashboard augments raw stats with status/meta fields. |
| 🅰️ Arena AutoCache: StatsEx (`ArenaAutoCacheStatsEx`) | 🅰️ Dashboard → `summary_json` | Числовые сокеты остаются в StatsEx; `summary_json` дублирует показатели для UI. / StatsEx sockets stay while `summary_json` mirrors totals for UI overlays. |
| 🅰️ Arena AutoCache Audit (`ArenaAutoCacheAudit`) | 🅰️ Dashboard → `audit_json` + `summary_json` | Добавлены `summary_json`, `extended_stats`, `apply_settings`, `do_trim_now`; подтверждение действий в UI. / Now mirrors dashboard feedback with `summary_json`, `extended_stats`, `apply_settings`, `do_trim_now`. |
| 🅰️ Arena AutoCache Warmup (`ArenaAutoCacheWarmup`) | 🅰️ Ops → `do_warmup=true` | Включите warmup в Ops для сценария `audit_then_warmup`. / Toggle warmup in Ops for an `audit_then_warmup` flow. |
| 🅰️ Arena AutoCache: Trim (`ArenaAutoCacheTrim`) | 🅰️ Ops → `do_trim=true` | Позволяет запускать очистку вместе с прогревом. / Run trims alongside warmups. |
| 🅰️ Arena AutoCache: Manager (`ArenaAutoCacheManager`) | 🅰️ Ops / 🅰️ Dashboard | Manager остаётся для совместимости; новые узлы дают сводки и управление. / Manager stays compatible, Dashboard/Ops surface summaries. |

> **RU:** Старые графы продолжают работать как есть; новые дашборды добавляют `summary_json` без изменения сокетов. / **EN:** Existing workflows keep working; the dashboards add `summary_json` without breaking sockets.

## Dashboard и Ops / Dashboard and Ops

### 🅰️ Arena AutoCache: Dashboard (`ArenaAutoCacheDashboard`)

**RU**

Наблюдатель объединяет статистику и аудит в одной панели. Выход `summary_json` содержит статусную строку (`ok`, `timestamp`) и блоки `stats_meta`/`audit_meta`, которые удобно подавать в текстовые виджеты, графики или API. Узел принимает те же поля `items` и `workflow_json`, что и Audit, поддерживает комментарии `#` и извлекает модели из сохранённых workflow.

- **Входы**
  - `category` (`STRING`, по умолчанию `"checkpoints"`).
  - `items` (`STRING`, многострочный) — списки/JSON с комментариями.
  - `workflow_json` (`STRING`, многострочный) — экспорт **Queue → Save (API Format)**.
  - `default_category` (`STRING`, по умолчанию `"checkpoints"`).
- **Выходы**
  - `STRING` (`summary_json`) — сводка для UI.
  - `STRING` (`stats_json`) — расширенная статистика (как у Stats/StatsEx).
  - `STRING` (`audit_json`) — подробный отчёт аудита.

**EN**

The dashboard node fuses stats and audit into one observability surface. Its `summary_json` output exposes the status line (`ok`, `timestamp`) and the `stats_meta`/`audit_meta` blocks ready for text widgets, charts, or external APIs. Inputs mirror the Audit node: multiline `items` (with `#` comments) and optional `workflow_json` dumps.

- **Inputs**
  - `category` (`STRING`, default `"checkpoints"`).
  - `items` (`STRING`, multiline) — list/JSON spec with inline comments.
  - `workflow_json` (`STRING`, multiline) — export from **Queue → Save (API Format)**.
  - `default_category` (`STRING`, default `"checkpoints"`).
- **Outputs**
  - `STRING` (`summary_json`) — UI-friendly summary payload.
  - `STRING` (`stats_json`) — extended stats JSON (same as Stats/StatsEx).
  - `STRING` (`audit_json`) — detailed audit report.

**Пример статусной строки / Example status line**

```json
{
  "ok": true,
  "timestamp": 1712345678.123,
  "stats_meta": {
    "items": 42,
    "total_gb": 118.7,
    "cache_root": "D:/ComfyCache",
    "session": {"hits": 128, "misses": 3, "trims": 1}
  },
  "audit_meta": {"total": 10, "cached": 8, "missing": 2},
  "stats": {"note": "cache disabled"}
}
```

### 🅰️ Arena AutoCache: Ops (`ArenaAutoCacheOps`)

**RU**

Операционный узел объединяет прогрев (`Warmup`) и очистку (`Trim`). Выберите режим `audit_then_warmup`, чтобы выполнить аудит и затем прогреть кэш — это рекомендуемый сценарий. Режим `audit` запускает только аудит, `warmup` — только прогрев, а `trim` — только очистку. `summary_json` отражает блоки `warmup_meta` и `trim` для UI.

- **Входы**
  - `category` (`STRING`, по умолчанию `"checkpoints"`).
  - `items` (`STRING`, многострочный) — общая спецификация Audit/Warmup.
  - `workflow_json` (`STRING`, многострочный) — автодобавление моделей из workflow.
  - `default_category` (`STRING`, по умолчанию `"checkpoints"`).
  - `mode` (`STRING`, по умолчанию `"audit_then_warmup"`) — варианты: `audit_then_warmup`, `audit`, `warmup`, `trim`.
- **Выходы**
  - `STRING` (`summary_json`) — объединённая сводка статуса и операций.
  - `STRING` (`warmup_json`) — отчёт прогрева.
  - `STRING` (`trim_json`) — отчёт очистки.

**EN**

The Ops node coordinates warmups and trims. Pick the `audit_then_warmup` mode to run an audit followed by a warmup — this is the recommended workflow. Use `audit` for audit-only passes, `warmup` when you just need to fill the cache, and `trim` for cleanup-only operations. The resulting `summary_json` adds `warmup_meta` and `trim` blocks for dashboards.

- **Inputs**
  - `category` (`STRING`, default `"checkpoints"`).
  - `items` (`STRING`, multiline) — same spec as Audit/Warmup.
  - `workflow_json` (`STRING`, multiline) — adds workflow-discovered models.
  - `default_category` (`STRING`, default `"checkpoints"`).
  - `mode` (`STRING`, default `"audit_then_warmup"`) — choices: `audit_then_warmup`, `audit`, `warmup`, `trim`.
- **Outputs**
  - `STRING` (`summary_json`) — consolidated status + operations report.
  - `STRING` (`warmup_json`) — warmup report payload.
  - `STRING` (`trim_json`) — trim report payload.

**Вариант `audit_then_warmup` / `audit_then_warmup` recipe**

1. Подайте один и тот же список `items` в Dashboard и Ops. / Feed the same `items` list into both Dashboard and Ops.
2. Оцените `audit_meta.missing` в `summary_json` Dashboard. / Inspect `audit_meta.missing` in the Dashboard summary.
3. Переключите `mode` в `audit_then_warmup` (и выберите `trim`, если нужна только очистка). / Switch `mode` to `audit_then_warmup` (pick `trim` when you only need cleanup).
4. Передайте `warmup_json` и `trim_json` в текстовые виджеты или логгеры. / Pipe `warmup_json` and `trim_json` to text widgets or loggers.

**Бенчмаркинг / Benchmarking tips**

- RU: Включите `ARENA_CACHE_VERBOSE=1`, чтобы видеть HIT/COPY в консоли и замерять длительность. Используйте `stats_meta.session.hits/misses` для расчёта hit-rate и `warmup_meta.copied` для оценки пропускной способности.
- EN: Enable `ARENA_CACHE_VERBOSE=1` to log HIT/COPY events for timing. Consume `stats_meta.session.hits/misses` to compute hit rate and `warmup_meta.copied` to gauge throughput.

## AutoCache nodes

### 🅰️ Arena AutoCache: Config (`ArenaAutoCacheConfig`)

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

### 🅰️ Arena AutoCache: Stats (`ArenaAutoCacheStats`)

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

### 🅰️ Arena AutoCache: StatsEx (`ArenaAutoCacheStatsEx`)

**RU**

Расширенная версия статистики с отдельными сокетами для числовых значений и счётчиков сессии.

- **Входы**
  - `category` (`STRING`, по умолчанию `"checkpoints"`).
- **Выходы**
  - `STRING` (`json`) — тот же JSON, что и у «🅰️ Arena AutoCache: Stats» (`ArenaAutoCacheStats`).
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
  - `STRING` (`json`) — same JSON payload as **🅰️ Arena AutoCache: Stats** (`ArenaAutoCacheStats`).
  - `INT` (`items`) — number of cached entries.
  - `FLOAT` (`total_gb`) — total cache size in GiB.
  - `STRING` (`cache_root`) — resolved cache root path.
  - `INT` (`session_hits`) — cache hits recorded during the session.
  - `INT` (`session_misses`) — cache misses recorded during the session.
  - `INT` (`session_trims`) — manual or automatic trims executed during the session.

### 🅰️ Arena AutoCache Audit (`ArenaAutoCacheAudit`)

**RU**

Пробегает по списку моделей, проверяет наличие исходных файлов и актуальность копий в кэше. Узел принимает перечень `items` (текст построчно или JSON-массив строк/объектов вида `{"category": "loras", "name": "model.safetensors"}`) и, при необходимости, выгрузку графа `workflow_json`. Из workflow извлекаются строки с расширениями моделей (`.safetensors`, `.ckpt`, `.pt`, `.pth`, `.onnx`, `.vae`, `.bin`, `.gguf`, `.yaml`, `.yml`, `.npz`, `.pb`, `.tflite`).

- **Входы**
  - `items` (`STRING`, многострочный) — перечень путей вида `category:file.safetensors` или JSON-список. Комментарии начинающиеся с `#` игнорируются.
  - `workflow_json` (`STRING`, многострочный) — опционально: сырой JSON сохранённого workflow для автоматического извлечения моделей.
  - `default_category` (`STRING`, по умолчанию `"checkpoints"`) — категория для элементов без префикса.
  - `extended_stats` (`BOOLEAN`, опционально) — собирает расширенную статистику по всем обнаруженным категориям и добавляет агрегаты в `summary_json`.
  - `apply_settings` (`BOOLEAN`, опционально) — применяет переопределения из `settings_json` до запуска аудита.
  - `do_trim_now` (`BOOLEAN`, опционально) — запускает LRU-очистку для всех затронутых категорий сразу после аудита.
  - `settings_json` (`STRING`, многострочный, опционально) — JSON с полями `cache_root`, `max_size_gb`, `enable`, `verbose`; используется, когда `apply_settings=true`.
- **Выходы**
  - `STRING` (`json`) — подробный отчёт с полями `items[]`, статусами (`cached`, `missing_cache`, `missing_source`) и сводкой `counts`.
  - `INT` (`total`) — количество уникальных записей в отчёте.
  - `INT` (`cached`) — число элементов, присутствующих в кэше.
  - `INT` (`missing`) — число элементов без кэша или без исходника.
  - `STRING` (`summary_json`) — сводка для UI: содержит массив `actions` (settings/stats/trim), блоки `stats_meta`/`audit_meta`, список категорий и тайминги выполненных операций.

> **Ограничения**: `apply_settings` меняет глобальные параметры кэша, а `do_trim_now` запускает очистку для всех категорий, найденных в `items`/`workflow_json`. При множестве категорий `summary_json` агрегирует статистику по каждой и фиксирует результаты очисток в массиве `actions`.
- **Примеры**
  - Многострочный список c комментариями:

    ```text
    # checkpoints по умолчанию
    anything-v4.5-pruned.ckpt
    loras:korean-style.safetensors
    checkpoints:refiner.safetensors
    ```

  - JSON-массив (поддерживает строки и объекты):

    ```json
    [
      "loras:paper-cut.safetensors",
      {
        "category": "checkpoints",
        "name": "base-model.safetensors",
        "source": "/mnt/models/base-model.safetensors"
      }
    ]
    ```

  - Использование `workflow_json`: экспортируйте граф через **Queue → Save (API Format)**, загрузите файл с помощью стандартного `Load Text` и подключите его выход к `workflow_json`, чтобы узел автоматически добавил модели из workflow.

**EN**

Traverses the provided item list, verifies that source files exist and the cache copy is up to date. The `items` field accepts newline-delimited strings (e.g. `loras:model.safetensors`) or a JSON array of strings/objects such as `{"category": "loras", "name": "model.safetensors"}`. When `workflow_json` is supplied, the node parses the ComfyUI workflow dump and extracts filenames with model extensions (`.safetensors`, `.ckpt`, `.pt`, `.pth`, `.onnx`, `.vae`, `.bin`, `.gguf`, `.yaml`, `.yml`, `.npz`, `.pb`, `.tflite`).

- **Inputs**
  - `items` (`STRING`, multiline) — list of `category:file` entries or a JSON array. Lines beginning with `#` are ignored.
  - `workflow_json` (`STRING`, multiline, optional) — raw workflow JSON for automatic model discovery.
  - `default_category` (`STRING`, default `"checkpoints"`) — fallback cache category when the spec omits a prefix.
  - `extended_stats` (`BOOLEAN`, optional) — collects extended stats for every discovered category and adds aggregates to `summary_json`.
  - `apply_settings` (`BOOLEAN`, optional) — applies overrides from `settings_json` before the audit run.
  - `do_trim_now` (`BOOLEAN`, optional) — triggers an immediate LRU trim for each affected category after the audit completes.
  - `settings_json` (`STRING`, multiline, optional) — JSON with `cache_root`, `max_size_gb`, `enable`, `verbose` overrides used when `apply_settings=true`.
- **Outputs**
  - `STRING` (`json`) — detailed report with `items[]`, status fields (`cached`, `missing_cache`, `missing_source`) and a `counts` summary.
  - `INT` (`total`) — number of unique entries covered by the audit.
  - `INT` (`cached`) — entries already cached.
  - `INT` (`missing`) — entries missing from cache or sources.
  - `STRING` (`summary_json`) — UI-friendly summary that lists executed `actions` (settings/stats/trim), exposes `stats_meta`/`audit_meta`, the processed categories, and operation timings.

> **Limitations**: `apply_settings` mutates the global cache configuration, and `do_trim_now` trims every category discovered via `items`/`workflow_json`. When multiple categories are involved, `summary_json` aggregates their stats and records trim results inside the `actions` array.
- **Examples**
  - Multiline list with inline comments:

    ```text
    # default checkpoints category
    anything-v4.5-pruned.ckpt
    loras:korean-style.safetensors
    checkpoints:refiner.safetensors
    ```

  - JSON payload (mixing strings and objects):

    ```json
    [
      "loras:paper-cut.safetensors",
      {
        "category": "checkpoints",
        "name": "base-model.safetensors",
        "source": "/mnt/models/base-model.safetensors"
      }
    ]
    ```

  - `workflow_json` hookup: export the graph via **Queue → Save (API Format)**, load the file with the built-in `Load Text` node and feed its output into `workflow_json` so the audit adds every model referenced in the workflow automatically.

### 🅰️ Arena AutoCache Warmup (`ArenaAutoCacheWarmup`)

**RU**

Использует ту же спецификацию `items`/`workflow_json`, но создаёт или обновляет файлы в SSD-кэше. Перед копированием узел гарантирует наличие свободного места (`_lru_ensure_room`) и отмечает результаты в индексе (`_update_index_touch`/`_update_index_meta`).

- **Входы**
  - `items` (`STRING`, многострочный) — перечень моделей для прогрева (строки или JSON-список, как в `Audit`).
  - `workflow_json` (`STRING`, многострочный) — опциональный дамп workflow для автодобавления моделей.
  - `default_category` (`STRING`, по умолчанию `"checkpoints"`).
- **Выходы**
  - `STRING` (`json`) — отчёт с итоговым статусом каждого файла (`copied`, `cached`, `missing_source`, `error_*`) и агрегированными счётчиками `warmed`, `copied`, `missing`, `errors`, `skipped`.
  - `INT` (`total`) — количество обработанных элементов.
  - `INT` (`warmed`) — число элементов, оказавшихся в кэше после выполнения.
  - `INT` (`copied`) — сколько файлов пришлось копировать заново.
  - `INT` (`missing`) — сколько записей не удалось подготовить из-за отсутствующих исходников.
  - `INT` (`errors`) — количество ошибок (например, нехватка места или сбой копирования).
- **Примеры**
  - Формат `items` полностью совпадает с `Audit`, поэтому можно переиспользовать список или JSON из предыдущего примера.
  - Чтобы прогреть модели из текущего графа, подключите тот же `Load Text` с экспортированным workflow к `workflow_json` и, при необходимости, добавьте вручную элементы, которых нет в workflow.

**EN**

Warms up the cache using the same `items`/`workflow_json` specification. For every discovered model the node ensures there is enough room via `_lru_ensure_room`, copies missing files and updates the index via `_update_index_touch`/`_update_index_meta`.

- **Inputs**
  - `items` (`STRING`, multiline) — warmup target list (strings or JSON array, identical to `Audit`).
  - `workflow_json` (`STRING`, multiline, optional) — workflow dump for automatic model discovery.
  - `default_category` (`STRING`, default `"checkpoints"`).
- **Outputs**
  - `STRING` (`json`) — execution report with per-item status (`copied`, `cached`, `missing_source`, `error_*`) and aggregate counters `warmed`, `copied`, `missing`, `errors`, `skipped`.
  - `INT` (`total`) — number of processed entries.
  - `INT` (`warmed`) — entries ending up in the cache.
  - `INT` (`copied`) — files copied during the warmup.
  - `INT` (`missing`) — entries skipped because the source file is missing.
  - `INT` (`errors`) — number of failures (lack of space, copy errors, etc.).
- **Examples**
  - The `items` format mirrors the audit node, so you can reuse the multiline list or JSON payload shown above.
  - To warm up every model referenced in the current workflow, feed the exported JSON (via `Load Text` or any text loader) into `workflow_json` and optionally append manual entries for assets that live outside the workflow.

### 🅰️ Arena AutoCache: Trim (`ArenaAutoCacheTrim`)

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

### 🅰️ Arena AutoCache: Manager (`ArenaAutoCacheManager`)

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
  - `STRING` (`stats_json`) — тот же JSON, что и у «🅰️ Arena AutoCache: StatsEx» (`ArenaAutoCacheStatsEx`).
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
  - `STRING` (`stats_json`) — same JSON payload as **🅰️ Arena AutoCache: StatsEx** (`ArenaAutoCacheStatsEx`).
  - `STRING` (`action_json`) — execution log containing the `config` result and optional `trim` details when enabled.

## Legacy node

### 🅰️ Arena Make Tiles Segments (`Arena_MakeTilesSegs`)

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
