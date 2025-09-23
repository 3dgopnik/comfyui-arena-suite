# ComfyUI Arena Suite

> 🚀 **NEW: Bootstrap Scripts v2.0** — Easy setup with Debug/Prod profiles!
> 
> **Quick Start:**
> ```cmd
> # Debug mode (for testing) - disables filters, enables verbose logs
> arena_bootstrap_cache_v2.bat --debug
> 
> # Production mode (daily work) - enables filters, normal logs  
> arena_bootstrap_cache_v2.bat --prod
> 
> # Then start ComfyUI in the same terminal
> cd C:\ComfyUI
> python main.py
> ```
> 
> **Manual Setup (if needed):**
> - Если `ARENA_CACHE_ROOT` не задан:
>   - Windows: `%LOCALAPPDATA%\ArenaAutoCache` (например, `C:\Users\you\AppData\Local\ArenaAutoCache`)
>   - Linux/macOS: `<корень ComfyUI>/ArenaAutoCache`
> - Установите `ARENA_CACHE_ROOT=<путь>` перед запуском ComfyUI — SSD‑патч будет писать туда.
> - Перезапустите ComfyUI после изменения переменных окружения.
> - Примеры:
>   - PowerShell: `$env:ARENA_CACHE_ROOT='D:\ComfyCache'; python main.py`
>   - CMD: `set ARENA_CACHE_ROOT=D:\ComfyCache && python main.py`
>   - bash: `ARENA_CACHE_ROOT=/mnt/ssd/cache python main.py`
> - Переопределения: `ARENA_CACHE_ENABLE=0` временно отключает патч; `ARENA_CACHE_MAX_GB=512` ограничивает размер кэша (GiB).

Custom nodes for ComfyUI with the "Arena" prefix bundled in a single package.

RU: Набор узлов Arena: наследие (legacy), SSD‑кэширование (AutoCache) и утилиты обновления — всё в одном пакете для упрощения инсталляции ComfyUI.

## Features overview
- Legacy nodes — утилиты с прежними интерфейсами под `ComfyUI_Arena/legacy`.
- AutoCache — рантайм‑патч `folder_paths` с SSD‑кэшем + узлы (Analyze/Ops/Config/StatsEx/Trim/Manager).
- Audit & Warmup — проверка и прогрев кэша по спискам или workflow JSON.
- (Отложено) UI‑оверлей был экспериментом и удалён по умолчанию для стабильности в ComfyUI Desktop. Возможное возвращение описано в ROADMAP.
- Updater scaffolding — заготовки для Hugging Face/CivitAI (WIP) с управлением симлинками `current`.

### AutoCache highlights
- **🚀 Bootstrap Scripts v2.0**: Easy setup with Debug/Prod profiles for different use cases
- **✅ NAS Model Caching**: Successfully caches models from network storage (NAS) to local SSD
- **📊 Progress Indicators**: Real-time copy progress display in terminal with percentage
- **🔧 MB Size Support**: Fine-grained size filtering with `ARENA_CACHE_MIN_SIZE_MB` (default: 1024 MB)
- **🌐 NAS Connectivity Check**: Automatic detection of NAS availability before cache operations
- **🔒 Cache Permissions Check**: Validation of write permissions to cache directory
- **💡 Quick Tips System**: Built-in troubleshooting hints and solutions for common issues
- Zero‑input UX: узлы `Analyze` и `Ops` работают от активного воркфлоу (пустой `workflow_json`).
- Fallback по `last_path`: если парсер не нашёл элементы в схеме, прогревается последняя использованная модель.
- Группы нод: `Arena/AutoCache/Basic`, `Advanced`, `Utils`.
- **Фильтры копирования**: автоматический пропуск мелких моделей (< 1 ГБ) и жёстко прописанных путей.
- **Визуальный индикатор**: нода `Copy Status` показывает прогресс копирования в реальном времени.

## System requirements
- ComfyUI (актуальный `master`) с поддержкой кастом‑нодов.
- Python 3.10+
- Быстрый SSD для AutoCache
- [ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack) для legacy‑узлов (добавьте `ComfyUI-Impact-Pack/modules` в `PYTHONPATH`).

## Quick usage summary

### 🚀 New: Bootstrap Scripts v2.0 (Recommended)
1. Установите пакет через ComfyUI Manager → "Install from URL" (`https://github.com/3dgopnik/comfyui-arena-suite`).
2. **Настройте кеш одним из способов:**
   - **Debug режим** (для тестирования): `arena_bootstrap_cache_v2.bat --debug`
   - **Production режим** (повседневная работа): `arena_bootstrap_cache_v2.bat --prod`
   - **PowerShell GUI**: `arena_bootstrap_cache_v2.ps1`
