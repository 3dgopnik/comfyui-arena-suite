# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.1.3] - Fri Oct 10 2025 12:01:06 GMT+0300 (Москва, стандартное время)

### Added
- **Universal NAS Scanning**: Implemented intelligent scanning that automatically discovers ALL model folders on NAS, regardless of folder names or structure
- **Smart Model Categorization**: Added automatic pattern-based categorization for discovered model folders
- **Generic Models Category**: Created fallback "models" category for any folders that don't fit standard ComfyUI categories
- **Enhanced Model Discovery**: System now finds models in custom folder structures like "Diffusion Model", "LLM", "text_encoders"

### Changed
- **Scanning Algorithm**: Replaced rigid folder-based scanning with flexible universal discovery mechanism
- **Caching Strategy**: Improved cache efficiency by finding all model locations during initial scan
- **Workflow-Only Copying**: Refined copying behavior to only cache models from active workflows, preventing unnecessary mass copying

### Fixed
- **Wan Model Detection**: Resolved issue where wan diffusion models in "Diffusion Model" folder were not being discovered during NAS scanning
- **Limited Folder Scanning**: Fixed scanning to work beyond predefined folder lists, making it truly universal
- **Model Cache Misses**: Eliminated cache misses for models in non-standard folder locations

---

## [6.0.2] - Thu Oct 09 2025 15:22:45 GMT+0300 (Москва, стандартное время)

### Changed
- **Smart Scanning**: Проверка размера файла (>= min_size) вместо хардкоженного списка расширений
- **Configurable Parameters**: Min size и max depth читаются из .env (`ARENA_CACHE_MIN_SIZE_MB=1.0`, `ARENA_NAS_SCAN_MAX_DEPTH=3`)
- **Performance Optimization**: `iterdir()` вместо `glob()` для 2-3x ускорения сканирования
- **Early Exit**: Останавливает проверку папки при первой найденной модели

### Fixed
- **SUPIR Subfolder Models**: Исправлена двойная подпапка в cache_path (строка 1765) - использование `filename_only` вместо `filename_normalized`
- **Recursive NAS Scanning**: Рекурсивное сканирование автоматически находит модели в любых вложенных папках (SDXL\SUPIR, SD1.5\ControlNet, etc.)
- **Extension-Agnostic Detection**: Определение моделей по размеру файла вместо списка расширений - поддержка любых форматов
- **Unified Config Paths**: Оба конфиг файла (`arena_autocache.env`, `arena_nas_cache.json`) теперь в `comfy_root/user/`

---

## [6.0.2] - Thu Oct 09 2025 15:06:52 GMT+0300 (Москва, стандартное время)

### Changed
- **Auto-discovery**: Система больше не требует ручного добавления путей в KNOWN_CATEGORY_FOLDERS
- **Scan Depth**: Рекурсивное сканирование ограничено 2 уровнями для производительности

### Fixed
- **Recursive NAS Scanning**: Arena Path Manager теперь рекурсивно сканирует подпапки до 2 уровней глубины, автоматически находя модели в нестандартных путях (SDXL\SUPIR, SD1.5\ControlNet, etc.)
- **SUPIR Subfolder Models**: Добавлен базовый путь SDXL в upscale_models для автоматического обнаружения SUPIR моделей
- **Cache Path Construction**: Исправлена двойная подпапка в cache_path (v6.0.1)

---

## [6.0.1] - Thu Oct 09 2025 14:51:54 GMT+0300 (Москва, стандартное время)

### Fixed
- **SUPIR Subfolder Models Caching**: Исправлена критическая проблема с кешированием моделей из подпапок (SUPIR, etc.). Модели с путями типа `SUPIR\SUPIR-v0Q_fp16.safetensors` теперь корректно обнаруживаются через `folder_paths.get_full_path()` и кешируются без двойных подпапок в пути
- **Cache Path Construction**: Заменен `filename_normalized` на `filename_only` в строке 1765 для формирования `cache_path`, что устраняет ошибку "Model NOT FOUND in folder_paths"

---

## [6.0.0] - Wed Oct 08 2025 17:06:23 GMT+0300 (Москва, стандартное время)

### Changed
- **Major Version Bump**: Updated from v5.1.0 to v6.0.0 to reflect major improvements and critical bug fixes
- **Node Registration**: Updated NODE_CLASS_MAPPINGS to "🅰️ Arena AutoCache v6.0.0"
- **Package Versioning**: Synchronized version in pyproject.toml to v6.0.0
- **Documentation**: Updated README.md and Russian documentation to reflect v6.0.0

---

## [5.1.0] - Wed Oct 08 2025 17:04:05 GMT+0300 (Москва, стандартное время)

### Changed
- **Version Bump**: Updated version from v4.20.0 to v5.1.0 across all components
- **Node Registration**: Updated NODE_CLASS_MAPPINGS and display names to reflect v5.1.0
- **Documentation**: Synchronized version numbers in README.md, pyproject.toml, and Russian documentation
- **Node Description**: Updated Arena AutoCache node description with v5.1.0 features and bug fixes

---

## [4.20.0] - Wed Oct 08 2025 16:56:28 GMT+0300 (Москва, стандартное время)

### Added
- **Universal Workflow Analysis**: Implemented automatic model detection across all node types without manual configuration
- **Enhanced Error Handling**: Added robust Path/str conversion logic in _copy_worker for cross-platform compatibility
- **Comprehensive Testing**: Validated caching functionality across SUPIR, Wan, and Flux workflow scenarios

### Changed
- **Universal Model Parser**: Replaced hardcoded node type detection with universal parser that scans widgets_values for model file extensions
- **Cache Path Construction**: Improved cache path handling to prevent Path/str type inconsistencies in worker threads
- **Model Type Detection**: Enhanced _detect_model_type to correctly identify SUPIR models in upscale_models category

### Fixed
- **Model Caching Pipeline**: Resolved critical issue where models were detected but not actually cached due to missing queue processing
- **Path Handling**: Fixed WindowsPath + str concatenation error in _copy_worker that prevented file copying operations
- **SUPIR Model Detection**: Corrected model type detection for SUPIR models, ensuring proper cache folder structure
- **Double Path Creation**: Eliminated duplicate subfolders (Flux\flux\, Wan\Wan\) by using os.path.basename for type detection
- **Python Indentation**: Fixed critical indentation errors in post_autopatch_endpoint that prevented autopatch execution
- **Filename Resolution**: Resolved folder_paths.get_full_path() failures by using basename for model lookups

---

## [4.19.0] - Wed Oct 08 2025 16:56:10 GMT+0300 (Москва, стандартное время)

