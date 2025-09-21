---
title: "Диагностика"
description: "Типовые проблемы и способы решения для Arena Suite."
---

[Обзор](index.md) · [Быстрый старт](quickstart.md) · [CLI](cli.md) · [Конфигурация](config.md) · **Диагностика**

---

# Частые проблемы

## Веб‑оверлей не грузится
- Проверьте, что файл `web/extensions/arena_autocache.js` существует.
- В DevTools (вкладка Network) убедитесь, что браузер получил этот файл без 404.
- В консоли ComfyUI/браузера проверьте ошибки.

## Переменные окружения не применяются
- Убедитесь, что переменные (`ARENA_CACHE_ROOT`, и т.п.) выставлены перед запуском ComfyUI.
- На Windows PowerShell: `$env:ARENA_CACHE_ROOT='D:\ComfyCache'; python main.py`.
- Перезапустите ComfyUI после изменений.

## Узлы не появились
- Выполните Refresh custom nodes или перезапустите ComfyUI.
- Проверьте, что папка `custom_nodes/comfyui-arena-suite` расположена корректно.

## Кэш не на SSD
- Посмотрите текущий путь в узле `ArenaAutoCacheConfig/Stats`.
- Измените `ARENA_CACHE_ROOT` и перезапустите ComfyUI.

