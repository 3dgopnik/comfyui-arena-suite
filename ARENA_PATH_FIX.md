# Исправление проблемы с путями моделей Arena AutoCache

## Проблема
Arena AutoCache нода патчит функции ComfyUI (`folder_paths.get_folder_paths` и `folder_paths.get_full_path`), добавляя пути кэша **в начало** списка путей поиска моделей. Это приводит к тому, что ComfyUI сначала ищет модели в кэше Arena, а не в оригинальных путях (включая NAS).

## Решение

### 1. Создан файл `.env` с настройками:
```env
# Arena AutoCache Configuration
# Отключаем автопатч ComfyUI для сохранения оригинальных путей
ARENA_AUTOCACHE_AUTOPATCH=0

# Настройки кэширования
ARENA_CACHE_MODE=ondemand
ARENA_AUTO_CACHE_ENABLED=0
ARENA_CACHE_VERBOSE=1

# Полное отключение патчинга путей ComfyUI
ARENA_DISABLE_PATH_PATCHING=1
```

### 2. Исправлен код Arena AutoCache:
- **Файл**: `autocache/arena_auto_cache_simple.py`
- **Изменение**: Пути кэша теперь добавляются **в конец** списка путей поиска
- **Строка 512**: `original_paths = original_paths + [cache_path]` (вместо `[cache_path] + original_paths`)

### 3. Добавлена опция полного отключения патчинга:
- **Переменная**: `ARENA_DISABLE_PATH_PATCHING=1`
- **Функция**: `_apply_folder_paths_patch()` теперь проверяет эту переменную

## Результат
- ComfyUI теперь сначала ищет модели в оригинальных путях (включая NAS)
- Arena AutoCache работает как дополнительный кэш, не переопределяя основные пути
- Модели с NAS снова доступны в ComfyUI

## Тестирование
1. Перезапустите ComfyUI
2. Проверьте, что модели с NAS снова видны в ComfyUI
3. Arena AutoCache по-прежнему работает, но не мешает основным путям

## Примечания
- Изменения в коде обратно совместимы
- Arena AutoCache продолжает работать в режиме ondemand
- Автопатч отключен для предотвращения конфликтов