### Added
- **System Health Checks**: Added comprehensive process analysis for Cursor IDE and ComfyUI applications
- **GPU Utilization Tracking**: Implemented monitoring of Desktop Window Manager and 3D rendering processes

### Changed
- **System Monitoring**: Enhanced diagnostic capabilities to track GPU utilization by process type
- **Performance Analysis**: Improved identification of performance bottlenecks in development environment

### Fixed
- **System Performance Diagnostics**: Resolved mouse lag and system slowdown issues by identifying GPU bottleneck (87% utilization)
- **Desktop Window Manager Optimization**: Identified DWM consuming 45.8% GPU resources due to excessive Cursor IDE processes
- **Process Management**: Cleaned up 16 redundant Cursor processes consuming 3.8GB RAM and significant GPU resources

---

## [4.18.0] - Wed Oct 08 2025 11:38:15 GMT+0300 (Москва, стандартное время)

### Added
- **Arena AutoCache Settings UI**: Improved user experience with intuitive setting names and logical grouping
- **Visual Settings Organization**: Added color-coded circles (🔴🟡🟢) to group related settings and bypass alphabetical sorting

### Changed
- **Settings Display Names**: Replaced technical IDs with user-friendly names (e.g., "Enable Auto Cache" instead of "autocache_enable")
- **Settings Order**: Reorganized settings to group related controls together - toggles (Enable Auto Cache + Verbose Logging) now appear side by side
- **Save Button**: Fixed capitalization from "save" to "Save Settings" for better user experience

### Fixed
- **Alphabetical Sorting Issue**: Resolved ComfyUI's automatic alphabetical sorting that was placing "Verbose Logging" at the bottom by using emoji prefixes
- **Settings Grouping**: Ensured logical flow from main toggles → cache configuration → save action
- **User Interface Consistency**: Standardized setting names to be more descriptive and professional

---

## [4.17.2] - Wed Oct 08 2025 09:32:12 GMT+0300 (Москва, стандартное время)

### Changed
- **API Integration**: Переход на официальный ComfyUI Settings API для более надёжного чтения значений настроек, особенно для числовых полей с PrimeVue InputNumber
- **Fallback Strategy**: Улучшена стратегия fallback с приоритетом: API → Store → localStorage → DOM (с принудительным commit)

### Fixed
- **Settings UI**: Исправлена критическая проблема с чтением значения Max Cache GB из ComfyUI Settings UI. Теперь используется официальный ComfyUI API (app.extensionManager.setting.get) вместо парсинга DOM, что полностью решает проблему с PrimeVue InputNumber компонентом
- **DOM Timing**: Добавлен принудительный blur() для числовых полей перед чтением DOM как fallback, устраняя проблемы с timing когда значение не коммитится до потери фокуса

---

## [4.17.1] - Tue Oct 07 2025 17:12:53 GMT+0300 (Москва, стандартное время)

### Changed
- Старт в безопасном режиме: полный отказ от авто‑кеширования на запуске (manual‑only). Никаких копий до явного включения красного режима
- Красный режим: запускает отложенный on‑demand автопатч сразу после записи `ARENA_AUTO_CACHE_ENABLED=1` и `ARENA_AUTOCACHE_AUTOPATCH=1` (через UI). Перехват путей `folder_paths.get_full_path` работает только при реальных загрузках моделей
- Зелёный режим: только использование кеша (новые копии не создаются), при miss — работа с оригинальным путём
- Кнопка в UI: пишет флаги в `.env` и при красном триггерит автопатч; при зелёном — не запускает копии
- При выходе ComfyUI `.env` автоматически сбрасывается в `0/0` (через `atexit`) — защита от «шторма» копирования при следующем старте
- API `/arena/autopatch`: разрешён запуск без `required_models` для true on‑demand сценария (копирование инициируется по факту загрузки)
- UI (красный): перед автопатчем отправляются найденные модели в `/arena/analyze_workflow` для корректного расширения категорий и прогрева состояния

### Fixed
- Спорадические массовые копии при старте из‑за ранних системных сканов путей (extra_model_paths); добавлены проверки стека вызовов и отложенный патч, чтобы реагировать только на реальные загрузки

### Removed
- Автостарт кеширования при наличии `1/1` на старте — убран как опасный по дисковому I/O и сети

---

## [5.0.0] - Tue Oct 07 2025 12:42:58 GMT+0300 (Москва, стандартное время)

### Added
- Settings UI for Arena AutoCache with a dedicated "💾 Save to .env" button at the top of the Arena section. One-click save creates/updates `user/arena_autocache.env` with all settings.
- Robust DOM value reading with fallbacks to ensure settings are reliably captured from the ComfyUI dialog.

### Changed
- Consolidated all Arena settings UI logic into a single script `web/arena_settings_save_button.js` for stability and ease of maintenance.
- Documentation consolidated to a single `docs/` root with language folders `docs/ru` and `docs/en`. All documentation filenames unified to lowercase for consistency.
- README updated to v5.0.0 with the new primary flow (Settings UI + Save to .env).
- Sync scripts simplified for ComfyUI Desktop environments.

### Fixed
- Auto-creation and reliable updating of `.env` now works consistently; all values are sent as strings to the backend to avoid type errors.
- Button rendering and ordering issues resolved by registering the Save button as a setting row and pinning it to the top.
- pyproject.toml restored to valid TOML with project metadata and tooling sections.

### Removed
- 19 outdated scripts and test files removed to avoid conflicts and reduce maintenance burden.
- Legacy/duplicate documentation folders removed (migrated to unified `docs/`).

---

## [5.0.0] - Tue Oct 07 2025 11:43:53 GMT+0300 (Москва, стандартное время)

### Added
- **Settings UI для Arena AutoCache** - Полноценный интерфейс настройки в ComfyUI Settings → arena
- Кнопка 💾 Save to .env расположена вверху списка настроек для удобства
- Все 11 параметров AutoCache доступны через графический интерфейс
- Автоматическое создание файла `user/arena_autocache.env` при сохранении
- Чтение настроек напрямую из DOM с умным fallback для Cache Root
- Интеграция с backend endpoint `/arena/env` для надёжного сохранения
- Closes #116

### Changed
- **Упрощена активация кеширования** - теперь не требуется добавлять ноду на canvas
- **Улучшен UX** - кнопка Save всегда видна в начале списка настроек
- **Обновлена документация** - context.md и development.md отражают новую архитектуру

### Fixed
- **Исправлен pyproject.toml** - корректная TOML структура вместо одной строки с версией
- **Убраны ошибки загрузки** - удалены конфликтующие JS файлы из папки _disabled

