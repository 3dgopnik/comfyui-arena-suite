# Улучшения Preload режима в Arena AutoCache

## Обзор

Preload режим был значительно улучшен для работы без сохранения workflow в файлы и неблокирующего копирования моделей.

## Новые возможности

### 1. Fallback для получения workflow

**Проблема**: Preload режим работал только с сохраненными JSON файлами workflow.

**Решение**: Добавлен fallback механизм для получения workflow из:
- **History API** - последний выполненный workflow из истории ComfyUI
- **PromptServer** - активный workflow из сервера ComfyUI
- **sys.modules** - поиск в загруженных модулях ComfyUI

**Использование**:
```python
# Теперь Preload работает даже без сохранения файла
workflow_data = _get_workflow_from_files()
if not workflow_data:
    workflow_data = _get_workflow_from_history_or_server()  # Fallback
```

### 2. Неблокирующее копирование

**Проблема**: Синхронное копирование больших файлов блокировало UI.

**Решение**: Асинхронная система копирования через фоновый поток:
- **Очередь задач** - `_copy_queue` для планирования копирования
- **Фоновый поток** - `_copy_worker()` для выполнения копирования
- **Неблокирующее планирование** - `_schedule_cache_copy()` для постановки задач

**Архитектура**:
```python
# Глобальные переменные
_copy_queue = Queue()
_copy_thread_started = False

# Фоновый воркер
def _copy_worker():
    while True:
        folder_type, filename, source_path = _copy_queue.get()
        # Копирование файла
        _copy_queue.task_done()

# Планирование копирования
def _schedule_cache_copy(folder_type, filename, source_path):
    _ensure_copy_thread()
    _copy_queue.put((folder_type, filename, source_path))
```

## Использование

### OnDemand режим (как раньше)

1. Выберите `cache_mode = "OnDemand"`
2. Запустите граф - модели кешируются при первом обращении
3. Копирование происходит в фоне, не блокируя UI

### Preload режим (улучшенный)

**Вариант А - с сохраненным файлом**:
1. Сохраните workflow в JSON файл
2. Выберите `cache_mode = "Preload"`, `start_preload = True`
3. Модели будут скопированы в фоне

**Вариант Б - без сохранения файла** (новое):
1. Загрузите workflow на канвас
2. Выберите `cache_mode = "Preload"`, `start_preload = True`
3. Система автоматически найдет workflow через fallback методы
4. Модели будут скопированы в фоне

## Результаты

### OnDemand режим
```json
{
  "ok": true,
  "cache_mode": "OnDemand",
  "message": "OnDemand caching enabled - models will be cached on first use",
  "patched": true,
  "min_size_mb": 10.0,
  "description": "Models will be automatically cached when first loaded via patched get_full_path (min size: 10.0 MB)"
}
```

### Preload режим
```json
{
  "ok": true,
  "cache_mode": "Preload",
  "message": "Preload completed: 5 scheduled, 0 cached, 2 skipped, 0 errors",
  "warmup_completed": true,
  "models_found": 7,
  "scheduled": 5,
  "cached": 0,
  "skipped": 2,
  "errors": 0,
  "min_size_mb": 10.0,
  "categories_checked": ["checkpoints", "loras", "vaes"],
  "models": [...],
  "cache_results": [...]
}
```

## Статусы копирования

- **`scheduled`** - файл запланирован для фонового копирования
- **`cached`** - файл уже был в кеше
- **`skipped_small`** - файл слишком мал (меньше `min_size_mb`)
- **`skipped_exists`** - файл уже существует в кеше
- **`error`** - ошибка при копировании
- **`not_found`** - исходный файл не найден

## Преимущества

### Для пользователей
- ✅ **Preload работает без сохранения файлов** - просто загрузите workflow на канвас
- ✅ **Неблокирующее копирование** - UI остается отзывчивым
- ✅ **Фоновое копирование** - можно продолжать работать пока модели копируются
- ✅ **Автоматический fallback** - система сама найдет workflow

### Для разработчиков
- ✅ **Модульная архитектура** - легко расширять fallback методы
- ✅ **Асинхронная обработка** - не блокирует основной поток
- ✅ **Обработка ошибок** - graceful fallback при недоступности API
- ✅ **Логирование** - подробная информация о процессе

## Настройка

### Переменные окружения
```bash
# Минимальный размер файлов для кеширования
ARENA_CACHE_MIN_SIZE_MB=10

# Включить подробное логирование
ARENA_CACHE_VERBOSE=true

# Корневая папка кеша
ARENA_CACHE_ROOT=C:/ComfyUI/cache
```

### Параметры ноды
- **`min_size_mb`** - минимальный размер файлов для кеширования
- **`categories`** - категории моделей для кеширования
- **`force_warmup`** - принудительный прогрев кеша
- **`start_preload`** - запуск предварительного кеширования

## Рекомендации

1. **Для больших моделей** - используйте Preload режим для предварительного копирования
2. **Для мелких файлов** - настройте `min_size_mb` для пропуска мелких LoRA
3. **Для отладки** - включите `ARENA_CACHE_VERBOSE=true` для подробных логов
4. **Для продакшена** - используйте OnDemand для прозрачного кеширования
