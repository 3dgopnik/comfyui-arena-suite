---
title: "Быстрый старт"
description: "Как установить и начать работать с ComfyUI Arena Suite."
---

[Обзор](index.md) · **Быстрый старт** · [Arena AutoCache Base](arena_autocache_base.md) · [Узлы](nodes.md) · [Диагностика](troubleshooting.md)

---

# Быстрый старт

Выполните шаги ниже, чтобы установить пакет и проверить работу Arena AutoCache Base.

## 1. Подготовка окружения
- Убедитесь, что установлен Python 3.10+ и ComfyUI (ветка `master`).
- При использовании кеширования задайте переменные окружения (опционально):
  - Пример (PowerShell):
    ```powershell
    $env:ARENA_CACHE_MIN_SIZE_MB='10'
    python main.py
    ```

## 2. Установка через ComfyUI Manager (рекомендуется)
1. Откройте ComfyUI и вкладку Manager → Install from URL.
2. Вставьте URL репозитория: `https://github.com/3dgopnik/comfyui-arena-suite`.
3. Нажмите Install, затем выполните Refresh custom nodes или перезапустите ComfyUI.

## 3. Ручная установка
1. Клонируйте репозиторий: `git clone https://github.com/3dgopnik/comfyui-arena-suite`.
2. Переместите папку `comfyui-arena-suite` в `ComfyUI/custom_nodes/`.
3. Перезапустите ComfyUI.

## 4. Проверка установки
- В Canvas добавьте узел из группы `🅰️ Arena/AutoCache`:
  - **🅰️ Arena AutoCache Base** — базовая нода для кеширования моделей
  - **🅰️ Arena Make Tiles Segments** — legacy узел для сегментации

---

[← Обзор](index.md) · [Далее: Arena AutoCache Base →](arena_autocache_base.md)