### Removed
- **Очистка проекта** - удалено 19 устаревших скриптов и тестовых файлов:
- arena_bootstrap_cache_v2.*, arena_fast_start.bat, arena_optimize_manager.bat
- check_comfyui_status.ps1, update_comfyui_desktop.*, sync_js_*.bat
- arena_test.js и 9 старых arena_settings_*.js файлов
- **Мёртвый код** - очищены неиспользуемые функции и комментарии

---

## [4.14.2] - Mon Oct 06 2025 16:25:47 GMT+0300 (Москва, стандартное время)

### Added
- Автосоздание `.env` при первом включении `AutoCacheEnable` (POST `/arena/env` с `ARENA_AUTO_CACHE_ENABLED=1`, `ARENA_AUTOCACHE_AUTOPATCH=1`).
- Улучшенные логи для диагностики: `DOM ready`, `Button row attached`, детальные ошибки POST/селекторов.

### Changed
- Единый UI-скрипт настроек для ARENA: удалены/отключены дублирующие файлы; теперь используется один источник — `web/arena_settings_save_button.js`.
- Переписан `arena_settings_save_button.js`: надёжное ожидание рендера (DOM-wait), единые селекторы (`arena.autocache_enable`), стабильная вставка строки с кнопками.
- Добавлены кнопки: "💾 Save to .env" (POST `/arena/env`), "🔍 Status" (GET `/arena/status`), "📝 Preview .env" (предпросмотр payload без POST).

---

## [4.14.1] - Mon Oct 06 2025 15:15:43 GMT+0300 (Москва, стандартное время)

### Added
- **Diagnostic Tools**: Добавлен тестовый файл arena_test.js для проверки корректности загрузки JavaScript модулей
- **Robust Validation**: Реализованы дополнительные проверки доступности ComfyUI Settings API

### Changed
- **Error Handling**: Улучшена диагностика загрузки JavaScript файлов с подробными логами для отладки
- **Code Formatting**: Исправлено форматирование arena_simple_header.js для лучшей читаемости

### Fixed
- **Settings Panel**: Восстановлен пропавший раздел ARENA в настройках ComfyUI с улучшенной стабильностью загрузки
- **JavaScript Loading**: Добавлены проверки доступности Settings API и обработка ошибок для предотвращения сбоев
- **Alternative Fallback**: Реализован альтернативный способ создания секции Arena при недоступности основного API

---

## [4.14.0] - Mon Oct 06 2025 14:10:18 GMT+0300 (Москва, стандартное время)

### Changed
- **ARENA Button Logic**: Кнопка ARENA теперь проверяет реальные значения из Settings Panel перед сохранением в .env файл
- **Settings Panel Logic**: Аналогично улучшена логика Settings Panel для использования только реальных настроек
- **Debug Logging**: Добавлено логирование реальных настроек для отладки процесса синхронизации

### Fixed
- **Settings Synchronization**: Исправлена проблема с хардкодными значениями по умолчанию в кнопке ARENA и Settings Panel. Теперь используются только реальные настройки из Settings Panel, без хардкодных значений типа "ondemand", "D:/ArenaCache", "50" и т.д.
- **Environment File Updates**: Улучшена логика сохранения настроек - теперь в .env файл записываются только реальные значения из Settings Panel, а не значения по умолчанию

---

## [4.13.0] - Mon Oct 06 2025 14:08:41 GMT+0300 (Москва, стандартное время)

### Changed
- **Settings Panel Logic**: Добавлена синхронизация с кнопкой ARENA через localStorage для обеспечения консистентности настроек
- **Environment File Updates**: Теперь при активации через кнопку ARENA сохраняются все настройки: режим кеширования, путь к кешу, размеры файлов, стратегия предзагрузки и другие параметры

### Fixed
- **Settings Synchronization**: Исправлена логика сохранения настроек из Settings Panel в .env файл при активации кнопки ARENA. Теперь кнопка ARENA читает все настройки из Settings Panel и сохраняет их в .env файл, а не только флаг включения
- **ARENA Button Integration**: Улучшена интеграция между кнопкой ARENA и панелью настроек для корректной синхронизации всех параметров кеширования

---

## [4.12.2] - Fri Oct 03 2025 15:54:59 GMT+0300 (Москва, стандартное время)

### Added
- **Global UI Integration**: Arena AutoCache теперь интегрирован непосредственно в интерфейс ComfyUI без необходимости добавления ноды на канвас
- **Floating Actionbar**: Плавающая кнопка Arena с возможностью перетаскивания и автоматического встраивания в хедер ComfyUI
- **Settings Panel**: Полная панель настроек Arena в разделе ComfyUI Settings с управлением всеми параметрами кеширования
- **Persistent State**: Сохранение позиции и состояния (docked/floating) в localStorage для восстановления при перезапуске

### Changed
- **API Registration**: Глобальная регистрация API endpoints при загрузке модуля, обеспечивающая доступность без ноды на канвасе
- **Docking Mechanism**: Умная логика автовстраивания при перетаскивании кнопки в область хедера (верхние 80px экрана)
- **User Experience**: Упрощенный доступ к функциям Arena AutoCache через интерфейс ComfyUI

---

## [4.16.0] - Fri Oct 03 2025 13:46:21 GMT+0300 (Москва, стандартное время)

### Added
- **Global UI Toggle**: Arena AutoCache can now be enabled directly from ComfyUI header without adding nodes to canvas
- **Header Indicator**: Added 🅰️ button in ComfyUI header with color-coded status (blue=ON, gray=OFF)
- **Settings Panel**: New "Arena" section in ComfyUI Settings for comprehensive cache configuration
- **Status API**: New `/arena/status` endpoint providing real-time cache status and configuration
- **Right-click Context**: Right-click header button opens Settings → Arena section for quick access

### Changed
- **User Experience**: Simplified activation workflow - one-click caching enable/disable from header
- **Documentation**: Updated manual and README with global toggle instructions as primary method
- **Integration**: Enhanced ComfyUI integration with seamless UI controls

---

## [4.12.1] - Fri Oct 03 2025 13:41:51 GMT+0300 (Москва, стандартное время)

### Added
- **Global UI Toggle**: Arena AutoCache can now be enabled directly from ComfyUI header without adding nodes to canvas
- **Header Indicator**: Added 🅰️ button in ComfyUI header with color-coded status (blue=ON, gray=OFF)
- **Settings Panel**: New "Arena" section in ComfyUI Settings for comprehensive cache configuration
- **Status API**: New `/arena/status` endpoint providing real-time cache status and configuration
- **Right-click Context**: Right-click header button opens Settings → Arena section for quick access

