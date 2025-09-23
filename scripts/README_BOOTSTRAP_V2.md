# Arena AutoCache Bootstrap v2.0

Модернизированные скрипты для настройки Arena AutoCache с поддержкой профилей Debug/Prod и расширенными возможностями.

## Файлы

- `arena_bootstrap_cache_v2.bat` - Windows Batch скрипт
- `arena_bootstrap_cache_v2.ps1` - PowerShell GUI скрипт

## Режимы работы

### Debug Mode (--debug)
**Для диагностики и тестирования:**
- `ARENA_CACHE_SKIP_HARDCODED=0` - отключен фильтр hardcoded paths
- `ARENA_CACHE_MIN_SIZE_GB=0.0` - убран порог размера
- `ARENA_CACHE_VERBOSE=1` - подробные логи
- `ARENA_CACHE_ENABLE=1` - включен кеш

### Production Mode (--prod)
**Для повседневной работы:**
- `ARENA_CACHE_SKIP_HARDCODED=0` - NAS пути не скипаются
- `ARENA_CACHE_MIN_SIZE_GB=1.0` - порог размера 1GB
- `ARENA_CACHE_VERBOSE=0` - обычные логи
- `ARENA_CACHE_ENABLE=1` - включен кеш

### Default Mode (--restore-defaults)
**Безопасные настройки по умолчанию:**
- `ARENA_CACHE_SKIP_HARDCODED=1` - включен фильтр hardcoded paths
- `ARENA_CACHE_MIN_SIZE_GB=1.0` - порог размера 1GB
- `ARENA_CACHE_VERBOSE=0` - обычные логи
- `ARENA_CACHE_ENABLE=1` - включен кеш

## Использование

### Windows Batch (arena_bootstrap_cache_v2.bat)

```cmd
# Debug режим (рекомендуется для тестирования)
arena_bootstrap_cache_v2.bat --debug

# Production режим
arena_bootstrap_cache_v2.bat --prod

# Возврат к дефолтным настройкам
arena_bootstrap_cache_v2.bat --restore-defaults

# Интерактивный режим
arena_bootstrap_cache_v2.bat

# Справка
arena_bootstrap_cache_v2.bat --help
```

### PowerShell GUI (arena_bootstrap_cache_v2.ps1)

```powershell
# Debug режим
.\arena_bootstrap_cache_v2.ps1 -Debug

# Production режим
.\arena_bootstrap_cache_v2.ps1 -Prod

# Возврат к дефолтным настройкам
.\arena_bootstrap_cache_v2.ps1 -RestoreDefaults

# Интерактивный режим
.\arena_bootstrap_cache_v2.ps1

# Справка
.\arena_bootstrap_cache_v2.ps1 -Help
```

## Новые возможности

### 1. Проверка окружения
- **NAS доступность**: автоматическая проверка доступности `nas-3d`
- **Права на кеш**: проверка прав записи в папку кеша
- **Создание папок**: автоматическое создание папки кеша при необходимости

### 2. Расширенные настройки
- **Verbose logs**: включение/выключение подробных логов
- **Skip hardcoded paths**: фильтр для NAS и других путей
- **Min size filter**: минимальный размер файлов для кеширования

### 3. Быстрые подсказки
После применения настроек показываются подсказки:
- Как решить проблему "copy_skipped (hardcoded path detected)"
- Как тестировать кеш через Smart/OPS узлы
- Где смотреть прогресс и логи

### 4. Визуальная индикация
- Цветовая индикация режимов (Debug=оранжевый, Prod=зеленый, Default=синий)
- Статус применения настроек
- Проверка доступности NAS и прав

## Переменные окружения

Скрипты устанавливают следующие переменные:

```cmd
ARENA_CACHE_ROOT=C:\Path\To\Cache
ARENA_CACHE_MAX_GB=100
ARENA_CACHE_ENABLE=1
ARENA_CACHE_VERBOSE=0
ARENA_CACHE_MIN_SIZE_GB=1.0
ARENA_CACHE_SKIP_HARDCODED=0
```

## Решение проблем

### Проблема: "copy_skipped (hardcoded path detected)"
**Решение:**
1. Запустите скрипт в Debug режиме: `arena_bootstrap_cache_v2.bat --debug`
2. Или установите `ARENA_CACHE_SKIP_HARDCODED=0`
3. Перезапустите ComfyUI

### Проблема: Модели не кешируются из-за размера
**Решение:**
1. В Debug режиме `ARENA_CACHE_MIN_SIZE_GB=0.0` (убирает фильтр)
2. В Production режиме можно настроить нужный порог

### Проблема: NAS недоступен
**Решение:**
- Скрипт покажет предупреждение, но продолжит работу
- Кеширование будет использовать только локальные источники

## Совместимость

- **Обратная совместимость**: старые скрипты продолжают работать
- **ComfyUI Desktop**: поддерживается автоматически
- **ComfyUI Python**: поддерживается автоматически
- **Windows 10/11**: полная поддержка

## Логи и отладка

После запуска ComfyUI проверьте:
1. **comfyui.log** - основные логи ComfyUI
2. **Copy Status** узел - прогресс кеширования
3. **Smart/OPS** узлы - результаты анализа

## Примеры использования

### Тестирование кеша
```cmd
# 1. Настройка Debug режима
arena_bootstrap_cache_v2.bat --debug

# 2. Запуск ComfyUI в том же терминале
cd C:\ComfyUI
python main.py

# 3. В ComfyUI: подключите ArenaAutoCacheSmart к workflow
# 4. Запустите workflow - модели должны кешироваться
```

### Повседневная работа
```cmd
# 1. Настройка Production режима
arena_bootstrap_cache_v2.bat --prod

# 2. Запуск ComfyUI
cd C:\ComfyUI
python main.py

# 3. Работа с кешем в фоновом режиме
```

## Технические детали

### Структура настроек
- **Debug**: максимальная диагностика, минимум фильтров
- **Prod**: оптимальный баланс производительности и фильтрации
- **Default**: безопасные настройки для новичков

### Проверки безопасности
- Валидация путей кеша
- Проверка прав доступа
- Тестирование записи в папку кеша
- Проверка доступности сетевых ресурсов

### Персистентность
- Все настройки сохраняются в пользовательские переменные окружения
- Настройки применяются к текущему процессу и сохраняются для будущих сессий
- Поддержка переопределения через .env файлы (планируется)
