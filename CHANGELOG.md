c:\ComfyUI\user\default\workflows\Test_lora_multiple.json# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.3.5] - 2025-01-27

### Changed
- **Обновлена версия Arena AutoCache** - v3.3.0 → v3.3.5
- **Добавлен эмодзи 🅰️** - для лучшей идентификации в ComfyUI
- **Упрощен интерфейс** - только 2 ноды: Arena AutoCache и Arena Make Tiles Segments

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