### Changed
- **User Experience**: Simplified activation workflow - one-click caching enable/disable from header
- **Documentation**: Updated manual and README with global toggle instructions as primary method
- **Integration**: Enhanced ComfyUI integration with seamless UI controls

---

## [4.12.0] - Fri Oct 03 2025 12:16:04 GMT+0300 (Москва, стандартное время)

### Added
- **Model Type Sorting**: Automatic model sorting in cache by type (SDXL, SD1.5, Flux, etc.) with subfolder creation for better file organization
- **Smart Model Detection**: New `_detect_model_type()` function that intelligently identifies model types from filenames using pattern matching
- **Enhanced Cache Structure**: Updated cache path structure to `cache_root/category/model_type/filename` for improved organization
- **Backward Compatibility**: Seamless support for existing cached models in old locations without breaking functionality

---

## [4.15.0] - 2025-01-27

### Fixed
- **Button Reset Issue**: Fixed JavaScript buttons not resetting after click - now `save_env_now`, `sync_from_env` buttons properly reset after action
- **Auto-load .env**: Added automatic loading of settings from .env file when node is created (if .env exists)
- **Comprehensive Model Loader Support**: Added comprehensive JavaScript logic to detect all ComfyUI model loaders and map them to correct categories
- **All Model Categories**: Enhanced `getModelType()` function to handle all ComfyUI model types including:
  - Text encoders: `DualCLIPLoader`, `FluxClipModel`, `QuadrupleCLIPLoader`, `T5TextEncoder`, `CLIPTextEncoder`
  - CLIP Vision: `CLIPVisionLoader`, `CLIPVisionLoaderModelOnly`
  - Embeddings: `EmbeddingLoader`, `EmbeddingLoaderModelOnly`
  - Hypernetworks: `HypernetworkLoader`, `HypernetworkLoaderModelOnly`
  - IPAdapter: `IPAdapterLoader`, `IPAdapterLoaderModelOnly`
  - GLIGEN: `GLIGENLoader`, `GLIGENLoaderModelOnly`
  - AnimateDiff: `AnimateDiffLoader`, `AnimateDiffLoaderModelOnly`
  - T2I Adapter: `T2IAdapterLoader`, `T2IAdapterLoaderModelOnly`
  - GGUF: `GGUFLoader`, `UNetLoaderGGUF`, `CLIPLoaderGGUF`
  - UNet: `UNetLoader`, `UNetLoaderModelOnly`
  - Diffusion: `DiffusionLoader`, `DiffusionLoaderModelOnly`
  - Upscale: `UpscaleLoader`, `UpscaleLoaderModelOnly`
  - ControlNet: `ControlNetLoader`, `ControlNetLoaderModelOnly`
  - VAE: `VAELoader`, `VAELoaderModelOnly`
  - LoRA: `LoraLoader`, `LoraLoaderModelOnly`
  - Checkpoints: `CheckpointLoader`, `CheckpointLoaderSimple`, `CheckpointLoaderModelOnly`
  - CLIP: `CLIPLoader`, `CLIPLoaderModelOnly`

### Technical Details
- Updated `arena_autocache.js` v4.1 with button reset functionality and auto-load from .env
- Updated `arena_workflow_analyzer.js` v1.2 with comprehensive model loader detection
- JavaScript now correctly identifies all ComfyUI model types and sends them to Python with proper categories
- Python automatically extends `effective_categories` when new categories are detected from workflow analysis
- No static categories needed - all determined dynamically through JavaScript analysis

## [4.14.0] - 2025-01-27

### Added
- **Bidirectional .env Sync**: Real-time synchronization between node UI and .env file
- **New UI Controls**: 
  - `Save to .env Now` button - instantly writes current settings to .env file
  - `Sync from .env` button - loads settings from .env file into UI
  - `Live .env Sync` toggle - enables automatic file watching and reloading
- **REST API Endpoints**: 
  - `GET /arena/env` - retrieve current ARENA_* environment variables
  - `POST /arena/env` - save environment variables to .env file
- **File Watcher**: Background monitoring of .env file changes with automatic reloading

### Fixed
- **.env Creation**: Fixed issue where .env file wasn't created when changing node parameters without running
- **.env Loading**: Fixed "cannot access local variable 'os'" error in _load_env_file()
- **Caching Blocking**: Resolved issue where scheduled caching was blocked by overly aggressive system scan detection
- **Default Values**: Aligned ARENA_AUTO_CACHE_ENABLED default to "false" across all components

### Changed
- **System Scan Detection**: Refined detection to use exact function name matching instead of substring matching
- **Environment Loading**: _load_env_file() now returns boolean indicating success/failure
- **Reload Logic**: Removed dependency on _env_loaded flag for file reloading
- **UI Parameters**: Added new boolean controls for .env synchronization

### Technical Details
- Enhanced _ensure_env_loaded() to only set _env_loaded flag on successful file loading
- Improved _reload_settings_if_needed() to reload .env file whenever it exists
- Updated IS_CHANGED() to handle new UI buttons and live sync functionality
- Added background thread for .env file monitoring with 1-second polling interval
- Implemented proper API validation for environment variable keys

## [4.11.1] - Thu Oct 02 2025 13:18:00 GMT+0300 (Москва, стандартное время)

### Changed
- **Copy Task Filtering**: Enhanced `_schedule_copy_task()` with multiple safety checks:
- System scan detection via call stack analysis
- Startup phase protection (first 30 seconds)
- Active Arena node verification
- Copy frequency limiting (1-second intervals)
- **Performance Optimization**: Significantly reduced system load during ComfyUI startup by eliminating unnecessary background copy operations

### Fixed
- **Mass Copying Issue**: Resolved critical problem where Arena AutoCache was triggering thousands of unnecessary copy tasks during ComfyUI's system scanning phase
- **System Scan Detection**: Added intelligent filtering to distinguish between system initialization and actual workflow usage
- **Startup Phase Protection**: Implemented 30-second startup delay to prevent caching during ComfyUI's initial model scanning

---

## [4.13.0] - Wed Oct 02 2025 10:00:00 GMT+0300 (Москва, стандартное время)

### Удалено
- **Упрощенный интерфейс**: Удалены поля `cache_categories` и `categories_mode` из Python ноды
- **Ручное управление категориями**: Убрана необходимость вручную указывать категории моделей
- **Сложная логика категорий**: Удалены функции `_compute_effective_categories`, константы `DEFAULT_WHITELIST` и `KNOWN_CATEGORIES`
- **Опасный режим eager**: Убран режим массового кэширования всех моделей при запуске ComfyUI
- **Функция _eager_cache_all_models**: Удалена функция массового кэширования для защиты дискового пространства

