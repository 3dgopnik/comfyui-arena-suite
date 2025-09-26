# 🅰️ Arena AutoCache Base

## Описание

Базовая нода Arena AutoCache с OnDemand режимом кеширования моделей. Модели кешируются автоматически при первом обращении через патч folder_paths, обеспечивая прозрачное кеширование без анализа workflow.

**Базовая нода готова для модификации и расширения функциональности.**

## Основные возможности

### 🎯 OnDemand кеширование
- **Прозрачное кеширование**: Модели кешируются автоматически при первом обращении
- **Патч folder_paths**: Перехватывает загрузку моделей через ComfyUI API
- **Неблокирующее копирование**: Фоновая очередь для копирования файлов
- **Автоматическое определение**: Не требует анализа workflow

### ⚙️ Настройки
- **Категории моделей**: Выбор типов моделей для кеширования (checkpoints, loras, vaes, etc.)
- **Минимальный размер**: Фильтр по размеру файлов (min_size_mb)
- **Переменные окружения**: Настройка через ARENA_CACHE_MIN_SIZE_MB

### 🎯 Производительность
- **Предварительное копирование**: Модели копируются до начала генерации
- **Избежание задержек**: Предотвращает задержки при загрузке с NAS
- **Прозрачность**: Процесс прогрева максимально прозрачен для пользователя

## Использование

### Базовая настройка

1. **Добавьте ноду Arena AutoCache Base** на ваш canvas
2. **Настройте параметры** (опционально):
   - `categories`: Список категорий моделей для кэширования
   - `min_size_mb`: Минимальный размер файлов для кеширования

### Параметры ноды

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `categories` | STRING | `"checkpoints,loras,vaes,upscale_models,controlnet"` | Категории моделей для кэширования (через запятую) |
| `min_size_mb` | FLOAT | `10.0` | Минимальный размер файлов для кеширования (MB) |

### Поддерживаемые типы нод

#### Checkpoint модели
- `CheckpointLoaderSimple`
- `CheckpointLoader`
- `UNETLoader`

#### VAE модели
- `VAELoader`
- `VAEDecode`
- `VAEEncode`

#### LoRA модели
- `LoraLoader`

#### ControlNet модели
- `ControlNetLoader`
- `ControlNetApply`

#### Upscale модели
- `UpscaleModelLoader`
- `ImageUpscaleWithModel`

#### Дополнительные типы
- `CLIPLoader` - CLIP модели
- `HypernetworkLoader` - Hypernetworks
- `IPAdapterLoader` - IP-Adapter модели
- `GLIGENLoader` - GLIGEN модели
- `AnimateDiffLoader` - AnimateDiff модели
- `InsightFaceLoader` - InsightFace модели
- `FaceRestoreWithModel` - Face restoration модели
- `StyleModelLoader` - Style модели
- `T2IAdapterLoader` - T2I-Adapter модели

## Логика работы

### 1. Первый запуск
```
[ArenaAutoCache] OnDemand caching enabled - models will be cached on first use
[ArenaAutoCache] Applied folder_paths patch
[ArenaAutoCache] Cache miss: model_name.safetensors
[ArenaAutoCache] Scheduled cache copy: model_name.safetensors
[ArenaAutoCache] Caching: model_name.safetensors
```

### 2. Повторный запуск
```
[ArenaAutoCache] Cache hit: model_name.safetensors (already cached)
```

## Настройка переменных окружения

```bash
# Основные настройки кэша
ARENA_CACHE_ROOT=C:/ComfyUI/cache
ARENA_CACHE_MAX_GB=300
ARENA_CACHE_ENABLE=true
ARENA_CACHE_VERBOSE=false

# Настройки фильтрации
ARENA_CACHE_MIN_SIZE_MB=10.0
```

## Результат работы

Нода возвращает JSON с детальной информацией о процессе кэширования:

```json
{
  "ok": true,
  "cache_mode": "OnDemand",
  "message": "OnDemand caching enabled - models will be cached on first use",
  "patched": true,
  "min_size_mb": 10.0,
  "categories": ["checkpoints", "loras", "vaes"],
  "description": "Models will be automatically cached when first loaded via patched get_full_path (min size: 10.0 MB)"
}
```

## Расширяемость

### Добавление новых типов моделей

Для добавления поддержки нового типа модели:

1. **Добавьте в `MODEL_NODE_TYPES`**:
```python
"NewModelLoader": ["model_field_name"]
```

2. **Добавьте в `CATEGORY_MAPPING`**:
```python
"NewModelLoader": "new_category"
```

3. **Обновите документацию** с новым типом модели

### Настройка категорий

Можно легко изменить список категорий для кэширования:

```python
# Только checkpoint и VAE модели
categories = "checkpoints,vaes"

# Все модели
categories = ""  # Пустая строка = все найденные модели
```

## Устранение неполадок

### Проблема: "No models found in current workflow"
**Решение**: Убедитесь, что на canvas есть ноды загрузки моделей (CheckpointLoader, VAELoader и т.д.)

### Проблема: "Source file not found"
**Решение**: Проверьте, что модели находятся в правильных папках ComfyUI

### Проблема: Медленное копирование
**Решение**: Убедитесь, что NAS и SSD имеют хорошую производительность. Используйте `ARENA_CACHE_VERBOSE=true` для диагностики

## Производительность

- **Асинхронное копирование**: Не блокирует основной поток
- **Проверка существования**: Избегает повторного копирования
- **Фильтрация по размеру**: Пропускает маленькие файлы
- **Умное определение путей**: Автоматически находит модели в папках ComfyUI

## Готовность к модификации

Базовая нода Arena AutoCache Base готова для:
- Добавления новых режимов кеширования
- Расширения функциональности
- Создания специализированных версий
- Интеграции с другими системами
