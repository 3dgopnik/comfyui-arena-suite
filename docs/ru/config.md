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

# Узлы AutoCache
- Названия, подсказки и сокеты на английском.
- Группы в списке нод:
  - Basic: `Analyze`, `Ops` — рекомендуемые для повседневной работы (zero‑input: пустой `workflow_json` → активный граф).
  - Advanced: `Dashboard`, `Manager`, `Trim`, `StatsEx` — расширенные действия и сводки.
  - Utils: `GetActiveWorkflow`, `Stats` — утилиты.
- Особенности:
  - Узлы `Ops/Analyze` автоматически читают активный воркфлоу при пустом `workflow_json`.
  - Если парсер не нашёл элементы, применяется fallback: берётся `last_path` из статистики категории и готовится прогрев последней использованной модели.

