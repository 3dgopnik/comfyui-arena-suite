---
title: "Обзор"
description: "Введение в ComfyUI Arena Suite и ключевые возможности пакета."
---

**Обзор** · [Быстрый старт](quickstart.md) · [CLI](cli.md) · [Конфигурация](config.md) · [Диагностика](troubleshooting.md) · [Узлы](nodes.md)

---

# ComfyUI Arena Suite

> **TL;DR — быстрый старт AutoCache**
> - Значение по умолчанию, если `ARENA_CACHE_ROOT` не задан:
>   - Windows: `%LOCALAPPDATA%\ArenaAutoCache` (например, `C:\Users\you\AppData\Local\ArenaAutoCache`)
>   - Linux/macOS: `<корень ComfyUI>/ArenaAutoCache`
> - Установите `ARENA_CACHE_ROOT=<path>` перед запуском ComfyUI, чтобы направить кэш на SSD. Узлы 🅰️ Arena AutoCache (Config/Stats/Trim/Manager) покажут активную директорию.
> - После изменения переменных окружения перезапустите ComfyUI.
> - Примеры:
>   - PowerShell: `$env:ARENA_CACHE_ROOT='D:\ComfyCache'; python main.py`
>   - CMD: `set ARENA_CACHE_ROOT=D:\ComfyCache && python main.py`
>   - bash: `ARENA_CACHE_ROOT=/mnt/ssd/cache python main.py`
> - Дополнительно: `ARENA_CACHE_ENABLE=0` временно отключает патч; `ARENA_CACHE_MAX_GB=512` ограничивает размер кэша (в ГиБ).

ComfyUI Arena Suite объединяет набор пользовательских узлов и вспомогательных инструментов для ComfyUI под единым пространством имён `ComfyUI_Arena`. Пакет поставляется в виде одной директории и обеспечивает единообразное развёртывание.

Подробные описания узлов см. в разделе [«Узлы»](nodes.md).

## Что входит в пакет
- **Legacy** — перенесённые узлы с сохранением исходной функциональности и интерфейсов.
- **AutoCache** — патчер для `folder_paths`, перенаправляющий загрузки на SSD-кэш до обращения к исходному хранилищу.
- **Updater** — вспомогательные скрипты для обновления моделей и ведения симлинков `current` под управлением ComfyUI.

## Архитектура
- Единый пакет `ComfyUI_Arena` экспортирует все узлы, поэтому ComfyUI обнаруживает их без дополнительных настроек.
- Подсистема AutoCache внедряется в рантайм ComfyUI. При выключении переменной окружения `ARENA_CACHE_ENABLE=0` патч не активируется, но узлы «🅰️ Arena AutoCache: Stats» (`ArenaAutoCacheStats`) и «🅰️ Arena AutoCache: Trim» (`ArenaAutoCacheTrim`) загружаются и возвращают заглушки, сигнализируя об отключении кэша.
- Компоненты Updater и AutoCache спроектированы модульно: незаполненные (WIP) элементы можно дорабатывать независимо от остального пакета.

## Совместимость
- **ComfyUI**: актуальные версии с поддержкой кастомных узлов (проверено на ветке `master`).
- **Python**: интерпретатор 3.10 или новее (см. `pyproject.toml`).
- **Системные требования**: SSD для ускорения AutoCache, права на создание симлинков/джанкшенов для блоков Updater.

## Следующие шаги
1. Перейдите в раздел [«Быстрый старт»](quickstart.md), чтобы установить пакет через ComfyUI Manager или вручную.
2. Ознакомьтесь с [настройкой окружения](config.md), чтобы активировать SSD-кэш и подготовить манифест обновлений.
3. Используйте [подсказки CLI](cli.md) для автоматизации обновлений моделей.
4. При возникновении ошибок обратитесь к разделу [«Диагностика»](troubleshooting.md).

---

[Далее: Быстрый старт →](quickstart.md)