### Изменено
- **Автоматическое определение моделей**: Категории моделей теперь определяются автоматически через JavaScript анализ workflow
- **Упрощенная архитектура**: Убрана сложная логика взаимодействия между Python и .env файлами для категорий
- **Чистый интерфейс**: Нода стала проще и понятнее - JS автоматически анализирует workflow и определяет нужные модели
- **Безопасные режимы кэширования**: Остались только ondemand и disabled режимы для защиты дискового пространства

### Исправлено
- **Консистентность**: Приведена в соответствие концепция, где JS отвечает за анализ workflow
- **Упрощение**: Убрана дублирующая логика между Python и JavaScript
- **Безопасность**: Убран опасный режим eager, который мог заполнить диск при массовом кэшировании

---

## [4.5.2] - 2025-09-30

### Added
* **MCP Changelog Integration** - объединение MCP changelog с основным CHANGELOG.md проекта для централизованного управления версиями
* **Unified Changelog Management** - единая система отслеживания изменений через MCP tools для автоматического обновления документации

### Enhanced
* **Documentation Workflow** - улучшен процесс ведения changelog с автоматическим анализом изменений
* **Version Management** - централизованное управление версиями проекта через MCP changelog system

## [4.5.1] - 2025-09-30

### Fixed
* **Исправлена логика значений по умолчанию** - все настройки теперь 0/False/disabled при первом запуске
* **Исправлена проблема с созданием .env файла** - файл теперь создается корректно при активации enable_caching=True
* **Исправлена проблема с небезопасными настройками в .env** - файл теперь создается с безопасными значениями по умолчанию (disabled, false, 0)
* **Исправлено время создания .env файла** - файл создается только при переключении чекбокса enable_caching=True, а не при запуске run()
* **Добавлена функция очистки переменных окружения** - `_cleanup_env_variables()` для корректной деактивации

### Changed
* **Упрощена логика создания .env файла** - создается только при активации enable_caching=True
* **Улучшена диагностика** - добавлен debug вывод для отладки проблем с .env файлом

## [4.5.0] - 2025-01-30

### Added
* **Переключатель активации** - enable_caching для контроля кеширования
  * **Переключатель `enable_caching`** - основной элемент управления кешированием
  * **Безопасность по умолчанию** - кеширование отключено до активации переключателя
  * **Все параметры видны** - полная настройка доступна всегда

### Enhanced
* **Улучшенный UX** - четкий переключатель для активации кеширования
* **Полная настройка** - все параметры доступны для настройки
* **Безопасность** - кеширование работает только при `enable_caching=True`

### Technical
* **Обновленная структура INPUT_TYPES** - все параметры в `required`
* **Переключатель активации** - enable_caching для контроля функциональности
* **Обновленная архитектура** - логика активации в методе `run()`

## [4.4.0] - 2025-01-29

### Added
* **Гибкие режимы кэширования** - добавлен параметр `cache_mode` с тремя режимами:
  * **`ondemand`** (по умолчанию) - кэширование только при первом обращении к модели
  * **`eager`** - массовое копирование всех моделей при загрузке ComfyUI
  * **`disabled`** - полное отключение кэширования
* **OnDemand кэширование** - умное кэширование только нужных моделей
* **Eager кэширование** - массовое копирование всех моделей в фоне
* **Валидация режимов** - проверка корректности режима кэширования в .env файле
* **Обновленная конфигурация** - добавлен параметр `ARENA_CACHE_MODE` в .env файл

### Enhanced
* **Улучшенная диагностика** - статус сообщения теперь показывают активный режим кэширования
* **Гибкое управление** - режим кэширования можно настроить через ноду или .env файл
* **Производительность** - OnDemand режим экономит место на диске и время загрузки
* **Обратная совместимость** - существующие настройки продолжают работать

### Technical
* **Новый параметр ноды** - `cache_mode` с выбором из трех режимов
* **Функция eager кэширования** - `_eager_cache_all_models()` для массового копирования
* **Валидация .env** - проверка корректности значения `ARENA_CACHE_MODE`
* **Обновленная версия** - v4.4.0 с поддержкой гибких режимов кэширования

## [4.3.3] - 2025-01-29

### Fixed
* **Issue #113**: Arena AutoCache нода присутствует на канвасе, но кэширование не работает
  * **Корень проблемы найден** - .env файл не загружался при импорте модуля
  * **Правильная архитектура** - добавлена идемпотентная загрузка .env файла
  * **Единая точка загрузки** - функция `_ensure_env_loaded()` гарантирует загрузку .env
  * **Устранена двойная загрузка** - .env загружается один раз, кэшируется в `_env_loaded`
  * **Deferred autopatch работает** - теперь запускается при импорте модуля

### Enhanced
* **Идемпотентная загрузка .env** - безопасная загрузка при повторных вызовах
* **Кэширование состояния** - флаг `_env_loaded` предотвращает повторную загрузку
* **Улучшенная архитектура** - единая точка загрузки настроек
* **Производительность** - .env файл загружается только один раз

## [4.3.2] - 2025-01-29

### Fixed
* **Issue #113**: Arena AutoCache нода присутствует на канвасе, но кэширование не работает
  * **Диагностика deferred autopatch** - добавлены подробные логи для отладки
  * **Улучшена функция `_is_folder_paths_ready()`** - детальная диагностика каждого условия готовности
  * **Добавлены диагностические логи** в начало модуля для отслеживания запуска autopatch
  * **Подробная диагностика** - теперь видно на каком этапе происходит сбой
  * **Эмодзи и читаемые сообщения** для лучшей отладки

### Enhanced
* **Улучшена диагностика** - добавлены логи в `deferred_worker()` с проверками каждые 500ms
* **Traceback для ошибок** - добавлен полный стек вызовов при сбоях
* **Детальная проверка folder_paths** - диагностика каждого условия готовности

## [4.3.1] - 2025-01-29

### Enhanced
* **Arena AutoCache**: Автоматическое управление .env файлом
  * Автоматическое создание .env файла с полным списком категорий при первом запуске
  * Автоматическое дополнение .env при режиме "extend" с новыми категориями из ноды
  * Умная логика extend - система автоматически добавляет недостающие категории
  * Синхронизация между нодой и .env файлом
  * **Принцип приоритетов**: .env файл главный, нода только дополняет недостающие категории
  * **НЕ перезаписывает** существующие настройки в .env файле
  * Пользователю больше не нужно вручную редактировать .env файл

