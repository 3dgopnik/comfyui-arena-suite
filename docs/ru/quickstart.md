---
title: "Быстрый старт"
description: "Как установить и начать работать с ComfyUI Arena Suite."
---

[Обзор](index.md) · **Быстрый старт** · [CLI](cli.md) · [Конфигурация](config.md) · [Диагностика](troubleshooting.md)

---

# Быстрый старт

Выполните шаги ниже, чтобы установить пакет и проверить работу узлов Arena.

## 1. Подготовка окружения
- Убедитесь, что установлен Python 3.10+ и ComfyUI (ветка `master`).
- При использовании SSD‑кэша задайте переменные окружения (подробнее в разделе Конфигурация):
  - Пример (PowerShell):
    ```powershell
    $env:ARENA_CACHE_ROOT='D:\ComfyCache'
    python main.py
    ```

## 2. Установка через ComfyUI Manager (рекомендуется)
1. Откройте ComfyUI и вкладку Manager → Install from URL.
2. Вставьте URL репозитория: `https://github.com/3dgopnik/comfyui-arena-suite`.
3. Нажмите Install, затем выполните Refresh custom nodes или перезапустите ComfyUI.

## 3. Ручная установка
1. Клонируйте репозиторий рядом с ComfyUI: `git clone https://github.com/<your-org>/comfyui-arena-suite`.
2. Переместите папку `comfyui-arena-suite` в `ComfyUI/custom_nodes/`.
3. Перезапустите ComfyUI.

## 4. Проверка установки
- В Canvas добавьте узел из группы `Arena/AutoCache/Basic`:
  - для регулярной работы — `ArenaAutoCache Ops` (по умолчанию режим `audit_then_warmup`),
  - для предварительной оценки — `ArenaAutoCache Analyze` и подключите его `Summary JSON` к `Show Any`.

---

[← Обзор](index.md) · [Далее: CLI →](cli.md)

