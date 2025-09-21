---
title: "Обзор"
description: "Краткий обзор ComfyUI Arena Suite и навигация по документации."
---

Обзор · [Быстрый старт](quickstart.md) · [CLI](cli.md) · [Конфигурация](config.md) · [Диагностика](troubleshooting.md) · [Узлы](nodes.md)

---

# ComfyUI Arena Suite

> TL;DR — AutoCache
> - По умолчанию (`ARENA_CACHE_ROOT` не задан):
>   - Windows: `%LOCALAPPDATA%\ArenaAutoCache`
>   - Linux/macOS: `<корень ComfyUI>/ArenaAutoCache`
> - Установите `ARENA_CACHE_ROOT=<путь>` перед запуском ComfyUI.
> - Перезапустите ComfyUI после изменения переменных окружения.
> - Переопределения: `ARENA_CACHE_ENABLE=0`, `ARENA_CACHE_MAX_GB=512`.

Arena Suite объединяет: узлы‑наследие (legacy), SSD‑кэширование (AutoCache) и заготовки для обновления моделей (Updater).

## Возможности
- Legacy — сохранение интерфейсов, расположение: `ComfyUI_Arena/legacy`.
- AutoCache — SSD‑кэш + узлы Config/StatsEx/Trim/Manager.
- Updater — помощники для HF/CivitAI (WIP).

## Требования
- ComfyUI (актуальный master)
- Python 3.10+
- SSD для лучшей производительности AutoCache

---

[Далее: Быстрый старт →](quickstart.md)

