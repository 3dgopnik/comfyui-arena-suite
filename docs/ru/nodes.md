---
title: "Узлы"
description: "Описание входов и выходов узлов ComfyUI Arena Suite."
---

[Обзор](index.md) · [Быстрый старт](quickstart.md) · [CLI](cli.md) · [Конфигурация](config.md) · [Диагностика](troubleshooting.md) · **Узлы**

---

# Справочник узлов Arena

Ниже приведены доступные узлы пакета `ComfyUI_Arena`, их назначение и сокеты. Все названия сокетов совпадают с указанными в интерфейсе ComfyUI.

## Веб-оверлей AutoCache

Пакет включает фронтенд-расширение `web/extensions/arena_autocache.js`, которое автоматически подключается в ComfyUI и слушает сокеты `summary_json`/`warmup_json`/`trim_json`.

### Как включить

1. **Установите репозиторий целиком.** При установке через ComfyUI Manager всё содержимое попадает в `custom_nodes/comfyui-arena-suite`. При ручном копировании дополнительно перенесите файлы из `web/extensions/` в `ComfyUI/web/extensions/`.
2. **Перезапустите ComfyUI.** После обновления или копирования файлов перезапустите интерфейс, чтобы расширение `arena_autocache.js` инициализировалось.
3. **Добавьте поддерживаемый узел.** Разместите `ArenaAutoCacheDashboard`, `ArenaAutoCacheOps` или `ArenaAutoCacheAudit` и запустите граф, чтобы получить JSON в соответствующих сокетах.
4. **Проверьте подсветку.** После появления данных заголовок узла, полосы прогресса и подсказки обновятся автоматически.

### UI-индикаторы и подсказки

- **Строка статуса.** Используется значение `summary_json.ui.headline`; до первого ответа отображается подпись «Arena AutoCache».
- **Цветовая схема.** Заголовок окрашивается в зелёный (`ok`), янтарный (`warn`) или красный (`error`). Пока нет данных, сохраняется стандартная палитра ComfyUI.
- **Полосы прогресса.** Отдельные шкалы показывают аудит, прогрев, трим и общий уровень заполненности (`Capacity`), используя счётчики из JSON-ответов.
- **Детали отчёта.** До четырёх строк из `ui.details` отображаются под статусом, поэтому можно оставлять краткие комментарии прямо в отчётах узлов.
- **Предупреждения.** Значок `⚠` появляется при пропущенных моделях, ошибках прогрева, заметках трима или при сбое разбора JSON.

Оверлей работает с `ArenaAutoCacheAudit`, `ArenaAutoCacheDashboard` и `ArenaAutoCacheOps` и не требует дополнительных переключателей.

## AutoCache

### 🅰️ Arena AutoCache: Config (`ArenaAutoCacheConfig`)

Помогает обновлять настройки SSD-кэша прямо во время работы графа.

- **Входы**
  - `cache_root` (`STRING`, по умолчанию текущее значение) — путь к каталогу кэша. Пустая строка сохраняет прежний путь.
  - `max_size_gb` (`INT`, ≥ 0) — лимит размера кэша в гигабайтах (GiB).
  - `enable` (`BOOLEAN`) — включает/выключает патч LRU-кэша.
  - `verbose` (`BOOLEAN`) — печатает отладочные сообщения в консоль.
- **Выходы**
  - `STRING` — JSON с полями `ok`, эффективными настройками и при необходимости `error`/`note`.

### 🅰️ Arena AutoCache: Stats (`ArenaAutoCacheStats`)

Отдаёт агрегированную статистику по выбранной категории кэша; при отключённом кэше возвращает заглушку с `ok=false`.

- **Входы**
  - `category` (`STRING`, по умолчанию `"checkpoints"`) — имя каталога внутри кэша.
- **Выходы**
  - `STRING` — JSON с полями `category`, `cache_root`, `enabled`, `items`, `total_bytes`, `total_gb`, `max_size_gb`, `last_op`, `last_path` и опциональной `note`.

### 🅰️ Arena AutoCache: StatsEx (`ArenaAutoCacheStatsEx`)

Расширенная версия статистики с отдельными сокетами для чисел и счётчиков за сессию.

- **Входы**
  - `category` (`STRING`, по умолчанию `"checkpoints"`).
- **Выходы**
  - `STRING` (`json`) — идентичный JSON-ответу «🅰️ Arena AutoCache: Stats» (`ArenaAutoCacheStats`).
  - `INT` (`items`) — число записей в кэше.
  - `FLOAT` (`total_gb`) — общий размер кэша в гигабайтах.
  - `STRING` (`cache_root`) — активный путь к кэшу.
  - `INT` (`session_hits`) — попадания за текущую сессию.
  - `INT` (`session_misses`) — промахи за текущую сессию.
  - `INT` (`session_trims`) — ручные или автоматические очистки за текущую сессию.

