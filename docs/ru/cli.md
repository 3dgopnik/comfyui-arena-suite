---
title: "CLI инструменты"
description: "Командные инструменты для ComfyUI Arena Suite"
order: 7
---

# CLI инструменты

Командные инструменты для управления и диагностики ComfyUI Arena Suite.

## 🛠️ Доступные инструменты

### 1. Диагностика системы

#### arena-diagnose

Полная диагностика системы кеширования.

```bash
# Запуск диагностики
python scripts/arena_diagnose.py

# Диагностика с подробным выводом
python scripts/arena_diagnose.py --verbose

# Диагностика конкретной директории
python scripts/arena_diagnose.py --cache-dir /path/to/cache
```

**Выходные данные:**
```
🔍 Arena AutoCache Diagnostic Tool
==================================================

📁 Проверка установки...
  ✅ custom_nodes/ComfyUI_Arena/__init__.py
  ✅ custom_nodes/ComfyUI_Arena/autocache/arena_auto_cache_simple.py
  ✅ web/arena/arena_autocache.js
  ✅ web/extensions/arena_autocache.js

⚙️ Проверка конфигурации...
  ✅ .env file exists: user/arena_autocache.env
  📄 Content: ARENA_CACHE_DIR=C:/ComfyUI/cache...

🚀 Проверка производительности...
  📝 Write 1MB: 0.023s
  📖 Read 1MB: 0.015s

💾 Проверка кеша...
  📊 Cache size: 2.34 GB
  📁 Files: 15
  💿 Disk usage: 45%
  🆓 Free space: 120.5 GB

✅ Диагностика завершена
```

### 2. Мониторинг кеша

#### arena-monitor

Мониторинг кеширования в реальном времени.

```bash
# Запуск мониторинга
python scripts/arena_monitor.py

# Мониторинг с интервалом 5 секунд
python scripts/arena_monitor.py --interval 5

# Мониторинг с сохранением в файл
python scripts/arena_monitor.py --output monitor.log
```

**Выходные данные:**
```
📊 Arena AutoCache Monitor
==================================================
💾 Cache size: 2.34 GB
📁 Files: 15
💿 Disk usage: 45%
🆓 Free space: 120.5 GB
🖥️  CPU: 12%
🧠 Memory: 67%
```

### 3. Управление кешем

#### arena-cache-manager

Управление кешем и его очистка.

```bash
# Показать статистику кеша
python scripts/arena_cache_manager.py --stats

# Очистить кеш
python scripts/arena_cache_manager.py --clear

# Очистить старые файлы (старше 30 дней)
python scripts/arena_cache_manager.py --cleanup --days 30

# Показать размер кеша по категориям
python scripts/arena_cache_manager.py --size-by-category
```

**Примеры использования:**

```bash
# Полная статистика
python scripts/arena_cache_manager.py --stats
# Output:
# 📊 Cache Statistics
# ===================
# Total size: 2.34 GB
# Files: 15
# Categories:
#   checkpoints: 1.8 GB (12 files)
#   loras: 0.4 GB (2 files)
#   vae: 0.14 GB (1 file)

# Очистка старых файлов
python scripts/arena_cache_manager.py --cleanup --days 7
# Output:
# 🧹 Cleaning up files older than 7 days...
# ✅ Removed 3 files (0.5 GB)
```

### 4. Конфигурация

#### arena-config

Управление конфигурацией системы.

```bash
# Показать текущую конфигурацию
python scripts/arena_config.py --show

# Создать .env файл с настройками по умолчанию
python scripts/arena_config.py --init

# Обновить настройки
python scripts/arena_config.py --set ARENA_CACHE_DIR=/new/path

# Валидация конфигурации
python scripts/arena_config.py --validate
```

**Примеры использования:**

```bash
# Инициализация конфигурации
python scripts/arena_config.py --init
# Output:
# ⚙️ Initializing Arena AutoCache configuration...
# ✅ Created .env file with default settings
# 📄 Configuration saved to: user/arena_autocache.env

# Показать конфигурацию
python scripts/arena_config.py --show
# Output:
# ⚙️ Current Configuration
# ========================
# ARENA_CACHE_DIR: C:/ComfyUI/cache
# ARENA_LOG_LEVEL: INFO
# ARENA_AUTO_CACHE_ENABLED: true
# ARENA_CACHE_MIN_SIZE_MB: 100
# ARENA_CACHE_MAX_GB: 50
# ARENA_CACHE_MODE: ondemand
```

### 5. Тестирование производительности

#### arena-benchmark

Тестирование производительности кеширования.

```bash
# Базовый тест производительности
python scripts/arena_benchmark.py

# Тест с конкретным размером файлов
python scripts/arena_benchmark.py --file-size 100MB

# Тест с множественными файлами
python scripts/arena_benchmark.py --files 10

# Тест записи и чтения
python scripts/arena_benchmark.py --test write,read
```

**Примеры результатов:**

