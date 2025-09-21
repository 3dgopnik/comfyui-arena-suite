---
title: "Конфигурация"
description: "Переменные окружения и параметры узлов Arena AutoCache."
---

[Обзор](index.md) · [Быстрый старт](quickstart.md) · [CLI](cli.md) · **Конфигурация** · [Диагностика](troubleshooting.md)

---

# Переменные окружения

- `ARENA_CACHE_ROOT` — путь к корню SSD‑кэша. Если не задано:
  - Windows: `%LOCALAPPDATA%\ArenaAutoCache`
  - Linux/macOS: `<корень ComfyUI>/ArenaAutoCache`
- `ARENA_CACHE_ENABLE` — `1`/`0` включить/выключить патч (по умолчанию включён).
- `ARENA_CACHE_MAX_GB` — лимит кэша в GiB (по умолчанию `300`).
- `ARENA_LANG` — принудительный язык узлов (`en`/`ru`). По умолчанию берётся из `COMFYUI_LANG`.

# Узлы AutoCache
- Config — применяет/переопределяет настройки кэша в рантайме.
- Stats / StatsEx — базовая и расширенная статистика кэша.
- Trim — очистка категории или по списку.
- Manager — операции с кэшем и категориями.
- Audit / Warmup — аудит наличия и прогрев кэша по спискам/JSON workflow.