### 🅰️ Arena AutoCache Audit (`ArenaAutoCacheAudit`)

Проверяет, существуют ли исходные модели и есть ли соответствующие файлы в кэше. Поддерживает списки `items` (по строкам или JSON) и извлечение имён из `workflow_json`; учитываются расширения `.safetensors`, `.ckpt`, `.pt`, `.pth`, `.onnx`, `.vae`, `.bin`, `.gguf`, `.yaml`, `.yml`, `.npz`, `.pb`, `.tflite`.

- **Входы**
  - `items` (`STRING`, многострочный) — строки `category:file` либо JSON-массив строк/объектов с ключами `category`, `name`/`filename`.
  - `workflow_json` (`STRING`, многострочный) — опционально: полный JSON сохранённого workflow для авто-добавления моделей.
  - `default_category` (`STRING`, по умолчанию `"checkpoints"`) — категория по умолчанию.
  - `extended_stats` (`BOOLEAN`, опционально) — собирает расширенную статистику по всем обнаруженным категориям и дополняет `summary_json` агрегатами.
  - `apply_settings` (`BOOLEAN`, опционально) — применяет переопределения из `settings_json` перед запуском аудита.
  - `do_trim_now` (`BOOLEAN`, опционально) — запускает LRU-очистку для всех категорий сразу после аудита.
  - `settings_json` (`STRING`, многострочный, опционально) — JSON с полями `cache_root`, `max_size_gb`, `enable`, `verbose`; используется, когда `apply_settings=true`.
- **Выходы**
  - `STRING` (`json`) — отчёт со статусами `cached`, `missing_cache`, `missing_source` и агрегатом `counts`. Полезная нагрузка дополнена блоками `ui` и `timings.duration_seconds` для отображения в дашбордах.
  - `INT` (`total`) — уникальные элементы в отчёте.
  - `INT` (`cached`) — элементы, найденные в кэше.
  - `INT` (`missing`) — отсутствующие элементы (в кэше или на источнике).
  - `STRING` (`summary_json`) — сводка для UI с массивом `actions` (settings/stats/trim), блоками `stats_meta`/`audit_meta`, списком категорий и таймингами операций.

> **Ограничения**: `apply_settings` меняет глобальные настройки кэша, а `do_trim_now` обрабатывает все категории, найденные в `items` и `workflow_json`. При множественных категориях `summary_json` агрегирует статистику и фиксирует результаты очистки в массиве `actions`.

### 🅰️ Arena AutoCache Warmup (`ArenaAutoCacheWarmup`)

Использует ту же спецификацию `items`/`workflow_json`, но прогревает кэш: освобождает место, копирует отсутствующие файлы и обновляет индекс (`_update_index_touch`, `_update_index_meta`).

- **Входы**
  - `items` (`STRING`, многострочный) — перечень моделей (строки или JSON, как в `Audit`).
  - `workflow_json` (`STRING`, многострочный) — опционально: JSON workflow.
  - `default_category` (`STRING`, по умолчанию `"checkpoints"`).
- **Выходы**
  - `STRING` (`json`) — отчёт с поэлементными статусами (`copied`, `cached`, `missing_source`, `error_*`) и суммарными счётчиками `warmed`, `copied`, `missing`, `errors`, `skipped`, а также с блоками `ui` и `timings.duration_seconds`.
  - `INT` (`total`) — количество обработанных записей.
  - `INT` (`warmed`) — элементы, оказавшиеся в кэше.
  - `INT` (`copied`) — количество копий.
  - `INT` (`missing`) — отсутствующие исходники.
  - `INT` (`errors`) — возникшие ошибки.

### 🅰️ Arena AutoCache: Trim (`ArenaAutoCacheTrim`)

Запускает ручное обслуживание LRU-кэша для указанной категории.

- **Входы**
  - `category` (`STRING`, по умолчанию `"checkpoints"`).
- **Выходы**
  - `STRING` — JSON с полями `ok`, `category`, `trimmed`, `items`, `total_bytes`, `total_gb`, `max_size_gb` и пояснительной `note`.

### 🅰️ Arena AutoCache: Manager (`ArenaAutoCacheManager`)

Комбинированный узел, который применяет конфигурацию, может сразу выполнить `Trim` и возвращает два отчёта.

- **Входы**
  - `cache_root` (`STRING`, по умолчанию текущее значение).
  - `max_size_gb` (`INT`, ≥ 0).
  - `enable` (`BOOLEAN`).
  - `verbose` (`BOOLEAN`).
  - `category` (`STRING`, по умолчанию `"checkpoints"`).
  - `do_trim` (`BOOLEAN`, по умолчанию `false`) — инициирует очистку после применения настроек.