## [4.3.0] - 2025-01-29

### Added
- **Умные предустановленные категории** - автоматическое включение основных категорий моделей
- **checkpoints** - основные модели (CheckpointLoaderSimple, CheckpointLoader, Load Diffusion Model)
- **loras** - LoRA модели
- **clip** - CLIP модели (Load CLIP)
- **vae** - VAE модели
- **controlnet** - ControlNet модели
- **upscale_models** - модели апскейлинга
- **embeddings** - Embeddings
- **hypernetworks** - Hypernetworks
- **gguf_models** - GGUF модели (CLIPLoader GGUF, Unet loader GGUF)
- **unet_models** - UNet модели (UNETLoader, отдельные UNet компоненты)
- **diffusion_models** - Diffusion модели (Load Diffusion Model)

### Enhanced
- **Автоматическое обновление .env** - категории из ноды автоматически сохраняются в .env файл
- **Умная логика взаимодействия** - приоритет .env файла над предустановленными категориями
- **Упрощенное управление** - не нужно вручную добавлять основные категории моделей

### Changed
- **DEFAULT_WHITELIST** - обновлен с основными категориями моделей
- **Логика категорий** - улучшена обработка пустых .env файлов
- **Документация** - добавлен раздел о логике взаимодействия категорий

## [4.2.8] - 2025-01-27

### Fixed
- **Мгновенная загрузка настроек из .env файла** - нода теперь загружает настройки сразу при создании на канвасе
  - **Конструктор ноды** - добавлена загрузка .env файла в `__init__()` для мгновенного доступа
  - **Динамические значения по умолчанию** - `INPUT_TYPES()` теперь использует настройки из .env файла
  - **Производительность** - критично для тяжелых workflow с большими моделями (20+ GB)
  - **Тестирование** - создан тест для проверки мгновенной загрузки всех параметров

### Enhanced
- **Улучшена производительность** - настройки загружаются мгновенно без ожидания запуска Run
  - **Тяжелые workflow** - нода больше не ждет своей очереди после загрузки больших моделей
  - **Пользовательский опыт** - настройки видны сразу в интерфейсе ноды

## [4.2.7] - 2025-01-27

### Fixed
- **Исправлена загрузка настроек из .env файла** - нода теперь правильно подхватывает настройки из `user/arena_autocache.env`
  - **Приоритет настроек** - исправлена логика приоритетов: нода > .env > default
  - **Параметры по умолчанию** - если параметр ноды равен значению по умолчанию, используется значение из .env файла
  - **Явные параметры** - если параметр ноды отличается от значения по умолчанию, используется значение из ноды
  - **Тестирование** - добавлена проверка корректности загрузки всех параметров из .env файла

### Enhanced
- **Улучшена документация** - добавлены примеры работы приоритетов настроек
  - **Сценарии использования** - подробные примеры работы .env файла и ноды
  - **Объяснение логики** - четкое описание когда используются настройки из .env, а когда из ноды

## [4.2.6] - 2025-01-27

### Enhanced
- **Обновлены правила разработки** - усилен процесс работы с GitHub Issues
  - **ОБЯЗАТЕЛЬНОЕ создание Issue** - каждая задача начинается с создания Issue через MCP GitHub
  - **Строгий контроль закрытия** - Issue закрывается ТОЛЬКО после явного разрешения пользователя
  - **MCP GitHub tools** - все операции с GitHub исключительно через MCP tools
  - **Связка PR-Issue** - PR обязательно привязывается к Issue через "Closes #номер"
  - **Фиксация прогресса** - все шаги и комментарии фиксируются в Issue
  - **Исключения для мета-задач** - Issue НЕ создается для обновления правил, настройки инструментов, админ-задач
  - **Идеи на будущее** - AI предлагает 1-2 идеи с оценкой приоритета (0.0-1.0) и документирует их
  - **GitHub репозиторий** - добавлен в правила: `3dgopnik/comfyui-arena-suite` для быстрого поиска
  - **Очистка правил** - убран раздел "Общение" как не относящийся к процессу разработки
  - **Правило веток** - работа только в main, ветки создавать только для особо важных дел

### Changed
- **Правила процесса** - обновлен раздел "Рабочий процесс" в .cursor/rules/00-process.mdc
- **Code Review чек-лист** - добавлена проверка создания и закрытия Issue
- **GitHub интеграция** - усилена обязательность использования MCP для всех GitHub операций

## [4.2.5] - 2025-01-27

### Enhanced
- **Улучшенная поддержка .env файлов** - полная интеграция настроек из arena_autocache.env
  - **Приоритет настроек** - параметры ноды > .env файл > значения по умолчанию
  - **Автоматическая загрузка** - .env файл загружается при каждой инициализации ноды
  - **Валидация настроек** - проверка корректности значений с предупреждениями
  - **Поддержка всех параметров** - все настройки ноды могут быть заданы через .env

### Added
- **Валидация .env файлов** - проверка ключей и значений с подробными предупреждениями
- **Fallback логика** - умное применение настроек с правильными приоритетами
- **Расширенная документация** - подробное описание использования .env файлов
- **Тесты для .env функциональности** - покрытие всех сценариев загрузки настроек

### Changed
- **Версия ноды** обновлена до v4.2.5
- **Логика инициализации** - улучшенная обработка приоритетов настроек
- **Документация** - добавлены примеры использования .env файлов

## [4.2.4] - 2025-01-27

### Enhanced
- **Deferred autopatch** - отложенный автопатч для лучшей совместимости с ComfyUI
  - **Улучшенная совместимость** - автопатч применяется только при необходимости
  - **Безопасная инициализация** - предотвращение конфликтов при загрузке модулей
  - **Оптимизированная производительность** - патч применяется только когда это действительно нужно

### Changed
- **Версия ноды** обновлена до v4.2.4
- **Улучшенная совместимость** с различными версиями ComfyUI
- **Оптимизированная инициализация** для лучшей стабильности

## [4.1.0] - 2025-01-27

### Enhanced
- **Усиленная безопасность очистки кэша** - строгие проверки глубины путей для всех платформ
  - **Windows drive roots** - запрещены корни дисков (C:/) и одноуровневые пути (C:/cache)
  - **UNC paths** - запрещены //server/share и //server/share/one, требуется //server/share/arena/cache
  - **POSIX** - запрещены /, /mnt, /media, /Volumes без достаточной глубины
  - **Минимальная глубина ≥3** для всех платформ (C:/folder/subfolder, /var/tmp/arena)
  - **Улучшенное разрешение путей** - используется expanduser().resolve(strict=False)
  - **Дружественные сообщения** - "Clear aborted: drive root or path too shallow"

