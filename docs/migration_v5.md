# Arena AutoCache v5.0 Migration Guide

## Обзор изменений

Arena AutoCache v5.0 представляет кардинальные изменения в архитектуре управления кешированием:

- **Settings Panel** становится основным интерфейсом управления
- **Автоматическая активация** по .env файлу без обязательной ноды на канвасе
- **Demand-driven caching** с защитой от массового копирования моделей
- **Локальные overrides** через ноду для конкретных workflow

## Ключевые изменения

### 1. Автоматическая активация

**До v5.0:**
- Нода на канвасе была обязательна для активации кеширования
- Кеширование работало только при наличии активной ноды

**После v5.0:**
- Кеширование активируется автоматически при наличии .env файла с `ARENA_AUTO_CACHE_ENABLED=1`
- Нода на канвасе становится опциональной
- Deferred autopatch запускается при загрузке ComfyUI

### 2. Settings Panel как основной интерфейс

**Новые настройки в Settings Panel:**
- **Model Discovery**: Workflow Only (рекомендуется) / Manual Only
- **Prefetch Strategy**: Lazy (on-demand) / Prefetch Allow-list
- **Max Concurrent Downloads**: Ограничение параллельных загрузок (по умолчанию: 2)
- **Dry-run кнопка**: Предварительный просмотр загрузок

### 3. Demand-driven caching (антимасс-кэш)

**Принципы защиты:**
- **Workflow Only**: Кеширование только моделей из активного workflow
- **Lazy режим**: Загрузка только при первом обращении к модели
- **Лимиты**: concurrency=2, cooldown=5s, byte-budget опционален
- **Белый список категорий**: Валидация против KNOWN_CATEGORIES

### 4. Локальные overrides через ноду

**Новые параметры ноды:**
- **Use Workflow Overrides**: Временное переопределение настроек для текущего workflow
- **Override Discovery Mode**: inherit / workflow_only / manual_only
- **Override Prefetch Strategy**: inherit / lazy / prefetch_allowlist

## Миграция существующих workflow

### Шаг 1: Обновление до v5.0

1. Обновите Arena AutoCache до версии v5.0
2. Перезапустите ComfyUI
3. Проверьте логи на наличие сообщений об автоактивации

### Шаг 2: Настройка через Settings Panel

1. Откройте **Settings** → **Arena**
2. Включите **Enable Arena AutoCache**
3. Настройте **Model Discovery** (рекомендуется: Workflow Only)
4. Выберите **Prefetch Strategy** (рекомендуется: Lazy)
5. Установите **Max Concurrent Downloads** (рекомендуется: 2)

### Шаг 3: Обновление существующих workflow

**Для workflow с нодой Arena AutoCache:**

1. **Если нода не нужна для overrides:**
   - Удалите ноду из workflow
   - Кеширование будет работать автоматически через Settings Panel

2. **Если нужны локальные overrides:**
   - Оставьте ноду в workflow
   - Включите **Use Workflow Overrides**
   - Настройте нужные параметры override

### Шаг 4: Проверка работы

1. Запустите workflow
2. Проверьте логи ComfyUI на наличие сообщений:
   ```
   [ArenaAutoCache] Auto-activation enabled, starting deferred autopatch...
   [ArenaAutoCache] ✅ Deferred autopatch applied successfully
   ```
3. Используйте **Dry-run** кнопку в Settings Panel для предварительного просмотра

## Новые возможности

### API Endpoints

**GET /arena/status** - расширенная информация:
```json
{
  "status": "success",
  "enabled": true,
  "discovery_mode": "workflow_only",
  "prefetch_strategy": "lazy",
  "max_concurrency": 2,
  "required_models_count": 5,
  "session_bytes_downloaded": 1024000,
  "autopatch_status": {
    "started": true,
    "patched": true,
    "copy_worker_running": true,
    "settings_initialized": true
  }
}
```

**POST /arena/autopatch** - с поддержкой required_models:
```json
{
  "action": "start",
  "required_models": [
    {"category": "checkpoints", "filename": "model.safetensors"},
    {"category": "loras", "filename": "lora.safetensors"}
  ]
}
```

**POST /arena/resolve** - dry-run резолвинг:
```json
{
  "models": [
    {"category": "checkpoints", "filename": "model.safetensors"}
  ]
}
```

### Error Codes

Унифицированные коды ошибок:
- `COOLDOWN_ACTIVE` - активен период ожидания
- `ALREADY_RUNNING` - autopatch уже запущен
- `NO_ENV` - .env файл не найден
- `EMPTY_REQUIRED_SET` - не указаны required_models
- `BUDGET_EXCEEDED` - превышен лимит byte-budget

## Troubleshooting

### Проблема: Кеширование не активируется автоматически

**Решение:**
1. Проверьте наличие .env файла в `user/arena_autocache.env`
2. Убедитесь что `ARENA_AUTO_CACHE_ENABLED=1` в .env файле
3. Проверьте логи ComfyUI на наличие ошибок

### Проблема: Массовое копирование моделей

**Решение:**
1. Установите **Model Discovery** в "Workflow Only"
2. Выберите **Prefetch Strategy** "Lazy"
3. Используйте **Dry-run** для предварительного просмотра

### Проблема: Нода не применяет overrides

**Решение:**
1. Включите **Use Workflow Overrides** в ноде
2. Убедитесь что override параметры не установлены в "inherit"
3. Проверьте логи на наличие сообщений о применении overrides

## Обратная совместимость

- **Существующие .env файлы** будут работать без изменений
- **Старые workflow** с нодой продолжат работать
- **API endpoints** расширены, но старые остаются рабочими

## Рекомендации

1. **Используйте Settings Panel** как основной способ управления
2. **Ноду используйте** только для локальных overrides
3. **Включите Dry-run** для предварительного просмотра загрузок
4. **Мониторьте логи** для диагностики проблем
5. **Тестируйте на копиях** workflow перед продакшеном

## Поддержка

При возникновении проблем:
1. Проверьте логи ComfyUI
2. Используйте **Dry-run** для диагностики
3. Проверьте настройки в Settings Panel
4. Создайте Issue в репозитории с подробным описанием
