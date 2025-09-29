---
title: "Конфигурация"
description: "Переменные окружения и параметры узлов Arena AutoCache."
---

[Обзор](index.md) · [Быстрый старт](quickstart.md) · [CLI](cli.md) · **Конфигурация** · [Диагностика](troubleshooting.md)

---

# Конфигурация Arena AutoCache

Arena AutoCache поддерживает два способа конфигурации:

## 1. Файл настроек `.env`

Основной способ конфигурации - через файл `user/arena_autocache.env` в корне ComfyUI:

```bash
# Arena AutoCache Environment Settings
# Generated automatically - do not edit manually

# Основные настройки кэша
ARENA_CACHE_ROOT=f:\ComfyUIModelCache\
ARENA_CACHE_MIN_SIZE_MB=10.0
ARENA_CACHE_MAX_GB=512.0
ARENA_CACHE_VERBOSE=1

# Категории моделей для кэширования
ARENA_CACHE_CATEGORIES=Checkpoint,LoRA
ARENA_CACHE_CATEGORIES_MODE=extend

# Управление функциональностью
ARENA_AUTO_CACHE_ENABLED=1
ARENA_AUTOCACHE_AUTOPATCH=1
```

### Параметры .env файла

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `ARENA_CACHE_ROOT` | Путь к корню SSD-кэша | `<ComfyUI>/user/ComfyUI-Cache` |
| `ARENA_CACHE_MIN_SIZE_MB` | Минимальный размер файла для кэширования (MB) | `10.0` |
| `ARENA_CACHE_MAX_GB` | Максимальный размер кэша (GB), `0` = без лимита | `0.0` |
| `ARENA_CACHE_VERBOSE` | Подробное логирование (`1`/`0`) | `0` |
| `ARENA_CACHE_CATEGORIES` | Дополнительные категории для кэширования через запятую | `checkpoints,loras,clip,vae,controlnet,upscale_models,embeddings,hypernetworks` (предустановлено) |
| `ARENA_CACHE_CATEGORIES_MODE` | Режим категорий: `extend` (дополнить) или `override` (заменить) | `extend` |
| `ARENA_AUTO_CACHE_ENABLED` | Включить автоматическое кэширование (`1`/`0`) | `0` (безопасность) |
| `ARENA_AUTOCACHE_AUTOPATCH` | Автоматический патч при старте ComfyUI (`1`/`0`) | `0` |

## 2. Логика категорий

### Предустановленные категории
По умолчанию Arena AutoCache включает следующие категории моделей:
- `checkpoints` - основные модели (CheckpointLoaderSimple, CheckpointLoader, Load Diffusion Model)
- `loras` - LoRA модели
- `clip` - CLIP модели (Load CLIP)
- `vae` - VAE модели
- `controlnet` - ControlNet модели
- `upscale_models` - модели апскейлинга
- `embeddings` - Embeddings
- `hypernetworks` - Hypernetworks
- `gguf_models` - GGUF модели (CLIPLoader GGUF, Unet loader GGUF)
- `unet_models` - UNet модели (UNETLoader, отдельные UNet компоненты)
- `diffusion_models` - Diffusion модели (Load Diffusion Model)

### Логика взаимодействия
1. **Если в ноде указаны категории** → автоматически сохраняются в .env файл
2. **Если .env пустой** → используются предустановленные категории
3. **Если .env содержит категории** → используются они (приоритет .env)
4. **Режим "extend"** → .env категории добавляются к предустановленным
5. **Режим "override"** → .env категории заменяют предустановленные

## 3. Переменные окружения

Альтернативный способ - через системные переменные окружения:

- `ARENA_CACHE_ROOT` — путь к корню SSD‑кэша. Если не задано:
  - Windows: `%LOCALAPPDATA%\ArenaAutoCache`
  - Linux/macOS: `<корень ComfyUI>/ArenaAutoCache`
