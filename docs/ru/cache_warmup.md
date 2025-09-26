# Arena AutoCache v3.3.0-optimized - OnDemand кеширование моделей

## Описание

Упрощенная версия Arena AutoCache с только OnDemand режимом кеширования. Модели кешируются автоматически при первом обращении через патч folder_paths, обеспечивая прозрачное кеширование без анализа workflow.

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

1. **Добавьте ноду Arena AutoCache** на ваш canvas
2. **Настройте параметры** (опционально):
   - `categories`: Список категорий моделей для кэширования
   - `force_warmup`: Принудительный прогрев (игнорирует состояние сессии)

### Параметры ноды

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `categories` | STRING | `"checkpoints,loras,vaes,upscale_models,controlnet"` | Категории моделей для кэширования (через запятую) |
| `force_warmup` | BOOLEAN | `False` | Принудительный прогрев кэша |

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
[ArenaAutoCache] Starting automatic model detection and caching
[ArenaAutoCache] Analyzing current workflow for all models...
[ArenaAutoCache] Found workflow data, analyzing for models...
[ArenaAutoCache] Workflow analysis found X models
[ArenaAutoCache] Starting cache warmup for X models
[ArenaAutoCache] 🔄 Caching: model_name.safetensors (1024.0 MB)
[ArenaAutoCache] ✅ Cached: model_name.safetensors
```

### 2. Повторный запуск
```
[ArenaAutoCache] Cache warmup already completed in this session
```

### 3. Принудительный прогрев
```
[ArenaAutoCache] Force warmup requested, resetting session state
[ArenaAutoCache] Starting cache warmup for X models
```

## Настройка переменных окружения

```bash
# Основные настройки кэша
ARENA_CACHE_ROOT=C:/ComfyUI/cache
ARENA_CACHE_MAX_GB=300
ARENA_CACHE_ENABLE=true
ARENA_CACHE_VERBOSE=false

# Настройки фильтрации
ARENA_CACHE_MIN_SIZE_GB=1.0
ARENA_CACHE_MIN_SIZE_MB=1024.0
ARENA_CACHE_SKIP_HARDCODED=true
```

## Результат работы

Нода возвращает JSON с детальной информацией о процессе кэширования:

```json
{
  "ok": true,
  "message": "Successfully processed 5 models",
  "warmup_completed": true,
  "models_found": 5,
  "cached": 3,
  "skipped": 2,
  "errors": 0,
  "categories_checked": ["checkpoints", "loras", "vaes"],
  "models": [...],
  "cache_results": [...]
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
