---
title: "Конфигурация"
description: "Подробное руководство по настройке ComfyUI Arena Suite"
order: 4
---

# Конфигурация

Подробное руководство по настройке всех параметров ComfyUI Arena Suite.

## ⚙️ Основные настройки

### Переменные окружения

Создайте файл `.env` в директории ComfyUI для глобальных настроек:

```env
# Основные настройки кеширования
ARENA_CACHE_DIR=C:/ComfyUI/cache
ARENA_LOG_LEVEL=INFO
ARENA_AUTO_CACHE_ENABLED=true

# Настройки кеша
ARENA_CACHE_MIN_SIZE_MB=100
ARENA_CACHE_MAX_GB=50
ARENA_CACHE_MODE=ondemand

# Автопатч
ARENA_AUTOCACHE_AUTOPATCH=true
```

### Настройки ноды

Все параметры ноды можно настроить как через интерфейс, так и через переменные окружения.

## 🎯 Параметры кеширования

### enable_caching

**Описание:** Основной переключатель кеширования

**Тип:** BOOLEAN  
**По умолчанию:** `False`  
**Переменная окружения:** `ARENA_AUTO_CACHE_ENABLED`

```python
# Включение кеширования
enable_caching = True

# Отключение кеширования
enable_caching = False
```

### cache_dir

**Описание:** Директория для хранения кешированных моделей

**Тип:** STRING  
**По умолчанию:** `C:/ComfyUI/cache`  
**Переменная окружения:** `ARENA_CACHE_DIR`

```python
# Windows
cache_dir = "C:/ComfyUI/cache"

# Linux/macOS
cache_dir = "/home/user/.cache/comfyui/arena"

# Сетевое хранилище
cache_dir = "//nas/models/cache"
```

### cache_categories

**Описание:** Категории моделей для кеширования

**Тип:** STRING  
**По умолчанию:** `checkpoints,loras,vae`  
**Переменная окружения:** `ARENA_CACHE_CATEGORIES`

```python
# Основные категории
cache_categories = "checkpoints,loras,vae"

# Все категории
cache_categories = "checkpoints,loras,vae,clip,controlnet,upscale_models,embeddings,hypernetworks,gguf_models,unet_models,diffusion_models"

# Только большие модели
cache_categories = "checkpoints,loras"
```

### min_size_mb

**Описание:** Минимальный размер файла для кеширования

**Тип:** FLOAT  
**По умолчанию:** `100.0`  
**Переменная окружения:** `ARENA_CACHE_MIN_SIZE_MB`

```python
# Кешировать только большие файлы (>500MB)
min_size_mb = 500.0

# Кешировать все файлы
min_size_mb = 0.0

# Кешировать файлы больше 50MB
min_size_mb = 50.0
```

### max_cache_gb

**Описание:** Максимальный размер кеша

**Тип:** FLOAT  
**По умолчанию:** `0.0` (без лимита)  
**Переменная окружения:** `ARENA_CACHE_MAX_GB`

```python
# Без лимита
max_cache_gb = 0.0

# Лимит 50GB
max_cache_gb = 50.0

# Лимит 100GB
max_cache_gb = 100.0
```

## 🔄 Режимы кеширования

### cache_mode

**Описание:** Режим работы кеширования

**Тип:** COMBO  
**По умолчанию:** `ondemand`  
**Переменная окружения:** `ARENA_CACHE_MODE`

#### OnDemand (по умолчанию)

```python
cache_mode = "ondemand"
```

**Характеристики:**
- Кеширование только при первом обращении
- Экономит место на диске
- Рекомендуется для большинства случаев

#### Eager

```python
cache_mode = "eager"
```

**Характеристики:**
- Массовое копирование всех моделей при загрузке
- Все модели готовы к использованию
- Требует больше места на диске

#### Disabled

```python
cache_mode = "disabled"
```

**Характеристики:**
- Полное отключение кеширования
- Использование оригинальных путей
- Для отладки и тестирования

## 🧹 Автоочистка

### auto_cleanup

**Описание:** Автоматическая очистка старых файлов

**Тип:** BOOLEAN  
**По умолчанию:** `False`

```python
# Включить автоочистку
auto_cleanup = True

# Отключить автоочистку
auto_cleanup = False
```

### Стратегии очистки

1. **LRU (Least Recently Used)** - удаление самых старых файлов
2. **По размеру** - удаление самых больших файлов
3. **По дате** - удаление файлов старше определенного возраста

## 📊 Логирование

### log_level

**Описание:** Уровень детализации логов

**Тип:** COMBO  
**По умолчанию:** `INFO`  
**Переменная окружения:** `ARENA_LOG_LEVEL`

```python
# Минимальное логирование
log_level = "ERROR"

# Стандартное логирование
log_level = "INFO"

# Подробное логирование
log_level = "DEBUG"
```

### Уровни логирования

| Уровень | Описание | Использование |
|---------|----------|---------------|
| `ERROR` | Только ошибки | Продакшн |
| `WARNING` | Предупреждения и ошибки | Отладка |
| `INFO` | Основные операции | Рекомендуется |
| `DEBUG` | Детальная диагностика | Разработка |