### Changed
- **Версия ноды** обновлена до v4.1.0
- **Документация** обновлена с новыми возможностями безопасности

## [4.0.0] - 2025-01-27

### Added
- **UI: 0 = unlimited для pruning** - max_cache_gb min изменён с 1.0 на 0.0
- **Safer defaults** - persist_env по умолчанию False, cache_categories по умолчанию ""
- **Remove redundant post-init reconfiguration** - убран блок повторной инициализации в run()
- **Clear: user-visible status passthrough** - run() возвращает точную строку из _clear_cache_folder()
- **Prune: add compact summary log** - добавлен summary лог после pruning
- **Tiny log/UX polish** - условные сообщения autopatch только при включении

### Changed
- **max_cache_gb default** изменён с 100.0 на 0.0 (unlimited по умолчанию)
- **persist_env default** изменён с True на False
- **cache_categories default** изменён с "checkpoints,loras" на ""

## [3.4.0] - 2025-01-27

### Added
- **Production-ready Arena AutoCache (simple)** - полностью переработанная нода с OnDemand режимом
  - **Корректная обработка .env файлов** - загрузка при импорте, умное сохранение с поддержкой удаления ключей
  - **Потокобезопасная дедупликация** - thread-safe операции с _scheduled_lock для исключения race conditions
  - **Безопасная очистка кэша** - множественные проверки безопасности, защита от удаления корневых директорий
  - **LRU-pruning до 95%** - умная очистка самых старых файлов по mtime при превышении лимита
  - **Автопатч при импорте** - критический порядок: сначала _load_env_file(), потом проверка флагов
  - **Подробное логирование** - все ключевые операции с детальной статистикой
  - **Cross-platform поддержка** - Windows (C:/ComfyUI/cache) и POSIX (~/.cache/comfyui/arena)

### Changed
- **Полная переработка arena_auto_cache_simple.py** - production-готовая архитектура
- **Улучшенная обработка .env** - поддержка удаления ключей, правильный порядок загрузки
- **Thread-safe операции** - все критические секции защищены локами
- **Безопасность** - проверки UNC/сетевых путей, глубины пути, корневых директорий

### Fixed
- **Исправлен порядок автопатча** - теперь работает корректно при наличии флага в .env файле
- **Устранены race conditions** - потокобезопасная работа с задачами копирования
- **Улучшена безопасность очистки** - защита от случайного удаления системных папок

## [3.3.5] - 2025-01-27

### Changed
- **Переименована Arena AutoCache** - v3.3.5 → Arena AutoCache Base
- **Базовая нода для модификации** - готова для дальнейшего развития
- **Упрощен интерфейс** - только 2 ноды: Arena AutoCache Base и Arena Make Tiles Segments

## [3.3.0] - 2025-01-27

### Added
- **Упрощенная Arena AutoCache v3.3.0-optimized** - только OnDemand режим кеширования
  - **OnDemand кеширование** - патч folder_paths + get_full_path для прозрачного кеширования при первом использовании
  - **Настройка категорий моделей** - параметр categories для выбора типов моделей для кеширования
  - **Настройка минимального размера файлов** - параметр min_size_mb для контроля порога кеширования
  - **Переменная окружения ARENA_CACHE_MIN_SIZE_MB** - возможность настройки через GitHub Actions
  - **Неблокирующее копирование** - асинхронное кеширование через фоновый поток
  - **Упрощенный интерфейс** - только 2 параметра: categories и min_size_mb
  - **Проверенная архитектура** - основана на решениях из arena_auto_cache_old.py

### Changed
- **Сокращение кода на 59.4%** - с 1500 до 609 строк
- **Удалено 10 неработающих методов** - API методы, direct методы, fallback логика
- **Сокращено отладочных сообщений на 84%** - с 142 до 23 сообщений
- **Упрощена обработка исключений на 78%** - с 42 до 9 обработчиков
- **Улучшена читаемость кода** - убраны дублирующиеся блоки и избыточная логика

### Removed
- **API методы поиска workflow** - `_get_workflow_via_api()`, `_get_canvas_workflow_via_api()`
- **Direct методы** - `_get_workflow_direct()`, `_get_current_workflow()`
- **Alternative методы** - `_get_workflow_alternative()`, `_analyze_current_canvas()`
- **Избыточные fallback методы** - множественные попытки получения workflow
- **Дублирующийся код** - повторяющиеся проверки типов и обработка исключений

### Fixed
- **Производительность** - убраны неработающие методы, оставлен только эффективный
- **Читаемость кода** - упрощена логика анализа workflow
- **Поддержка кода** - значительно упрощена структура и логика

## [3.2.0] - 2025-01-27

### Added
- **HTTP API метод для получения данных канваса** - `_get_canvas_workflow_via_api()`
- **Анализ workflow без Queue** - теперь нода может анализировать workflow с канваса через HTTP API
- **Fallback логика** - если API не работает, используются прямые методы

### Changed
- **Улучшена логика получения workflow** - сначала пробует HTTP API, затем прямые методы
- **Обновлены сообщения** - более точные описания того, откуда получен workflow

### Fixed
- **Работа без Queue** - теперь нода может работать с workflow на канвасе без запуска через Queue
- **Совместимость с Desktop** - HTTP API работает как в браузерной, так и в десктоп версии ComfyUI

## [3.1.5] - 2025-01-27

### Fixed
- **ComfyUI-Easy-Use Integration**: Enhanced support for ComfyUI-Easy-Use modules and prompt handling
- **Workflow File Detection**: Added support for user/default/workflows directory
- **Module Attribute Scanning**: Improved scanning of module attributes for workflow data
- **Workflow Data Extraction**: Better extraction from ComfyUI-Easy-Use prompt modules

### Changed
- **Module Processing**: Enhanced `_get_workflow_direct()` to better handle ComfyUI-Easy-Use modules
- **File Search**: Added user/default/workflows directory to workflow file search
- **Attribute Scanning**: Improved scanning of module attributes for workflow data
- **Error Handling**: Better handling of ComfyUI-Easy-Use modules

### Technical Details
- Enhanced ComfyUI-Easy-Use module detection in `_get_workflow_direct()`
- Added user/default/workflows directory to workflow file search patterns
- Improved module attribute scanning for workflow data extraction
- Enhanced error handling for ComfyUI-Easy-Use modules
- Added comprehensive attribute scanning for prompt modules

## [3.1.4] - 2025-01-27