3. **Запустите ComfyUI в том же терминале:**
   ```cmd
   cd C:\ComfyUI
   python main.py
   ```
4. **Добавьте узел из группы `Arena/AutoCache/Basic`:**
   - для регулярной работы — `ArenaAutoCacheSmart v2.17` (по умолчанию `audit_then_warmup`),
   - для оценки — `ArenaAutoCache Analyze` и подключите `Summary JSON` к `Show Any`,
   - для мониторинга — `ArenaAutoCache Copy Status` для отслеживания прогресса копирования.

### 📋 Manual Setup (Legacy)
1. Установите пакет через ComfyUI Manager → "Install from URL" (`https://github.com/3dgopnik/comfyui-arena-suite`).
2. Обновите список узлов или перезапустите ComfyUI.
3. По необходимости настройте SSD‑кэш (`ARENA_CACHE_ROOT`) и лимит (`ARENA_CACHE_MAX_GB`) — см. документацию ниже.

## 🎉 Latest Updates (v2.17)

### ✅ Successfully Fixed: NAS Model Caching
- **Problem Solved**: Model `Juggernaut_X_RunDiffusion_Hyper.safetensors` (6.7 GB) now caches successfully from NAS to local SSD
- **Critical Bug Fixed**: `_copy_into_cache_lru()` function calls corrected
- **Progress Indicators**: Real-time copy progress with percentage display
- **MB Size Support**: Fine-grained filtering with `ARENA_CACHE_MIN_SIZE_MB=1024.0`

### 🚀 Bootstrap Scripts v2.0
- **Debug Mode**: `--debug` - Disables filters, enables verbose logs for troubleshooting
- **Production Mode**: `--prod` - Enables filters, normal logs for daily work  
- **Default Mode**: `--restore-defaults` - Safe settings for beginners
- **PowerShell GUI**: Interactive setup with visual feedback
- **NAS Check**: Automatic detection of network storage availability
- **Permissions Check**: Validation of cache directory write access

### 📊 Success Logs Example
```
📋 [1/1] Копирую Juggernaut_X_RunDiffusion_Hyper.safetensors...
🔄 [1/1] Прогресс: 0% - Начинаю копирование...
[ArenaAutoCache] copy started: Juggernaut_X_RunDiffusion_Hyper.safetensors
[ArenaAutoCache] copy \\nas-3d\Visual\Lib\SDModels\SDXL\... -> f:\ComfyUIModelCache\checkpoints\...
✅ [1/1] Прогресс: 100% - Копирование завершено!
🎯 Кеширование завершено: 1/1 моделей скопировано
```

📖 **Подробные руководства**: [Русский мануал](docs/ru/MANUAL.md) | [English Manual](docs/en/MANUAL.md)  
📋 **Bootstrap Scripts**: [README_BOOTSTRAP_V2.md](scripts/README_BOOTSTRAP_V2.md)  
✅ **Success Documentation**: [SUCCESS_CACHING.md](docs/ru/SUCCESS_CACHING.md)

Примечание (ComfyUI Desktop): для перезагрузки фронтенда (JS‑расширений) используйте клавишу `R` в главном окне приложения. Изменения Python‑узлов требуют полного перезапуска Desktop.

## Documentation
- Русская документация: `docs/ru/index.md`, `docs/ru/quickstart.md`, `docs/ru/cli.md`, `docs/ru/config.md`, `docs/ru/troubleshooting.md`, `docs/ru/nodes.md`
- English placeholders: `docs/en/index.md`, `docs/en/quickstart.md`, `docs/en/cli.md`, `docs/en/config.md`, `docs/en/troubleshooting.md`
- Правила для агентов: `AGENTS.md`

## Codex workflow (RU)
1. Идентификаторы по‑английски, комментарии на русском.
2. Описывайте задачи Issue: `Codex: <module> — <topic> — <YYYY-MM-DD>` с блоками SUMMARY / ISSUES & TASKS / TEST PLAN / NOTES.
3. Делайте PR с описанием и ссылками на изменения (см. `.github/pull_request_template.md`).
4. Ссылайтесь на Issue: `Refs #<id>`.
5. Обновляйте CHANGELOG (`[Unreleased]`) и соответствующие разделы `docs` в рамках PR.

## Contributing
- См. `CONTRIBUTING.md` для локального окружения и запуска тестов.
- Следуйте `AGENTS.md` и `GLOBAL RULES.md` при добавлении агентов/узлов.
- В CI запускаются тесты на PR — держите их зелёными.