## 🔧 Расширенные настройки

### Автопатч

**Переменная окружения:** `ARENA_AUTOCACHE_AUTOPATCH`

```env
# Включить автопатч при загрузке
ARENA_AUTOCACHE_AUTOPATCH=true

# Отключить автопатч
ARENA_AUTOCACHE_AUTOPATCH=false
```

### Безопасность

#### Проверка путей

```python
# Безопасные пути
cache_dir = "C:/ComfyUI/cache"           # ✅ Безопасно
cache_dir = "/home/user/.cache/arena"   # ✅ Безопасно

# Небезопасные пути
cache_dir = "C:/"                        # ❌ Корень диска
cache_dir = "/"                          # ❌ Корень системы
cache_dir = "//server/share"             # ❌ Слишком мелкий UNC путь
```

#### Валидация настроек

Все настройки проходят валидацию:

- **Проверка типов** - корректность типов данных
- **Проверка диапазонов** - значения в допустимых пределах
- **Проверка путей** - безопасность файловых путей

## 📁 Настройка путей к моделям

### extra_model_paths.yaml

Arena AutoCache поддерживает работу с дополнительными путями к моделям через файл `extra_model_paths.yaml`.

**Расположение файла:**
- ComfyUI Desktop: `C:\Users\<username>\AppData\Local\Programs\@comfyorgcomfyui-electron\resources\ComfyUI\extra_model_paths.yaml`
- Локальная установка: `C:\ComfyUI\extra_model_paths.yaml`

**Настройка через Arena:**

1. **Автоматическая настройка (рекомендуется):**
   - Используйте Settings UI → Arena → заполните "NAS Root Path" и "Cache Directory"
   - Нажмите "Save Settings" - Arena создаст `.env` файл с настройками
   - Включите "Auto-scan NAS" для автоматического обнаружения моделей

2. **Ручная настройка через YAML:**
   - Скопируйте свой `extra_model_paths.yaml` в `<ComfyUI-Arena>/config/extra_model_paths.yaml`
   - Arena будет использовать этот файл как шаблон
   - Кнопка "Restore YAML" в Settings восстановит файл в ComfyUI из шаблона

**Пример extra_model_paths.yaml:**

```yaml
# Путь к моделям на NAS
models:
  checkpoints: Y:\SDModels\CheckPoints\
  loras: Y:\SDModels\Lora\
  vae: Y:\SDModels\VAE\
  upscale_models: Y:\SDModels\SDXL\SUPIR\
  clip: Y:\SDModels\CLIP\
  controlnet: Y:\SDModels\ControlNet\
```

**Важно:**
- Arena автоматически сканирует подпапки (до 3 уровней по умолчанию)
- Можно настроить глубину сканирования через "NAS Scan Max Depth" в Settings
- Модели определяются по размеру (по умолчанию >= 1MB), не зависит от расширений файлов

## 📁 Структура конфигурации

### Файл .env

```env
# Основные настройки
ARENA_CACHE_DIR=C:/ComfyUI/cache
ARENA_LOG_LEVEL=INFO
ARENA_AUTO_CACHE_ENABLED=true

# Настройки кеша
ARENA_CACHE_MIN_SIZE_MB=100
ARENA_CACHE_MAX_GB=50
ARENA_CACHE_MODE=ondemand

# Автопатч
ARENA_AUTOCACHE_AUTOPATCH=true

# Категории моделей
ARENA_CACHE_CATEGORIES=checkpoints,loras,vae,clip,controlnet
```

### Приоритет настроек

1. **Параметры ноды** - высший приоритет
2. **Переменные окружения** - средний приоритет
3. **Значения по умолчанию** - низший приоритет

## 🚀 Оптимизация производительности

### Рекомендации по настройке

1. **SSD для кеша** - используйте быстрые диски
2. **Достаточное место** - оставьте 20-30% свободного места
3. **Фильтрация по размеру** - настройте `min_size_mb`
4. **Лимит кеша** - установите разумный `max_cache_gb`

### Мониторинг

```python
# Включите подробное логирование для мониторинга
log_level = "DEBUG"

# Настройте автоочистку для управления размером
auto_cleanup = True
max_cache_gb = 50.0
```

## 🔍 Диагностика

### Проверка конфигурации

```python
# Проверьте все настройки
print(f"Cache directory: {cache_dir}")
print(f"Cache categories: {cache_categories}")
print(f"Min size: {min_size_mb} MB")
print(f"Max cache: {max_cache_gb} GB")
print(f"Cache mode: {cache_mode}")
```

### Логи для диагностики

```bash
# Windows
tail -f "C:\Users\username\AppData\Roaming\ComfyUI\logs\comfyui.log"

# Linux/macOS
tail -f ~/.local/share/ComfyUI/logs/comfyui.log
```

## 📚 Дополнительные ресурсы

- [Быстрый старт](quickstart.md) - начальная настройка
- [Руководство по нодам](nodes.md) - описание нод
- [Руководство пользователя](manual.md) - полное руководство
- [Устранение неполадок](troubleshooting.md) - решение проблем

---

**Правильная конфигурация - залог эффективной работы Arena AutoCache!**