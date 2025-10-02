# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.13.0] - Wed Oct 02 2025 10:00:00 GMT+0300 (Москва, стандартное время)

### Удалено
- **Упрощенный интерфейс**: Удалены поля `cache_categories` и `categories_mode` из Python ноды
- **Ручное управление категориями**: Убрана необходимость вручную указывать категории моделей
- **Сложная логика категорий**: Удалены функции `_compute_effective_categories`, константы `DEFAULT_WHITELIST` и `KNOWN_CATEGORIES`

### Изменено
- **Автоматическое определение моделей**: Категории моделей теперь определяются автоматически через JavaScript анализ workflow
- **Упрощенная архитектура**: Убрана сложная логика взаимодействия между Python и .env файлами для категорий
- **Чистый интерфейс**: Нода стала проще и понятнее - JS автоматически анализирует workflow и определяет нужные модели

### Исправлено
- **Консистентность**: Приведена в соответствие концепция, где JS отвечает за анализ workflow
- **Упрощение**: Убрана дублирующая логика между Python и JavaScript

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