- `ARENA_CACHE_ENABLE` — `1`/`0` включить/выключить патч (по умолчанию включён).
- `ARENA_CACHE_MAX_GB` — лимит кэша в GiB (по умолчанию `300`).

## Приоритет настроек

Настройки применяются в следующем порядке приоритета:

1. **Параметры ноды** (если переданы явно)
2. **Файл `.env`** (если параметр ноды не указан или равен значению по умолчанию)
3. **Значения по умолчанию**

### Мгновенная загрузка настроек

**Новое поведение (v4.2.8+):** Настройки из .env файла загружаются **мгновенно** при создании ноды на канвасе, без необходимости запуска Run в ComfyUI.

Это означает, что:
- При добавлении ноды Arena на канвас → настройки из .env файла загружаются сразу
- Видите ваши сохраненные настройки в интерфейсе ноды мгновенно
- Критично для тяжелых workflow с большими моделями (20+ GB)
- Не нужно ждать запуска Run для применения настроек

### Логика приоритетов

- Если в ноде параметр равен значению по умолчанию, используется значение из .env файла
- Если в ноде параметр отличается от значения по умолчанию, используется значение из ноды
- Это позволяет использовать .env для базовых настроек и переопределять их через ноду при необходимости

### Примеры работы приоритетов

**Сценарий 1: Использование .env файла**
- В ноде: `min_size_mb=10.0` (значение по умолчанию)
- В .env: `ARENA_CACHE_MIN_SIZE_MB=25.0`
- **Результат**: используется `25.0` из .env файла

**Сценарий 2: Переопределение через ноду**
- В ноде: `min_size_mb=50.0` (явно указано)
- В .env: `ARENA_CACHE_MIN_SIZE_MB=25.0`
- **Результат**: используется `50.0` из ноды

## Примеры использования

### Создание .env файла

1. Создайте файл `user/arena_autocache.env` в корне ComfyUI
2. Добавьте нужные настройки:

```bash
# Пример для SSD-кэша на диске F:
ARENA_CACHE_ROOT=f:\ComfyUIModelCache\
ARENA_CACHE_MIN_SIZE_MB=50.0
ARENA_CACHE_MAX_GB=256.0
ARENA_CACHE_VERBOSE=1
ARENA_CACHE_CATEGORIES=checkpoints,loras,vae
ARENA_CACHE_CATEGORIES_MODE=extend
ARENA_AUTO_CACHE_ENABLED=1
```

### Автоматическое сохранение настроек

При использовании ноды с параметром `persist_env=True`, настройки автоматически сохраняются в .env файл:

```python
# В ноде ComfyUI
node.run(
    cache_root="f:\\MyCache",
    min_size_mb=25.0,
    persist_env=True  # Сохранит настройки в .env
)
```

### Валидация настроек

Система автоматически валидирует настройки из .env файла:
- Проверяет корректность числовых значений
- Предупреждает о неизвестных ключах
- Игнорирует некорректные значения с предупреждением

### Отладка конфигурации

Включите подробное логирование для отладки:

```bash
ARENA_CACHE_VERBOSE=1
```

Это покажет:
- Какие настройки загружены из .env
- Приоритеты применения настроек
- Предупреждения о валидации

# Узлы AutoCache
- Названия, подсказки и сокеты на английском.
- Группы в списке нод:
  - Basic: `Analyze`, `Ops` — рекомендуемые для повседневной работы (zero‑input: пустой `workflow_json` → активный граф).
  - Advanced: `Dashboard`, `Manager`, `Trim`, `StatsEx` — расширенные действия и сводки.
  - Utils: `GetActiveWorkflow`, `Stats` — утилиты.
- Особенности:
  - Узлы `Ops/Analyze` автоматически читают активный воркфлоу при пустом `workflow_json`.
  - Если парсер не нашёл элементы, применяется fallback: берётся `last_path` из статистики категории и готовится прогрев последней использованной модели.