### Fixed
- **Module Processing**: Enhanced module handling to extract workflow data from ComfyUI modules
- **Workflow Detection**: Improved extraction of nodes data from `comfy_execution.graph` module
- **Type Conversion**: Added module-to-dict conversion for better workflow analysis

### Changed
- **Module Handling**: Enhanced `_get_workflow_direct()` to better handle ComfyUI modules
- **Workflow Analysis**: Improved `_analyze_workflow_for_models()` to process module attributes
- **Error Handling**: Better handling of module objects in workflow data

### Technical Details
- Enhanced module processing in `_get_workflow_direct()` method
- Added module-to-dict conversion in `_analyze_workflow_for_models()`
- Improved extraction of nodes data from ComfyUI execution modules
- Added comprehensive attribute scanning for module objects
- Enhanced workflow data extraction from `comfy_execution.graph`

## [3.1.3] - 2025-01-27

### Fixed
- **Type Checking**: Fixed `object of type 'module' has no len()` error with proper isinstance() checks
- **Module Handling**: Improved handling of ComfyUI modules with proper type validation
- **Workflow Detection**: Streamlined to use only direct ComfyUI access (removed API dependency)

### Changed
- **API Approach**: Removed ComfyUI API dependency for better ComfyUI Electron compatibility
- **Error Handling**: Enhanced type checking for workflow data analysis
- **User Experience**: Simplified workflow detection to focus on direct ComfyUI access

### Technical Details
- Removed `_get_workflow_via_api()` method (no longer needed for ComfyUI Electron)
- Enhanced `_analyze_workflow_for_models()` with proper isinstance() checks
- Improved module handling in `_get_workflow_direct()` method
- Added comprehensive type validation for nodes data structures
- Streamlined workflow detection to use only direct ComfyUI access + file fallback

## [3.1.2] - 2025-01-27

### Added
- **Auto Port Detection**: Automatic scanning of common ComfyUI ports (8188, 8189, 8190, 8080, 8081, 3000, 5000)
- **Configurable API Settings**: Added `comfyui_port` and `comfyui_host` parameters to node
- **Flexible Port Detection**: Support for different ComfyUI ports and hosts
- **Environment Variables**: Support for `COMFYUI_PORT` and `COMFYUI_HOST` environment variables
- **Port Detection Documentation**: Added guide for finding ComfyUI port

### Changed
- **API Approach**: Switched from internal module access to ComfyUI API for workflow analysis
- **Reliability**: More reliable workflow detection using ComfyUI's HTTP API endpoints
- **Error Handling**: Better error messages and fallback strategies
- **User Experience**: Clearer feedback when workflow data is not available

### Technical Details
- Added `_get_workflow_direct()` method for direct ComfyUI module access (primary method)
- Added `_get_workflow_alternative()` method for file-based workflow detection (fallback)
- Removed dependency on ComfyUI API for better compatibility with ComfyUI Electron
- Enhanced error messages to guide users on proper usage
- Improved workflow data extraction reliability with proper type checking
- Added direct PromptServer access for ComfyUI Electron
- Fixed module handling errors with proper isinstance() checks
- Streamlined workflow detection to focus on direct ComfyUI access

## [3.1.1] - 2025-01-27

### Fixed
- **Module Handling**: Fixed `object of type 'module' has no len()` error when workflow data is a module
- **Workflow Analysis**: Improved handling of ComfyUI's `comfy_execution.graph` module objects
- **Node Extraction**: Enhanced extraction of nodes from module objects with proper type checking
- **Error Handling**: Better error handling for complex workflow data structures

### Technical Details
- Enhanced `_analyze_workflow_for_models()` to properly handle module objects
- Improved `_get_current_workflow()` to extract data from module attributes
- Added proper type checking for module vs dict/list objects
- Fixed workflow data extraction from ComfyUI's internal modules

## [3.1.0] - 2025-01-27

### Added
- **Workflow Analysis**: Automatic analysis of entire ComfyUI workflow to detect all model nodes
- **First-Run Cache Warming**: Cache warmup only triggers on first node execution per session
- **Comprehensive Model Detection**: Support for 20+ model node types including Checkpoint, VAE, LoRA, ControlNet, IP-Adapter, etc.
- **Async Cache Operations**: Non-blocking model copying with threading for better performance
- **Enhanced Logging**: Detailed progress logging with emoji indicators for better user experience
- **Force Warmup Option**: Ability to force cache warmup even if already completed in session
- **Session State Management**: Tracks completed warmups and analyzed models per session
- **Fallback Analysis**: Canvas analysis fallback when workflow data is unavailable
- **Test Suite**: Comprehensive test coverage for workflow analysis and model detection

### Changed
- **ArenaAutoCache Node**: Enhanced with workflow analysis and first-run logic
- **Model Detection**: Now analyzes entire workflow instead of just current canvas
- **Cache Strategy**: Pre-copies models from NAS to SSD before generation starts
- **Performance**: Asynchronous model copying to prevent blocking main thread
- **User Experience**: Clear progress indicators and detailed logging

### Technical Details
- Added `_analyze_workflow_for_models()` function for comprehensive workflow analysis
- Added `_get_model_category()` function for proper model categorization
- Added `_get_current_workflow()` function for workflow data retrieval
- Enhanced `_cache_models_with_progress()` with async copying and better logging
- Added session state variables `_session_warmup_completed` and `_session_models_analyzed`
- Added `force_warmup` parameter to bypass session state checks

## [3.0.0-alpha] - 2025-09-25

### Added
- Complete repository restart with clean structure
- ArenaAutoCacheSimple node for automatic model caching
- Web extensions for ComfyUI integration
- Comprehensive documentation and CI/CD setup
- Modern Python project structure with pyproject.toml

### Changed
- Migrated from legacy codebase to modern architecture
- Simplified node structure and API
- Updated documentation to reflect new structure

### Removed
- Legacy autocache implementation
- Outdated documentation and scripts
- Moved to clean, maintainable codebase

## [2.17.0] - 2025-09-24

### Fixed
- Fixed `_copy_into_cache_lru()` missing required positional argument 'category'
- Updated ArenaAutoCacheSmart to v2.17
- Improved error handling in cache operations

### Changed
- Enhanced cache management with better parameter handling
- Updated model caching workflow for better reliability

## [2.16.0] - 2025-09-23

### Added
- New ArenaAutoCacheSmart node with advanced caching features
- Support for multiple model types (checkpoints, loras, vaes, clips)
- Automatic cache directory management
- Progress tracking for cache operations

### Changed
- Improved cache performance and reliability
- Better error handling and user feedback
- Enhanced documentation and examples