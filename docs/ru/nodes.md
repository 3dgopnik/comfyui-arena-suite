---
title: "Узлы"
description: "Справка по узлам ComfyUI Arena Suite."
---

[Обзор](index.md) · [Быстрый старт](quickstart.md) · [CLI](cli.md) · [Конфигурация](config.md) · [Диагностика](troubleshooting.md) · **Узлы**

---

# Узлы Arena AutoCache

Разделение по группам в ComfyUI:

## Basic
- ArenaAutoCache Analyze — автоанализ текущего воркфлоу, план копирования и автопрогрев без ввода.
- ArenaAutoCache Ops — сводный узел: аудит + прогрев (+trim при выборе режима).

## Advanced
- ArenaAutoCache Dashboard — сводка и действия (настройки, аудит, trim) в одном месте.
- ArenaAutoCache Manager — быстрые изменения настроек и (опц.) trim.
- ArenaAutoCache Trim — принудительная очистка категории по LRU.
- ArenaAutoCache StatsEx — расширенная статистика с отдельными выходами.

## Utils
- ArenaGetActiveWorkflow — возвращает текущий активный воркфлоу (JSON) из PromptServer.
- ArenaAutoCache Stats — базовая статистика по кэшу (JSON).

Примечание: точный состав узлов и выводы зависят от текущей версии. Подсказки по входам/выходам смотрите в интерфейсе ComfyUI или по всплывающим подсказкам.

## Workflow allowlist

Узлы Audit/Warmup/Ops перед запуском обновляют allowlist моделей на основе входов `items` и `workflow_json`. Если вход `workflow_json` пуст, узлы пытаются считать активный граф через `server.PromptServer` и продолжают работать с текущей схемой. Только перечисленные пары категория/файл попадают в LRU-копирование; прямые вызовы `folder_paths.get_full_path` без регистрации возвращают исходные пути без прогрева.

Fallback: если парсер ничего не нашёл в воркфлоу, используются последние сведения из статистики категории (`last_path`) — это позволяет прогреть последнюю использованную модель без ручных вводов.

## Уведомления о копировании

- `_copy_into_cache_lru` всегда отправляет события `copy_started`, `copy_completed` и `copy_skipped` в консоль (`[ArenaAutoCache] ...`) и, при наличии `PromptServer.instance`, синхронно ретранслирует их в канал `arena/autocache/copy_event`. События фиксируются даже при `ARENA_CACHE_VERBOSE=0`.
- В контексте ошибок отправляется событие `copy_failed` с текстом исключения, чтобы оверлей получил сигнал о проблеме.
- Узлы ArenaAutoCache Warmup и ArenaAutoCache Ops получили необязательный вход `log_context` (строка). Передайте текст или JSON с `node_id`, тегом пользователя и т.п. Строка автоматически оборачивается в `{"text": "..."}`.
- Warmup автоматически добавляет в контекст поле `node="ArenaAutoCacheWarmup"`, а Ops — `node="ArenaAutoCacheOps"` и `mode=<текущий режим>`. Итоговый контекст попадает во все события копирования, что позволяет ComfyUI overlay сопоставить прогрев с конкретным узлом и его выполнением.