- **Выходы**
  - `STRING` (`stats_json`) — JSON со статистикой, совпадающий с «🅰️ Arena AutoCache: StatsEx» (`ArenaAutoCacheStatsEx`).
  - `STRING` (`action_json`) — журнал операции с вложенными объектами `config` и, при активном `do_trim`, `trim`.

### 🅰️ Arena AutoCache: Дашборд (`ArenaAutoCacheDashboard`)

Объединяет статистику, аудит, опциональный трим и применение настроек в одном ответе. Все JSON-выходы обогащены полями `ui` и `timings` для удобного отображения в интерфейсе.

- **Входы**
  - `category` (`STRING`, по умолчанию `"checkpoints"`).
  - `items` (`STRING`, многострочный) — список для аудита.
  - `workflow_json` (`STRING`, многострочный) — опциональный дамп workflow для авто-обнаружения моделей.
  - `default_category` (`STRING`, по умолчанию `"checkpoints"`).
  - `extended_stats` (`BOOLEAN`, по умолчанию `false`) — добавляет подсказки `ui` в `stats_json`.
  - `apply_settings` (`BOOLEAN`, по умолчанию `false`) — применяет переопределения из `settings_json` перед сбором статистики.
  - `do_trim_now` (`BOOLEAN`, по умолчанию `false`) — сразу выполняет очистку и включает результат в сводку.
  - `settings_json` (`STRING`, многострочный) — JSON с полями `cache_root`, `max_size_gb`, `enable`, `verbose`.
- **Выходы**
  - `STRING` (`summary_json`) — объединённая сводка с секциями `config`, `stats`, `audit`, `trim` и картой `timings`.
  - `STRING` (`stats_json`) — статистика (при `extended_stats=true` содержит `ui` и `timings`).
  - `STRING` (`audit_json`) — отчёт аудита с дополнительными полями `ui` и `timings`.

### 🅰️ Arena AutoCache: Операции (`ArenaAutoCacheOps`)

Универсальный узел для автоматизации: умеет выполнять аудит, прогрев, очистку или связку «аудит + прогрев», а также по желанию проводит бенчмарк скорости чтения кэша.

- **Входы**
  - `category` (`STRING`, по умолчанию `"checkpoints"`).
  - `items` (`STRING`, многострочный) — спецификация, общая для аудита и прогрева.
  - `workflow_json` (`STRING`, многострочный) — опциональный дамп workflow для авто-обнаружения моделей.
  - `default_category` (`STRING`, по умолчанию `"checkpoints"`).
  - `mode` (`STRING`, по умолчанию `"audit_then_warmup"`) — варианты `audit`, `warmup`, `audit_then_warmup`, `trim`.
  - `benchmark_samples` (`INT`, по умолчанию `0`) — сколько файлов читать для замера пропускной способности (0 отключает бенчмарк).
  - `benchmark_read_mb` (`FLOAT`, по умолчанию `0.0`) — лимит чтения с одного файла в МиБ.
- **Выходы**
  - `STRING` (`summary_json`) — JSON с собранными `stats`, `warmup`, `trim` и, при наличии, `audit`, а также с картой `timings` (включая `benchmark`, если активен).
  - `STRING` (`warmup_json`) — отчёт о прогреве либо заглушка, если режим его не запускал.
  - `STRING` (`trim_json`) — отчёт о триме либо заглушка при пропуске операции.

## Legacy

### 🅰️ Arena Make Tiles Segments (`Arena_MakeTilesSegs`)

Генерирует сегменты (`SEGS`) для тайлового апскейла в связке с Impact Pack. При отсутствии Impact Pack узел завершится ошибкой `IMPACT_MISSING_MESSAGE`.

- **Входы**
  - `images` (`IMAGE`) — исходные изображения.
  - `width` (`INT`, 64–4096, шаг 8) — ширина тайла.
  - `height` (`INT`, 64–4096, шаг 8) — высота тайла.
  - `crop_factor` (`FLOAT`, 1.0–10.0, шаг 0.01) — коэффициент расширения маски при нарезке.
  - `min_overlap` (`INT`, 0–512, шаг 1) — минимальное перекрытие тайлов.
  - `filter_segs_dilation` (`INT`, −255…255, шаг 1) — дилатация для масок фильтрации.
  - `mask_irregularity` (`FLOAT`, 0–1.0, шаг 0.01) — сила случайных неровностей маски.
  - `irregular_mask_mode` (`STRING`, варианты `Reuse fast`, `Reuse quality`, `All random fast`, `All random quality`).
  - `filter_in_segs_opt` (`SEGS`, опционально) — маски включения.
  - `filter_out_segs_opt` (`SEGS`, опционально) — маски исключения.
- **Выходы**
  - `SEGS` — кортеж из исходного размера изображения и списка сегментов `SEG`, совместимых с узлами Impact.

---

[← Назад: Диагностика](troubleshooting.md) · [К началу ↑](#справочник-узлов-arena)
