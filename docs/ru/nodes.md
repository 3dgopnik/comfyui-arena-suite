---
title: "Узлы"
description: "Справка по узлам ComfyUI Arena Suite."
---

[Обзор](index.md) · [Быстрый старт](quickstart.md) · [CLI](cli.md) · [Конфигурация](config.md) · [Диагностика](troubleshooting.md) · **Узлы**

---

# Узлы Arena AutoCache

- ArenaAutoCacheConfig — настройка кэша в рантайме.
- ArenaAutoCacheStats — базовая статистика по кэшу.
- ArenaAutoCacheStatsEx — расширенная статистика.
- ArenaAutoCacheTrim — очистка кэша по категории.
- ArenaAutoCacheManager — операции с категориями и путями.
- ArenaAutoCache Audit — аудит наличия моделей.
- ArenaAutoCache Warmup — прогрев кэша по спискам/JSON.

Примечание: точный состав узлов и выводы зависят от текущей версии. Подсказки по входам/выходам смотрите в интерфейсе ComfyUI или по всплывающим подсказкам.

## Workflow allowlist

Узлы Audit/Warmup/Ops перед запуском обновляют allowlist моделей на основе входов `items` и `workflow_json`. Если вход `workflow_json` пуст, узлы пытаются считать активный граф через `server.PromptServer` и продолжают работать с текущей схемой. Только перечисленные пары категория/файл попадают в LRU-копирование; прямые вызовы `folder_paths.get_full_path` без регистрации возвращают исходные пути без прогрева.

