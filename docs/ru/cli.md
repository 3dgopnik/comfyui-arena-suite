---
title: "CLI"
description: "Командные утилиты для обслуживания кэша и моделей."
---

[Обзор](index.md) · [Быстрый старт](quickstart.md) · **CLI** · [Конфигурация](config.md) · [Диагностика](troubleshooting.md)

---

# CLI и вспомогательные скрипты

В каталоге `scripts/` есть утилиты для обновления моделей (HF/CivitAI), бенчмарка диска и инициализации кэша.

## Подсказка по каждому скрипту
```bash
python scripts/arena_updater_hf.py --help
python scripts/arena_updater_civitai.py --help
python scripts/arena_benchmark_disk.py --help
```

## Быстрые сценарии
- Настроить корень кэша (Windows CMD):
  ```cmd
  call scripts/arena_set_cache.bat D:\ComfyCache 1 1
  ```
- Bootstrap‑скрипты для Windows: `scripts/arena_bootstrap_cache.bat` / PowerShell: `scripts/arena_bootstrap_cache.ps1`.

---

[← Быстрый старт](quickstart.md) · [Далее: Конфигурация →](config.md)