```bash
python scripts/arena_benchmark.py
# Output:
# 🚀 Arena AutoCache Performance Benchmark
# ========================================
# 
# 📝 Write Performance:
#   1MB: 0.023s (43.5 MB/s)
#   10MB: 0.156s (64.1 MB/s)
#   100MB: 1.234s (81.0 MB/s)
# 
# 📖 Read Performance:
#   1MB: 0.015s (66.7 MB/s)
#   10MB: 0.089s (112.4 MB/s)
#   100MB: 0.678s (147.5 MB/s)
# 
# 💾 Cache Performance:
#   Hit rate: 95.2%
#   Miss rate: 4.8%
#   Average load time: 0.234s
```

## 📋 Скрипты установки

### Windows

#### arena_bootstrap_cache_v2.bat

Автоматическая установка и настройка для Windows.

```cmd
# Запуск установки
arena_bootstrap_cache_v2.bat

# Установка с настройками
arena_bootstrap_cache_v2.bat --cache-dir "D:\ComfyUI\cache" --max-size 50GB
```

#### arena_set_cache.bat

Настройка параметров кеширования.

```cmd
# Настройка директории кеша
arena_set_cache.bat --dir "D:\ComfyUI\cache"

# Настройка лимита размера
arena_set_cache.bat --max-size 50GB

# Настройка режима кеширования
arena_set_cache.bat --mode eager
```

### PowerShell

#### arena_bootstrap_cache_v2.ps1

PowerShell скрипт для установки.

```powershell
# Запуск установки
.\arena_bootstrap_cache_v2.ps1

# Установка с параметрами
.\arena_bootstrap_cache_v2.ps1 -CacheDir "D:\ComfyUI\cache" -MaxSize 50GB
```

## 🔧 Утилиты разработки

### 1. Проверка качества кода

#### arena-lint

Проверка качества кода и стиля.

```bash
# Проверка всех файлов
python scripts/arena_lint.py

# Проверка конкретного файла
python scripts/arena_lint.py --file autocache/arena_auto_cache_simple.py

# Автоматическое исправление
python scripts/arena_lint.py --fix
```

### 2. Тестирование

#### arena-test

Запуск тестов системы.

```bash
# Запуск всех тестов
python scripts/arena_test.py

# Запуск конкретных тестов
python scripts/arena_test.py --test test_cache_operations

# Запуск с покрытием
python scripts/arena_test.py --coverage
```

### 3. Генерация документации

#### arena-docs

Генерация и обновление документации.

```bash
# Генерация документации
python scripts/arena_docs.py --generate

# Обновление документации
python scripts/arena_docs.py --update

# Проверка ссылок
python scripts/arena_docs.py --check-links
```

## 📊 Мониторинг и логи

### 1. Просмотр логов

```bash
# Просмотр логов ComfyUI
tail -f /path/to/ComfyUI/logs/comfyui.log

# Фильтрация логов Arena
tail -f /path/to/ComfyUI/logs/comfyui.log | grep -i arena

# Просмотр логов с временными метками
tail -f /path/to/ComfyUI/logs/comfyui.log | grep -E "\[.*\]"
```

### 2. Анализ производительности

```bash
# Анализ использования диска
python scripts/arena_analyze.py --disk-usage

# Анализ времени загрузки
python scripts/arena_analyze.py --load-times

# Анализ статистики кеша
python scripts/arena_analyze.py --cache-stats
```

## 🚀 Автоматизация

### 1. Cron задачи (Linux/macOS)

```bash
# Очистка кеша каждую неделю
0 2 * * 0 /path/to/scripts/arena_cache_manager.py --cleanup --days 7

# Мониторинг каждые 5 минут
*/5 * * * * /path/to/scripts/arena_monitor.py --quiet
```

### 2. Windows Task Scheduler

```cmd
# Создание задачи очистки кеша
schtasks /create /tn "Arena Cache Cleanup" /tr "python scripts\arena_cache_manager.py --cleanup --days 7" /sc weekly

# Создание задачи мониторинга
schtasks /create /tn "Arena Monitor" /tr "python scripts\arena_monitor.py --quiet" /sc minute /mo 5
```

### 3. Docker

```dockerfile
# Dockerfile для Arena AutoCache
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

# Запуск диагностики при старте
CMD ["python", "scripts/arena_diagnose.py"]
```

## 📚 Дополнительные ресурсы

- [Быстрый старт](quickstart.md) - начальная настройка
- [Руководство по нодам](nodes.md) - описание нод
- [Конфигурация](config.md) - настройка параметров
- [Руководство пользователя](manual.md) - полное руководство
- [Устранение неполадок](troubleshooting.md) - решение проблем

## 🆘 Получение помощи

### Сообщество

- **GitHub Issues** - [сообщить об ошибке](https://github.com/3dgopnik/comfyui-arena-suite/issues)
- **Discussions** - [задать вопрос](https://github.com/3dgopnik/comfyui-arena-suite/discussions)
- **Documentation** - [полная документация](https://github.com/3dgopnik/comfyui-arena-suite/tree/main/docs)

### Поддержка

Если у вас возникли проблемы с CLI инструментами:

1. **Проверьте зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Запустите диагностику:**
   ```bash
   python scripts/arena_diagnose.py
   ```

3. **Проверьте права доступа:**
   ```bash
   chmod +x scripts/*.py
   ```

---

**CLI инструменты - ваш надежный помощник для управления Arena AutoCache!**