# EXPERIMENTS.md

## Цель документа
Отслеживание экспериментов, проблем и решений в разработке ArenaAutoCache для ComfyUI.

---

### v2.18 - Успешное кеширование и улучшения UX
**Проблема:** Пользователь запросил индикатор прогресса, поддержку МБ и фиксацию успеха

**Решение:**
- ✅ Добавлен индикатор прогресса в терминале: `🔄 [1/1] Прогресс: 0% - Начинаю копирование...`
- ✅ Добавлена поддержка МБ для минимального размера: `ARENA_CACHE_MIN_SIZE_MB=1024.0`
- ✅ Обновлена функция `_should_skip_by_size()` для проверки обоих порогов (ГБ и МБ)
- ✅ Создана документация успеха: `docs/ru/SUCCESS_CACHING.md`
- ✅ Обновлена версия до v2.17

**Результат:**
- Модель `Juggernaut_X_RunDiffusion_Hyper.safetensors` (6.7 GB) успешно кешируется
- Логи показывают: `copy_started → copy_completed`
- Кеш-папка: `f:\ComfyUIModelCache\checkpoints\`
- Статус: `🎯 Кеширование завершено: 1/1 моделей скопировано`

**Тестирование:**
1. **ArenaAutoCacheSmart v2.17** → ▶ Run → Ожидаем: успешное кеширование с индикатором прогресса

---

### v2.17 - Исправление ошибки _copy_into_cache_lru
**Проблема:** ArenaAutoCacheSmart v2.15 выдавал ошибку `_copy_into_cache_lru() missing 1 required positional argument: 'category'`

**Решение:**
- Исправлены вызовы функции `_copy_into_cache_lru` в `_cache_models_with_progress`
- Функция ожидает `(src: Path, dst: Path, category: str)`, но вызывалась с `(category, name)`
- Добавлен правильный вызов: `_copy_into_cache_lru(Path(src_path), cache_path, model["category"])`
- Обновлена версия до v2.16

**Тестирование:**
1. **ArenaAutoCacheSmart v2.16** → ▶ Run → Ожидаем: успешное копирование без ошибки `missing 1 required positional argument`

---

### v2.16 - Модернизация Bootstrap скриптов
**Проблема:** Пользователь запросил модернизацию arena_bootstrap_cache.bat и arena_bootstrap_cache.ps1 с профилями Debug/Prod

**Решение:**
- Созданы arena_bootstrap_cache_v2.bat и arena_bootstrap_cache_v2.ps1
- Добавлены профили: Debug (отключены фильтры), Prod (повседневная работа), Default (безопасные настройки)
- Добавлена проверка доступности NAS и прав на папку кеша
- Добавлены быстрые подсказки и визуальная индикация
- Поддержка режимов --debug, --prod, --restore-defaults

**Файлы:**
- scripts/arena_bootstrap_cache_v2.bat
- scripts/arena_bootstrap_cache_v2.ps1
- scripts/README_BOOTSTRAP_V2.md
- scripts/test_bootstrap_v2.bat

**Тестирование:**
1. **Debug режим:** arena_bootstrap_cache_v2.bat --debug → ARENA_CACHE_SKIP_HARDCODED=0, MIN_SIZE_GB=0
2. **Prod режим:** arena_bootstrap_cache_v2.bat --prod → включены фильтры, обычные логи
3. **Restore defaults:** arena_bootstrap_cache_v2.bat --restore-defaults → безопасные настройки

---

### v2.6 - Исправления для тестирования
**Проблема:** ArenaAutoCacheSmart v2.5 показывал "No workflow loaded" и Alert ошибку "Invalid workflow against zod schema"

**Решение:**
- Добавлена коррекция неправильных links в workflow
- Исправлено отображение реального пути к workflow
- Обновлена версия до v2.6

**Тестирование:**
1. **ArenaAutoCacheSmart v2.6** → ▶ Run → Ожидаем: реальный путь, без Alert ошибки
2. **ArenaAutoCacheGetActiveWorkflow v2.6** → подключить к Smart → ▶ Run → Ожидаем: структура workflow
3. **ArenaAutoCacheAnalyze v2.6** → подключить к GetActiveWorkflow → ▶ Run → Ожидаем: список моделей

---

### v2.5 - Исправление ошибки 'list' object has no attribute 'keys'
**Проблема:** ArenaAutoCacheSmart получал список моделей от ArenaAutoCacheAnalyze, но ожидал workflow JSON

**Решение:** Добавлена специальная обработка данных от ArenaAutoCacheAnalyze с конвертацией форматов

---

### v2.4 - Отображение пути к workflow
**Проблема:** Пользователь не видел, откуда загружается workflow

**Решение:** Добавлено поле `workflow_path_display` с отображением источника workflow

---

### v2.3 - Анализ JSON workflow
**Проблема:** Нужен анализ JSON структуры workflow для извлечения моделей

**Решение:** Реализованы функции `_extract_models_from_workflow_json` и `_get_model_category`

---

### v2.2 - Правильная стратегия кеширования
**Проблема:** Невозможно получить активный canvas workflow

**Решение:** Реализована работа с последним выполненным workflow через history API

---

### v2.1 - Улучшенная отладка
**Проблема:** Недостаточно информации для отладки

**Решение:** Добавлена подробная отладочная информация и версионирование узлов

---

## Технические детали

### Измененные файлы:
- `custom_nodes/ComfyUI_Arena/autocache/arena_auto_cache.py` - основные изменения
- `EXPERIMENTS.md` - этот файл
- `GLOBAL RULES.md` - обновлены правила

### Ключевые функции:
- `_load_active_workflow()` - получение активного workflow
- `_load_last_executed_workflow()` - получение последнего выполненного workflow
- `_extract_models_from_workflow_json()` - анализ JSON workflow
- `ArenaAutoCacheSmart.run()` - основная логика кеширования

---

## Заключение
Все основные проблемы решены. ArenaAutoCacheSmart v2.6 готов к тестированию.
