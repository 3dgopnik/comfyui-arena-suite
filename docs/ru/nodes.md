---
title: "Узлы"
description: "Описание входов и выходов узлов ComfyUI Arena Suite."
---

[Обзор](index.md) · [Быстрый старт](quickstart.md) · [CLI](cli.md) · [Конфигурация](config.md) · [Диагностика](troubleshooting.md) · **Узлы**

---

# Справочник узлов Arena

Ниже приведены доступные узлы пакета `ComfyUI_Arena`, их назначение и сокеты. Все названия сокетов совпадают с указанными в интерфейсе ComfyUI.

## AutoCache

### ArenaAutoCacheConfig

Помогает обновлять настройки SSD-кэша прямо во время работы графа.

- **Входы**
  - `cache_root` (`STRING`, по умолчанию текущее значение) — путь к каталогу кэша. Пустая строка сохраняет прежний путь.
  - `max_size_gb` (`INT`, ≥ 0) — лимит размера кэша в гигабайтах (GiB).
  - `enable` (`BOOLEAN`) — включает/выключает патч LRU-кэша.
  - `verbose` (`BOOLEAN`) — печатает отладочные сообщения в консоль.
- **Выходы**
  - `STRING` — JSON с полями `ok`, эффективными настройками и при необходимости `error`/`note`.

### ArenaAutoCacheStats

Отдаёт агрегированную статистику по выбранной категории кэша; при отключённом кэше возвращает заглушку с `ok=false`.

- **Входы**
  - `category` (`STRING`, по умолчанию `"checkpoints"`) — имя каталога внутри кэша.
- **Выходы**
  - `STRING` — JSON с полями `category`, `cache_root`, `enabled`, `items`, `total_bytes`, `total_gb`, `max_size_gb`, `last_op`, `last_path` и опциональной `note`.

### ArenaAutoCacheStatsEx

Расширенная версия статистики с отдельными сокетами для чисел и счётчиков за сессию.

- **Входы**
  - `category` (`STRING`, по умолчанию `"checkpoints"`).
- **Выходы**
  - `STRING` (`json`) — идентичный JSON-ответу `ArenaAutoCacheStats`.
  - `INT` (`items`) — число записей в кэше.
  - `FLOAT` (`total_gb`) — общий размер кэша в гигабайтах.
  - `STRING` (`cache_root`) — активный путь к кэшу.
  - `INT` (`session_hits`) — попадания за текущую сессию.
  - `INT` (`session_misses`) — промахи за текущую сессию.
  - `INT` (`session_trims`) — ручные или автоматические очистки за текущую сессию.

### ArenaAutoCacheTrim

Запускает ручное обслуживание LRU-кэша для указанной категории.

- **Входы**
  - `category` (`STRING`, по умолчанию `"checkpoints"`).
- **Выходы**
  - `STRING` — JSON с полями `ok`, `category`, `trimmed`, `items`, `total_bytes`, `total_gb`, `max_size_gb` и пояснительной `note`.

### ArenaAutoCacheManager

Комбинированный узел, который применяет конфигурацию, может сразу выполнить `Trim` и возвращает два отчёта.

- **Входы**
  - `cache_root` (`STRING`, по умолчанию текущее значение).
  - `max_size_gb` (`INT`, ≥ 0).
  - `enable` (`BOOLEAN`).
  - `verbose` (`BOOLEAN`).
  - `category` (`STRING`, по умолчанию `"checkpoints"`).
  - `do_trim` (`BOOLEAN`, по умолчанию `false`) — инициирует очистку после применения настроек.
- **Выходы**
  - `STRING` (`stats_json`) — JSON со статистикой, совпадающий с `ArenaAutoCacheStatsEx`.
  - `STRING` (`action_json`) — журнал операции с вложенными объектами `config` и, при активном `do_trim`, `trim`.

## Legacy

### Arena_MakeTilesSegs

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
