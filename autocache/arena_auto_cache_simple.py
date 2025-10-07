#!/usr/bin/env python3
"""
Arena AutoCache (simple) - Production-ready OnDemand-only node with robust env handling, thread-safety, safe pruning, and autopatch
RU: Production-готовая нода кэширования с надежной обработкой .env, потокобезопасностью, безопасной очисткой и автопатчингом
"""

import os
import shutil
import threading
import time
import json
import inspect
from dataclasses import dataclass
from pathlib import Path
from queue import Queue


@dataclass
class CacheSettings:
    """RU: Настройки кэширования."""

    root: Path
    min_size_mb: float
    max_cache_gb: float
    verbose: bool
    effective_categories: list[str]
    # Новые поля для demand-driven caching
    discovery_mode: str = "workflow_only"  # workflow_only | manual_only
    prefetch_strategy: str = "lazy"  # lazy | prefetch_allowlist
    max_concurrency: int = 2
    session_byte_budget: int = 0  # 0 = unlimited
    cooldown_ms: int = 5000


# RU: Глобальные настройки и состояние
_settings = None
_folder_paths_patched = False
_copy_queue = Queue()
_copy_thread_started = False
_deferred_autopatch_started = False
_scheduled_tasks: set[tuple[str, str]] = set()  # (category, filename)
_patch_lock = threading.Lock()
_scheduled_lock = threading.Lock()  # RU: Лок для дедупликации
_env_loaded = False  # RU: Флаг загрузки .env файла

# RU: Модели от JavaScript анализа workflow
_workflow_models: set[tuple[str, str]] = set()  # (category, filename)
_workflow_models_lock = threading.Lock()  # RU: Лок для моделей от workflow

# RU: Контроль системного сканирования
_startup_time = time.time()  # RU: Время старта для задержки
_last_copy_time = 0.0  # RU: Время последнего копирования для контроля частоты
_copy_frequency_limit = 1.0  # RU: Минимальный интервал между копированиями (секунды)

# RU: Live sync watcher
_env_watcher_thread = None
_env_watcher_running = False
_env_file_mtime = 0.0

# RU: Контроль demand-driven caching
_required_models: set[tuple[str, str]] = set()  # (category, filename)
_download_semaphore = None  # threading.Semaphore для лимита concurrency
_session_bytes_downloaded = 0
_last_autopatch_time = 0.0
_required_models_lock = threading.Lock()

# RU: Whitelist категорий для кэширования - основные категории моделей
DEFAULT_WHITELIST = [
    "checkpoints",      # RU: Основные модели (CheckpointLoaderSimple, CheckpointLoader, Load Diffusion Model)
    "loras",           # RU: LoRA модели
    "clip",            # RU: CLIP модели (Load CLIP)
    "vae",             # RU: VAE модели
    "controlnet",      # RU: ControlNet модели
    "upscale_models",  # RU: Модели апскейлинга
    "embeddings",      # RU: Embeddings
    "hypernetworks",   # RU: Hypernetworks
    "gguf_models",     # RU: GGUF модели (CLIPLoader GGUF, Unet loader GGUF)
    "unet_models",     # RU: UNet модели (UNETLoader, отдельные UNet компоненты)
    "diffusion_models", # RU: Diffusion модели (Load Diffusion Model)
]
KNOWN_CATEGORIES = [
    # RU: Основные категории моделей ComfyUI
    "checkpoints",
    "loras",
    "clip",
    "clip_vision",
    "text_encoders",
    "vae",
    "controlnet",
    "upscale_models",
    "embeddings",
    "hypernetworks",
    "ipadapter",
    "gligen",
    "animatediff_models",
    "t2i_adapter",
    "diffusion_models",
    "ultralytics",
    "insightface",
    "inpaint",
    "pix2pix",
    "sams",
    "pulid",
    # RU: Дополнительные категории из лога ComfyUI
    "llm",
    "ipadapter_encoders",
    "animatediff",
    "download_model_base",
    # RU: Специальные категории для GGUF и других форматов
    "gguf_models",
    "unet_models",
    "style_models",
    "flux_models",
    # RU: Категории для восстановления лиц и детекции
    "facerestore_models",
    "antelopev2",
    "bbox",
    "segm",
    # RU: Категории для апскейлинга
    "apisr",
    "stablesr",
    "supir",
    "ccsr",
    # RU: Категории для видео и анимации
    "video_models",
    "motion_models",
    "temporal_models",
]

# RU: Статистика копирования
_copy_status = {
    "total_jobs": 0,
    "completed_jobs": 0,
    "failed_jobs": 0,
    "current_file": "",
    "last_update": 0,
}


def _now() -> float:
    """RU: Текущее время в секундах."""
    return time.time()


def _ensure_env_loaded():
    """RU: Гарантирует загрузку .env файла (идемпотентно)."""
    global _env_loaded
    if not _env_loaded:
        _env_loaded = bool(_load_env_file())


# RU: Функция _compute_effective_categories удалена - категории определяются автоматически через JS анализ workflow


def _find_comfy_root():
    """RU: Находит корень ComfyUI, идя вверх от текущего файла."""
    current_path = Path(__file__).parent
    while current_path != current_path.parent:
        # RU: Ищем специфичные папки ComfyUI (models более надежный индикатор)
        if (current_path / "models").exists() or (
            (current_path / "web").exists() and (current_path / "custom_nodes").exists()
        ):
            return current_path
        current_path = current_path.parent
    
    # RU: Если не нашли, пробуем стандартные пути
    standard_paths = [
        Path("C:/ComfyUI"),
        Path("F:/ComfyUI"),
        Path("C:/Users/acherednikov/AppData/Local/Programs/@comfyorgcomfyui-electron/resources/ComfyUI")
    ]
    
    for path in standard_paths:
        if path.exists() and (path / "models").exists():
            return path
    
    return None


def _load_env_file():
    """RU: Загружает настройки из user/arena_autocache.env если файл существует."""
    comfy_root = _find_comfy_root()
    print(f"[ArenaAutoCache] DEBUG: Found ComfyUI root: {comfy_root}")
    if not comfy_root:
        print("[ArenaAutoCache] DEBUG: ComfyUI root not found!")
        return False

    # RU: Основной путь для .env файла
    env_file = comfy_root / "user" / "arena_autocache.env"
    
    # RU: Fallback для ComfyUI Desktop - поиск в AppData
    if not env_file.exists():
        appdata_path = Path(os.environ.get("APPDATA", "")) / "ComfyUI" / "logs" / "arena_autocache.env"
        if appdata_path.exists():
            print(f"[ArenaAutoCache] Found .env file in AppData: {appdata_path}")
            env_file = appdata_path
        else:
            print(f"[ArenaAutoCache] No .env file found - caching disabled by default")
            return False
    
    if env_file.exists():
        try:
            loaded_count = 0
            with open(env_file, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # RU: Валидация ключей
                        if not key or not value:
                            print(f"[ArenaAutoCache] Warning: Empty key or value in {env_file}:{line_num}")
                            continue
                            
                        # RU: Валидация известных ключей
                        known_keys = {
                            "ARENA_CACHE_ROOT", "ARENA_CACHE_MIN_SIZE_MB", "ARENA_CACHE_MAX_GB",
                            "ARENA_CACHE_VERBOSE", "ARENA_CACHE_CATEGORIES", "ARENA_CACHE_CATEGORIES_MODE",
                            "ARENA_CACHE_MODE", "ARENA_AUTO_CACHE_ENABLED", "ARENA_AUTOCACHE_AUTOPATCH",
                            "ARENA_CACHE_DISCOVERY", "ARENA_CACHE_PREFETCH_STRATEGY", "ARENA_CACHE_MAX_CONCURRENCY",
                            "ARENA_CACHE_SESSION_BYTE_BUDGET", "ARENA_CACHE_COOLDOWN_MS"
                        }
                        
                        if key not in known_keys:
                            print(f"[ArenaAutoCache] Warning: Unknown key '{key}' in {env_file}:{line_num}")
                        
                        # RU: Валидация значений для числовых параметров
                        if key in ("ARENA_CACHE_MIN_SIZE_MB", "ARENA_CACHE_MAX_GB"):
                            try:
                                float(value)
                            except ValueError:
                                print(f"[ArenaAutoCache] Warning: Invalid numeric value '{value}' for {key} in {env_file}:{line_num}")
                                continue
                        
                        # RU: Валидация булевых значений
                        if key in ("ARENA_CACHE_VERBOSE", "ARENA_AUTO_CACHE_ENABLED", "ARENA_AUTOCACHE_AUTOPATCH"):
                            if value.lower() not in ("true", "false", "1", "0", "yes", "no"):
                                print(f"[ArenaAutoCache] Warning: Invalid boolean value '{value}' for {key} in {env_file}:{line_num}")
                        
                        # RU: Валидация режима кэширования
                        if key == "ARENA_CACHE_MODE":
                            if value.lower() not in ("ondemand", "disabled"):
                                print(f"[ArenaAutoCache] Warning: Invalid cache mode '{value}' for {key} in {env_file}:{line_num} (valid: ondemand, disabled)")
                        
                        os.environ[key] = value
                        loaded_count += 1
            
            if loaded_count > 0:
                print(f"[ArenaAutoCache] Loaded {loaded_count} settings from {env_file}")
                return True
            else:
                print(f"[ArenaAutoCache] No valid settings found in {env_file}")
                return False
                
        except Exception as e:
            print(f"[ArenaAutoCache] Error loading env file: {e}")
            return False
    
    return False


def _save_env_file(kv: dict[str, str], remove_keys: list[str] = None):
    """RU: Сохраняет настройки в user/arena_autocache.env с поддержкой удаления ключей."""
    try:
        comfy_root = _find_comfy_root()
        if not comfy_root:
            return

        env_dir = comfy_root / "user"
        env_dir.mkdir(exist_ok=True)
        env_file = env_dir / "arena_autocache.env"

        # RU: Читаем существующие настройки
        existing_settings = {}
        if env_file.exists():
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        existing_settings[key.strip()] = value.strip()

        # RU: Обновляем настройки (только непустые значения)
        for key, value in kv.items():
            if value:  # RU: Не записываем пустые значения
                existing_settings[key] = value

        # RU: Удаляем указанные ключи
        if remove_keys:
            for key in remove_keys:
                existing_settings.pop(key, None)

        # RU: Записываем обратно
        with open(env_file, "w", encoding="utf-8") as f:
            f.write("# Arena AutoCache Environment Settings\n")
            f.write("# Generated automatically - do not edit manually\n\n")
            for key, value in existing_settings.items():
                f.write(f"{key}={value}\n")

        print(f"[ArenaAutoCache] Saved env to {env_file}")
    except Exception as e:
        print(f"[ArenaAutoCache] Error saving env file: {e}")


def _init_settings(
    cache_root: str = "",
    min_size_mb: float = 10.0,
    max_cache_gb: float = 0.0,
    verbose: bool = False,
) -> CacheSettings:
    """RU: Инициализирует настройки кэширования с резолвингом путей по умолчанию."""
    global _settings

    # RU: Загружаем .env файл при каждой инициализации для актуальности настроек
    _load_env_file()


    # RU: Приоритет настроек: параметры ноды > .env файл > значения по умолчанию
    # RU: Если параметр ноды пустой/по умолчанию, используем значение из .env
    
    # RU: Cache root - приоритет: нода > .env > default
    # RU: Если cache_root пустой или None, используем .env
    if not cache_root or cache_root.strip() == "":
        env_cache_root = os.environ.get("ARENA_CACHE_ROOT", "")
        if env_cache_root:
            cache_root = env_cache_root
    
    # RU: Min size - приоритет: нода > .env > default (10.0)
    if min_size_mb == 10.0:  # RU: Значение по умолчанию
        env_min_size = os.environ.get("ARENA_CACHE_MIN_SIZE_MB", "")
        if env_min_size:
            try:
                min_size_mb = float(env_min_size)
            except ValueError:
                print(f"[ArenaAutoCache] Invalid ARENA_CACHE_MIN_SIZE_MB: {env_min_size}, using default 10.0")
                min_size_mb = 10.0
    
    # RU: Max cache size - приоритет: нода > .env > default (0.0)
    if max_cache_gb == 0.0:  # RU: Значение по умолчанию
        env_max_cache = os.environ.get("ARENA_CACHE_MAX_GB", "")
        if env_max_cache:
            try:
                max_cache_gb = float(env_max_cache)
            except ValueError:
                print(f"[ArenaAutoCache] Invalid ARENA_CACHE_MAX_GB: {env_max_cache}, using default 0.0")
                max_cache_gb = 0.0
    
    # RU: Verbose - приоритет: нода > .env > default (True)
    # RU: Всегда проверяем .env файл, если в ноде не указано явно
    env_verbose = os.environ.get("ARENA_CACHE_VERBOSE", "")
    if env_verbose:
        verbose = env_verbose.lower() in ("true", "1", "yes")
    
    # RU: Резолвим корень кэша (приоритет: параметр ноды > env переменная > default)
    if cache_root and cache_root.strip():
        # RU: Если в ноде указан путь - используем его
        root = Path(cache_root)
        if verbose:
            print(f"[ArenaAutoCache] Using cache root from node: {root}")
    else:
        # RU: Определяем корень ComfyUI для относительных путей
        comfy_root = _find_comfy_root()
        if comfy_root:
            default_root = comfy_root / "models" / "arena_cache"
        else:
            default_root = Path.home() / "Documents" / "ComfyUI-Cache"
        root = Path(os.environ.get("ARENA_CACHE_ROOT", default_root))
        if verbose:
            print(f"[ArenaAutoCache] Using cache root from .env/default: {root}")
    
    # RU: Создаем папку кэша
    root.mkdir(parents=True, exist_ok=True)
    
    # RU: Используем базовые категории - JS автоматически определяет нужные модели
    base_categories = [
        "checkpoints", "loras", "clip", "vae", "controlnet", "upscale_models", 
        "embeddings", "hypernetworks", "gguf_models", "unet_models", "diffusion_models",
        "text_encoders"  # RU: Добавляем text_encoders для DualCLIPLoader
    ]
    
    # RU: Создаем подпапки для базовых категорий
    for category in base_categories:
        (root / category).mkdir(exist_ok=True)
    
    # RU: Читаем новые параметры для demand-driven caching
    discovery_mode = os.environ.get("ARENA_CACHE_DISCOVERY", "workflow_only")
    prefetch_strategy = os.environ.get("ARENA_CACHE_PREFETCH_STRATEGY", "lazy")
    max_concurrency = int(os.environ.get("ARENA_CACHE_MAX_CONCURRENCY", "2"))
    session_byte_budget = int(os.environ.get("ARENA_CACHE_SESSION_BYTE_BUDGET", "0"))
    cooldown_ms = int(os.environ.get("ARENA_CACHE_COOLDOWN_MS", "5000"))
    
    _settings = CacheSettings(
        root=root,
        min_size_mb=min_size_mb,
        max_cache_gb=max_cache_gb,
        verbose=verbose,
        effective_categories=base_categories,
        discovery_mode=discovery_mode,
        prefetch_strategy=prefetch_strategy,
        max_concurrency=max_concurrency,
        session_byte_budget=session_byte_budget,
        cooldown_ms=cooldown_ms,
    )
    
    
    if verbose:
        print(
            f"[ArenaAutoCache] Cache root: {root} / Min file size: {min_size_mb}MB / Max cache size: {max_cache_gb}GB / Verbose: {verbose}"
        )
    
    return _settings


def _apply_folder_paths_patch():
    """RU: Применяет патч folder_paths для перехвата загрузки моделей."""
    global _folder_paths_patched

    with _patch_lock:
        if _folder_paths_patched:
            return

    try:
        import folder_paths

        # RU: Сохраняем оригинальные функции
        original_get_folder_paths = folder_paths.get_folder_paths
        original_get_full_path = folder_paths.get_full_path

        # RU: Создаем алиас для оригинальной функции
        if not hasattr(folder_paths, "get_full_path_origin"):
            folder_paths.get_full_path_origin = original_get_full_path

        def patched_get_folder_paths(folder_name: str) -> list[str]:
            """RU: Патченная функция get_folder_paths БЕЗ добавления кэша."""
            # RU: НЕ добавляем кеш-пути в список - это ломает логику!
            # RU: ComfyUI должен искать в оригинальных путях, а мы перехватываем в get_full_path
            return original_get_folder_paths(folder_name)

        def patched_get_full_path(folder_name: str, filename: str) -> str:
            """RU: Патченная функция get_full_path с кэшированием."""
            print(f"[ArenaAutoCache] patched_get_full_path called: {folder_name} -> {filename}")
            
            # RU: Диагностика для всех моделей в verbose режиме
            if _settings and _settings.verbose:
                print(f"[ArenaAutoCache] Model requested: {folder_name}/{filename}")
                print(f"[ArenaAutoCache] Stack trace:")
                import traceback
                traceback.print_stack()
            
            # RU: Кэширование только для эффективных категорий
            if folder_name in _settings.effective_categories:
                print(f"[ArenaAutoCache] Category {folder_name} is in effective_categories")
                if _settings and _settings.verbose:
                    print(f"[ArenaAutoCache] Effective categories: {_settings.effective_categories}")
                # RU: Сначала проверяем кэш
                cache_path = _settings.root / folder_name / filename
                if cache_path.exists():
                    if _settings.verbose:
                        print(f"[ArenaAutoCache] Cache hit: {filename}")
                    return str(cache_path)

                # RU: Если не в кэше, получаем оригинальный путь
                try:
                    original_path = folder_paths.get_full_path_origin(folder_name, filename)
                    if os.path.exists(original_path):
                        # RU: Планируем копирование в фоне ТОЛЬКО если включено авто-кеширование
                        auto_cache_enabled = os.environ.get("ARENA_AUTO_CACHE_ENABLED", "false").lower() in ("true", "1", "yes")
                        print(f"[ArenaAutoCache] auto_cache_enabled: {auto_cache_enabled}")
                        
                        # RU: Проверяем системное сканирование
                        is_system_scan = _is_system_scanning()
                        print(f"[ArenaAutoCache] is_system_scanning: {is_system_scan}")
                        
                        if auto_cache_enabled and not is_system_scan:
                            _schedule_copy_task(folder_name, filename, original_path, str(cache_path))
                            if _settings.verbose:
                                print(f"[ArenaAutoCache] Scheduled cache copy: {filename}")
                        else:
                            if _settings.verbose:
                                print(f"[ArenaAutoCache] Auto-caching disabled, using original: {filename}")
                        return original_path
                except Exception as e:
                    if _settings.verbose:
                        print(f"[ArenaAutoCache] Error getting original path: {e}")

            # RU: Для неэффективных категорий используем оригинальную функцию
            return original_get_full_path(folder_name, filename)

        # RU: Применяем патчи
        folder_paths.get_folder_paths = patched_get_folder_paths
        folder_paths.get_full_path = patched_get_full_path

        _folder_paths_patched = True
        print("[ArenaAutoCache] Applied folder_paths patch")

    except Exception as e:
        print(f"[ArenaAutoCache] Error applying folder_paths patch: {e}")


def _is_system_scanning() -> bool:
    """RU: Детектирует системное сканирование по стеку вызовов."""
    try:
        # RU: Получаем текущий стек вызовов
        frame = inspect.currentframe()
        call_stack = []
        
        # RU: Собираем стек вызовов (максимум 15 уровней)
        for _ in range(15):
            if frame is None:
                break
            call_stack.append(frame.f_code.co_name)
            frame = frame.f_back
        
        # RU: Ищем признаки системного сканирования (точные имена)
        system_indicators = {
            'load_checkpoint_guess_config',  # RU: ComfyUI загрузка конфигурации
            'load_checkpoint',              # RU: ComfyUI загрузка чекпоинта
            'load_lora',                    # RU: ComfyUI загрузка LoRA
            'load_vae',                     # RU: ComfyUI загрузка VAE
            'load_controlnet',              # RU: ComfyUI загрузка ControlNet
            'load_upscale_model',           # RU: ComfyUI загрузка модели апскейлинга
            'scan_directory',               # RU: Сканирование директории
            'get_folder_paths',             # RU: Получение путей папок
            'list_files',                   # RU: Список файлов
            'scan_models',                  # RU: Сканирование моделей
            'folder_paths',                 # RU: Работа с путями папок
            'model_management',             # RU: Управление моделями
            'extra_model_paths',            # RU: Дополнительные пути моделей
        }
        
        # RU: Ищем признаки реального использования моделей
        real_usage_indicators = {
            'execute',                      # RU: Выполнение workflow
            'run',                          # RU: Запуск ноды
            'forward',                      # RU: Forward pass
            'load_state_dict',             # RU: Загрузка весов модели
            'from_pretrained',             # RU: Загрузка предобученной модели
            'DualCLIPLoader',              # RU: DualCLIPLoader нода
            'FluxClipModel',               # RU: FluxClipModel нода
            'QuadrupleCLIPLoader',         # RU: QuadrupleCLIPLoader нода
            'T5TextEncoder',               # RU: T5TextEncoder нода
            'CLIPTextEncoder',             # RU: CLIPTextEncoder нода
            'VAELoader',                   # RU: VAE нода
            'VAELoaderModelOnly',          # RU: VAE нода только модель
            'CheckpointLoader',            # RU: Checkpoint нода
            'CheckpointLoaderSimple',      # RU: Checkpoint нода простая
            'LoraLoader',                  # RU: LoRA нода
            'ControlNetLoader',            # RU: ControlNet нода
            'UpscaleLoader',               # RU: Upscale нода
        }
        
        # RU: Проверяем наличие индикаторов реального использования (приоритет)
        if any(call in real_usage_indicators for call in call_stack):
            if _settings and _settings.verbose:
                print(f"[ArenaAutoCache] Real usage detected, allowing caching: {[call for call in call_stack if call in real_usage_indicators]}")
            return False
        
        # RU: Проверяем наличие системных индикаторов в стеке (точное совпадение)
        if any(call in system_indicators for call in call_stack):
            if _settings and _settings.verbose:
                print(f"[ArenaAutoCache] System scanning detected: {[call for call in call_stack if call in system_indicators]}")
            return True
        
        # RU: Дополнительная проверка - если стек содержит только системные вызовы
        if len(call_stack) > 5:
            system_calls = sum(1 for call in call_stack if call in system_indicators)
            if system_calls > len(call_stack) * 0.7:  # RU: Если 70%+ вызовов системные
                if _settings and _settings.verbose:
                    print(f"[ArenaAutoCache] High system call ratio detected: {system_calls}/{len(call_stack)}")
                return True
                
        return False
        
    except Exception as e:
        # RU: В случае ошибки считаем, что это системное сканирование (безопаснее)
        if _settings and _settings.verbose:
            print(f"[ArenaAutoCache] Error in _is_system_scanning: {e}, defaulting to system scanning")
        return True


def _is_startup_phase() -> bool:
    """RU: Проверяет, находимся ли мы в фазе старта (первые 60 секунд)."""
    return time.time() - _startup_time < 60.0

def _is_startup_phase_aggressive() -> bool:
    """RU: Проверяет агрессивную фазу старта (отключено для параллельного кеширования)."""
    # RU: Отключаем фазу старта для параллельного кеширования
    return False

def _has_real_usage_indicators() -> bool:
    """RU: Проверяет наличие индикаторов реального использования в стеке вызовов."""
    try:
        frame = inspect.currentframe()
        call_stack = []
        
        # RU: Собираем стек вызовов (максимум 10 уровней)
        for _ in range(10):
            if frame is None:
                break
            call_stack.append(frame.f_code.co_name)
            frame = frame.f_back
        
        # RU: Индикаторы реального использования
        real_usage_indicators = {
            'execute', 'run', 'forward', 'load_state_dict', 'from_pretrained',
            'DualCLIPLoader', 'FluxClipModel', 'QuadrupleCLIPLoader', 'T5TextEncoder', 'CLIPTextEncoder',
            'VAELoader', 'VAELoaderModelOnly', 'CheckpointLoader', 'CheckpointLoaderSimple',
            'LoraLoader', 'ControlNetLoader', 'UpscaleLoader'
        }
        
        # RU: Проверяем наличие индикаторов реального использования
        return any(call in real_usage_indicators for call in call_stack)
        
    except Exception:
        return False

def _is_frequency_limited_aggressive() -> bool:
    """RU: Проверяет агрессивное ограничение частоты (отключено для параллельного кеширования)."""
    # RU: Отключаем частотный лимит для параллельного кеширования
    return False


def _is_frequency_limited() -> bool:
    """RU: Проверяет, не превышена ли частота копирования."""
    current_time = time.time()
    return current_time - _last_copy_time < _copy_frequency_limit


def _has_active_arena_nodes() -> bool:
    """RU: Проверяет, есть ли активные ноды Arena на канвасе."""
    try:
        # RU: Пытаемся импортировать ComfyUI модули для проверки активных нод
        import sys
        
        # RU: Ищем модули ComfyUI в sys.modules
        comfyui_modules = [name for name in sys.modules.keys() if 'comfy' in name.lower()]
        
        # RU: Если ComfyUI не загружен, считаем что нод нет
        if not comfyui_modules:
            return False
            
        # RU: Проверяем наличие активных workflow или нод
        # RU: Это упрощенная проверка - в реальности нужно анализировать текущий workflow
        # RU: Пока что возвращаем True, чтобы не блокировать кеширование
        return True
        
    except Exception:
        # RU: В случае ошибки считаем, что ноды есть
        return True


def _reload_settings_if_needed():
    """RU: Перезагружает настройки если .env файл изменился."""
    global _settings
    
    if not _settings:
        return
        
    # RU: Проверяем, есть ли .env файл сейчас
    comfy_root = _find_comfy_root()
    if not comfy_root:
        return
        
    # RU: Основной путь для .env файла
    env_file = comfy_root / "user" / "arena_autocache.env"
    
    # RU: Fallback для ComfyUI Desktop - поиск в AppData
    if not env_file.exists():
        appdata_path = Path(os.environ.get("APPDATA", "")) / "ComfyUI" / "logs" / "arena_autocache.env"
        if appdata_path.exists():
            env_file = appdata_path
    
    # RU: Если .env файл появился или обновился, перезагружаем настройки
    if env_file.exists():
        print("[ArenaAutoCache] .env file detected, reloading settings...")
        _load_env_file()
        
        # RU: Перезагружаем настройки с учетом .env файла
        cache_root = os.environ.get("ARENA_CACHE_ROOT", "")
        min_size_mb = float(os.environ.get("ARENA_CACHE_MIN_SIZE_MB", "10.0"))
        max_cache_gb = float(os.environ.get("ARENA_CACHE_MAX_GB", "512.0"))
        verbose = os.environ.get("ARENA_CACHE_VERBOSE", "false").lower() in ("true", "1", "yes")
        
        if cache_root:
            _settings = CacheSettings(
                root=Path(cache_root),
                min_size_mb=min_size_mb,
                max_cache_gb=max_cache_gb,
                verbose=verbose,
                effective_categories=_settings.effective_categories
            )
            print(f"[ArenaAutoCache] Settings reloaded from .env: {cache_root}")


def _schedule_copy_task(category: str, filename: str, source_path: str, cache_path: str):
    """RU: Планирует задачу копирования с дедупликацией и фильтрацией."""
    global _last_copy_time
    
    # RU: ПРИОРИТЕТ КЕШИРОВАНИЯ - разрешаем кеширование по умолчанию
    
    # RU: 1. Проверяем системное сканирование (только если НЕ реальное использование)
    is_system_scanning = _is_system_scanning()
    if is_system_scanning:
        # RU: Проверяем, есть ли признаки реального использования
        real_usage_detected = _has_real_usage_indicators()
        if not real_usage_detected:
            if _settings and _settings.verbose:
                print(f"[ArenaAutoCache] Blocked by system scanning: {category}/{filename}")
            return  # RU: Блокируем только чистое системное сканирование
        else:
            if _settings and _settings.verbose:
                print(f"[ArenaAutoCache] Real usage detected, allowing despite system scanning: {category}/{filename}")
    
    # RU: 2. Проверяем фазу старта (только для первых 30 секунд)
    if _is_startup_phase_aggressive():
        if _settings and _settings.verbose:
            print(f"[ArenaAutoCache] Blocked by aggressive startup phase: {category}/{filename}")
        return  # RU: Блокируем только первые 30 секунд
    
    # RU: 3. Проверяем частоту копирования (только если слишком часто)
    if _is_frequency_limited_aggressive():
        if _settings and _settings.verbose:
            print(f"[ArenaAutoCache] Blocked by aggressive frequency limit: {category}/{filename}")
        return  # RU: Блокируем только при очень частых вызовах
    
    # RU: Перезагружаем настройки если .env файл появился
    _reload_settings_if_needed()
    
    # RU: Fallback: если настройки не загружены, используем настройки по умолчанию
    if not _settings:
        return  # RU: Молча блокируем без логов
    
    # RU: Проверяем, включено ли кеширование
    auto_cache_enabled = os.environ.get("ARENA_AUTO_CACHE_ENABLED", "false").lower() in ("true", "1", "yes")
    if not auto_cache_enabled:
        return  # RU: Молча блокируем без логов
    
    # RU: Проверяем наличие активных нод Arena
    if not _has_active_arena_nodes():
        return  # RU: Молча блокируем без логов
    
    # RU: Обновляем время последнего копирования
    _last_copy_time = time.time()
    
    with _scheduled_lock:
        task_key = (category, filename)
        if task_key in _scheduled_tasks:
            return
        _scheduled_tasks.add(task_key)

    _copy_queue.put((category, filename, source_path, cache_path))
    if _settings.verbose:
        print(f"[ArenaAutoCache] Scheduled cache copy: {filename}")


def _copy_worker():
    """RU: Фоновый воркер для копирования файлов."""
    global _copy_status

    while True:
        try:
            category, filename, source_path, cache_path = _copy_queue.get()

            _copy_status["current_file"] = filename
            _copy_status["total_jobs"] += 1

            try:
                # RU: Проверяем размер файла
                source_size = os.path.getsize(source_path)
                if source_size < _settings.min_size_mb * 1024 * 1024:
                    if _settings.verbose:
                        print(
                            f"[ArenaAutoCache] Skipping {filename}: too small ({source_size / 1024 / 1024:.1f}MB)"
                        )
                    _copy_queue.task_done()
                    with _scheduled_lock:
                        _scheduled_tasks.discard((category, filename))
                    continue

                # RU: Проверяем, не существует ли уже в кэше
                if os.path.exists(cache_path):
                    if _settings.verbose:
                        print(f"[ArenaAutoCache] Already cached: {filename}")
                    _copy_queue.task_done()
                    with _scheduled_lock:
                        _scheduled_tasks.discard((category, filename))
                    continue

                # RU: Создаем папку кэша
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)

                # RU: Копируем файл
                temp_path = cache_path + ".part"
                shutil.copy2(source_path, temp_path)
                os.rename(temp_path, cache_path)

                _copy_status["completed_jobs"] += 1
                if _settings.verbose:
                    print(f"[ArenaAutoCache] Cached: {filename}")

                # RU: Проверяем размер кэша и очищаем при необходимости
                _prune_cache_if_needed()

            except Exception as e:
                _copy_status["failed_jobs"] += 1
                if _settings.verbose:
                    print(f"[ArenaAutoCache] Error caching {filename}: {e}")

            _copy_queue.task_done()
            with _scheduled_lock:
                _scheduled_tasks.discard((category, filename))

        except Exception as e:
            if _settings and _settings.verbose:
                print(f"[ArenaAutoCache] Copy worker error: {e}")
            continue


# RU: Функция _eager_cache_all_models удалена - режим eager опасен для дискового пространства


def _prune_cache_if_needed():
    """RU: Очищает кэш при превышении лимита (LRU)."""
    try:
        # RU: Проверяем, включен ли лимит
        if _settings.max_cache_gb <= 0:
            return

        # RU: Получаем размер кэша (рекурсивно)
        total_size = 0
        all_files = []

        for category in _settings.effective_categories:
            category_path = _settings.root / category
            if category_path.exists():
                for file_path in category_path.rglob("*"):
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        total_size += size
                        all_files.append((file_path, size, file_path.stat().st_mtime))

        # RU: Проверяем лимит
        max_size_bytes = _settings.max_cache_gb * 1024 * 1024 * 1024
        if total_size > max_size_bytes:
            # RU: Сортируем по времени модификации (LRU)
            all_files.sort(key=lambda x: x[2])

            # RU: Удаляем файлы до 95% лимита
            target_size = max_size_bytes * 0.95
            current_size = total_size
            pruned_files = 0
            freed_bytes = 0

            for file_path, size, _ in all_files:
                if current_size <= target_size:
                    break

                try:
                    file_path.unlink()
                    current_size -= size
                    pruned_files += 1
                    freed_bytes += size
                    if _settings.verbose:
                        print(f"[ArenaAutoCache] Pruned: {file_path.name}")
                except Exception as e:
                    if _settings.verbose:
                        print(f"[ArenaAutoCache] Error pruning {file_path.name}: {e}")

            # RU: Summary лог для prune
            if pruned_files > 0:
                freed_mb = freed_bytes / 1024 / 1024
                print(
                    f"[ArenaAutoCache] Pruned {pruned_files} files; freed {freed_mb:.1f} MB (target ~95%)"
                )

    except Exception as e:
        if _settings.verbose:
            print(f"[ArenaAutoCache] Error pruning cache: {e}")


def _is_folder_paths_ready():
    """RU: Проверяет готовность folder_paths для патчинга."""
    try:
        import folder_paths
        
        # RU: Диагностические проверки
        has_get_folder_paths = hasattr(folder_paths, "get_folder_paths")
        has_get_full_path = hasattr(folder_paths, "get_full_path")
        has_folder_names_and_paths = hasattr(folder_paths, "folder_names_and_paths")
        folder_names_and_paths_len = len(folder_paths.folder_names_and_paths) if has_folder_names_and_paths else 0
        has_get_full_path_origin = hasattr(folder_paths, "get_full_path_origin")
        
        is_ready = (
            has_get_folder_paths
            and has_get_full_path
            and has_folder_names_and_paths
            and folder_names_and_paths_len > 0
            and not has_get_full_path_origin
        )
        
        # RU: Подробная диагностика
        if not is_ready:
            print(f"[ArenaAutoCache] folder_paths not ready: get_folder_paths={has_get_folder_paths}, get_full_path={has_get_full_path}, folder_names_and_paths={has_folder_names_and_paths}, len={folder_names_and_paths_len}, has_origin={has_get_full_path_origin}")
        
        return is_ready
    except Exception as e:
        print(f"[ArenaAutoCache] Error checking folder_paths readiness: {e}")
        return False


def _get_autopatch_status():
    """RU: Возвращает текущий статус автопатча."""
    return {
        "started": _deferred_autopatch_started,
        "patched": _folder_paths_patched,
        "copy_worker_running": _copy_thread_started,
        "settings_initialized": _settings is not None
    }


def _start_deferred_autopatch():
    """RU: Запускает отложенный автопатч в отдельном потоке."""
    global _deferred_autopatch_started

    if _deferred_autopatch_started:
        print("[ArenaAutoCache] Deferred autopatch already started, skipping")
        return

    _deferred_autopatch_started = True
    print("[ArenaAutoCache] Starting deferred autopatch - waiting for ComfyUI to be ready...")

    def deferred_worker():
        import time

        timeout_s = int(os.environ.get("ARENA_AUTOCACHE_AUTOPATCH_TIMEOUT_S", "90"))
        poll_ms = int(os.environ.get("ARENA_AUTOCACHE_AUTOPATCH_POLL_MS", "500"))

        start_time = time.time()
        print(f"[ArenaAutoCache] Deferred worker started - timeout: {timeout_s}s, poll: {poll_ms}ms")

        while time.time() - start_time < timeout_s:
            elapsed = time.time() - start_time
            is_ready = _is_folder_paths_ready()
            print(f"[ArenaAutoCache] Check #{int(elapsed * 1000 / poll_ms) + 1}: folder_paths ready = {is_ready} (elapsed: {elapsed:.1f}s)")
            
            if is_ready:
                try:
                    global _settings, _copy_thread_started
                    print("[ArenaAutoCache] folder_paths is ready, initializing settings...")
                    _settings = _init_settings()
                    
                    if not _folder_paths_patched:
                        print("[ArenaAutoCache] Applying folder_paths patch...")
                        _apply_folder_paths_patch()
                    else:
                        print("[ArenaAutoCache] folder_paths already patched")

                    # RU: Запускаем воркер копирования
                    if not _copy_thread_started:
                        print("[ArenaAutoCache] Starting copy worker thread...")
                        copy_thread = threading.Thread(target=_copy_worker, daemon=True)
                        copy_thread.start()
                        _copy_thread_started = True
                    else:
                        print("[ArenaAutoCache] Copy worker already started")

                    elapsed = time.time() - start_time
                    print(f"[ArenaAutoCache] ✅ Deferred autopatch applied successfully after {elapsed:.1f}s")
                    return
                except Exception as e:
                    print(f"[ArenaAutoCache] ❌ Deferred autopatch failed: {e}")
                    import traceback
                    traceback.print_exc()
                    return

            time.sleep(poll_ms / 1000.0)

        print("[ArenaAutoCache] ⏰ Deferred autopatch timed out; will patch on first node run")

    threading.Thread(target=deferred_worker, daemon=True).start()


def _ensure_patch_applied():
    """RU: Идемпотентно применяет патч при первом использовании ноды."""
    global _settings, _copy_thread_started

    if _folder_paths_patched:
        return

    try:
        _settings = _init_settings()
        _apply_folder_paths_patch()

        # RU: Запускаем воркер копирования
        if not _copy_thread_started:
            copy_thread = threading.Thread(target=_copy_worker, daemon=True)
            copy_thread.start()
            _copy_thread_started = True

        print("[ArenaAutoCache] Patched on first node use")
    except Exception as e:
        print(f"[ArenaAutoCache] Failed to patch on first node use: {e}")


def _clear_cache_folder():
    """RU: Очищает папку кэша с безопасными проверками."""
    try:
        if not _settings.root.exists():
            return "Cache cleared: 0.0 MB freed (no cache found)"

        # RU: Проверяем безопасность пути
        try:
            cache_path = _settings.root.expanduser().resolve(strict=False)
        except Exception:
            return "Cache cleared: 0.0 MB freed (path resolution failed)"

        # RU: Проверяем Windows drive roots и глубину
        if os.name == "nt":  # Windows
            # RU: Проверяем корни дисков через Path.drive
            if cache_path.drive and len(cache_path.parts) < 3:
                return "Clear aborted: drive root or path too shallow"

            # RU: Проверяем UNC paths (двойной backslash)
            if str(cache_path).startswith("\\\\"):
                parts = str(cache_path).split("\\")
                if len(parts) <= 4:  # \\server\share or \\server\share\one
                    return "Clear aborted: drive root or path too shallow"

            # RU: Требуем минимум C:/folder/subfolder (≥3 parts)
            if len(cache_path.parts) < 3:
                return "Clear aborted: drive root or path too shallow"

        # RU: Проверяем POSIX
        else:  # POSIX
            # RU: Запрещаем корень и mount roots без достаточной глубины
            forbidden_roots = {"/", "/mnt", "/media", "/Volumes"}
            if str(cache_path) in forbidden_roots:
                return "Clear aborted: drive root or path too shallow"

            # RU: Требуем минимум /var/tmp/arena (≥3 parts)
            if len(cache_path.parts) < 3:
                return "Clear aborted: drive root or path too shallow"

        # RU: Подсчитываем размер перед очисткой (рекурсивно)
        total_size = 0
        for category in _settings.effective_categories:
            category_path = _settings.root / category
            if category_path.exists():
                for file_path in category_path.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size

        # RU: Очищаем только эффективные категории (рекурсивно)
        for category in _settings.effective_categories:
            category_path = _settings.root / category
            if category_path.exists():
                for file_path in category_path.rglob("*"):
                    if file_path.is_file():
                        file_path.unlink()

        # RU: Пересоздаем папки
        for category in _settings.effective_categories:
            (_settings.root / category).mkdir(exist_ok=True)

        freed_mb = total_size / 1024 / 1024
        result = f"Cache cleared: {freed_mb:.1f} MB freed"
        print(f"[ArenaAutoCache] {result}")
        return result

    except Exception as e:
        error_msg = f"Cache cleared: 0.0 MB freed (error: {str(e)})"
        print(f"[ArenaAutoCache] Error clearing cache: {e}")
        return error_msg


# RU: НЕ загружаем .env при импорте - только через ноду или deferred режим


def get_env_default(key: str, default_value, value_type=str):
    """RU: Получает значение из .env файла с правильным типом данных."""
    env_value = os.environ.get(key, "")
    if not env_value:
        return default_value
    
    try:
        if value_type == bool:
            return env_value.lower() in ("true", "1", "yes")
        elif value_type == float:
            return float(env_value)
        elif value_type == int:
            return int(env_value)
        else:
            return str(env_value)
    except (ValueError, TypeError):
        return default_value


def _cleanup_env_variables():
    """RU: Очищает все переменные окружения ARENA_* при деактивации ноды."""
    arena_vars = [key for key in os.environ.keys() if key.startswith("ARENA_")]
    for var in arena_vars:
        if var in os.environ:
            del os.environ[var]
    print(f"[ArenaAutoCache] Cleaned up {len(arena_vars)} environment variables")


def _add_workflow_models(models: list[dict]):
    """RU: Добавляет модели от JavaScript анализа workflow."""
    global _workflow_models
    
    with _workflow_models_lock:
        for model in models:
            if isinstance(model, dict) and 'name' in model and 'type' in model:
                category = model['type']
                filename = model['name']
                
                # RU: Нормализуем категорию модели
                normalized_category = _normalize_model_category(category)
                if normalized_category:
                    _workflow_models.add((normalized_category, filename))
                    print(f"[ArenaAutoCache] Added workflow model: {normalized_category}/{filename}")
                else:
                    print(f"[ArenaAutoCache] Unknown model category: {category}")


def _normalize_model_category(category: str) -> str:
    """RU: Нормализует категорию модели для соответствия KNOWN_CATEGORIES."""
    category_mapping = {
        'checkpoint': 'checkpoints',
        'lora': 'loras', 
        'vae': 'vae',
        'clip': 'clip',
        'controlnet': 'controlnet',
        'upscale': 'upscale_models',
        'embedding': 'embeddings',
        'hypernetwork': 'hypernetworks',
        'model': 'checkpoints',  # RU: Общие модели обычно checkpoints
        'ipadapter': 'ipadapter',
        'gligen': 'gligen',
        'animatediff': 'animatediff_models',
        't2i_adapter': 't2i_adapter',
        'gguf': 'gguf_models',
        'unet': 'unet_models',
        'diffusion': 'diffusion_models',
    }
    
    normalized = category_mapping.get(category.lower(), category.lower())
    
    # RU: Проверяем, что категория входит в известные
    if normalized in KNOWN_CATEGORIES:
        return normalized
    
    # RU: Если не найдена точная категория, ищем похожую
    for known_cat in KNOWN_CATEGORIES:
        if normalized in known_cat or known_cat in normalized:
            return known_cat
    
    return None


def _get_workflow_models() -> set[tuple[str, str]]:
    """RU: Получает модели от JavaScript анализа workflow."""
    with _workflow_models_lock:
        return _workflow_models.copy()


def _clear_workflow_models():
    """RU: Очищает модели от JavaScript анализа workflow."""
    global _workflow_models
    with _workflow_models_lock:
        _workflow_models.clear()
        print("[ArenaAutoCache] Cleared workflow models")


def _start_env_watcher():
    """RU: Запускает фоновый наблюдатель .env файла."""
    global _env_watcher_thread, _env_watcher_running
    
    if _env_watcher_running:
        return
    
    _env_watcher_running = True
    
    def watcher_worker():
        global _env_file_mtime
        while _env_watcher_running:
            try:
                comfy_root = _find_comfy_root()
                if comfy_root:
                    env_file = comfy_root / "user" / "arena_autocache.env"
                    if env_file.exists():
                        current_mtime = env_file.stat().st_mtime
                        if current_mtime != _env_file_mtime:
                            _env_file_mtime = current_mtime
                            print("[ArenaAutoCache] .env file changed, reloading...")
                            _load_env_file()
                            # RU: Здесь можно добавить уведомление фронтенда
                time.sleep(1.0)  # RU: Проверяем каждую секунду
            except Exception as e:
                if _env_watcher_running:
                    print(f"[ArenaAutoCache] Env watcher error: {e}")
                time.sleep(1.0)
    
    _env_watcher_thread = threading.Thread(target=watcher_worker, daemon=True)
    _env_watcher_thread.start()
    print("[ArenaAutoCache] Started .env file watcher")


def _stop_env_watcher():
    """RU: Останавливает фоновый наблюдатель .env файла."""
    global _env_watcher_running
    _env_watcher_running = False
    print("[ArenaAutoCache] Stopped .env file watcher")


def _get_source_path(category: str, filename: str) -> Path:
    """RU: Получает исходный путь к модели."""
    try:
        import folder_paths
        
        # RU: Получаем оригинальный путь через folder_paths
        original_path = folder_paths.get_full_path_origin(category, filename)
        if original_path and os.path.exists(original_path):
            return Path(original_path)
        
        # RU: Если не найден через folder_paths, ищем в стандартных путях
        comfy_root = _find_comfy_root()
        if comfy_root:
            models_dir = comfy_root / "models" / category
            if models_dir.exists():
                model_path = models_dir / filename
                if model_path.exists():
                    return model_path
        
        return None
    except Exception as e:
        if _settings and _settings.verbose:
            print(f"[ArenaAutoCache] Error getting source path for {category}/{filename}: {e}")
        return None


def _detect_model_type(category: str, filename: str) -> str:
    """RU: Определяет тип модели по имени файла для создания подпапок в кеше."""
    filename_lower = filename.lower()
    
    # RU: Исключения для text encoders и clip моделей - они не должны определяться как SDXL
    if category in ['text_encoders', 'clip']:
        # RU: T5 модели всегда Other
        if 't5' in filename_lower:
            return 'Other'
        # RU: CLIP модели всегда Other
        if 'clip' in filename_lower:
            return 'Other'
        # RU: Text encoder модели всегда Other
        if 'text_encoder' in filename_lower or 'encoder' in filename_lower:
            return 'Other'
    
    # RU: SDXL модели - расширенная проверка
    sdxl_keywords = [
        'sdxl', 'xl_', '_xl', 'xl-', '-xl', 'xlarge', 'extra_large',
        'realvisxl', 'proteus', 'dreamshaperxl', 'cyberrealisticxl', 
        'juggernautxl', 'zavychromaxl', 'albedobasexl', 'colorfulxl',
        'epicrealismxl', 'fenrisxl', 'leosamshelloworldxl', 'turbovisionxl'
    ]
    if any(keyword in filename_lower for keyword in sdxl_keywords):
        return 'SDXL'
    
    # RU: SD1.5 модели - точная проверка только для явных SD1.5 моделей
    sd15_keywords = [
        'sd15', 'sd1.5', 'sd_1_5', 'sd-1.5', 'stable_diffusion_1_5',
        'juggernaut_reborn', 'juggernaut_aftermath'
    ]
    if any(keyword in filename_lower for keyword in sd15_keywords):
        return 'SD1.5'
    
    # RU: Flux модели - проверяем различные варианты названий
    flux_keywords = [
        'flux', 'flux1', 'flux2', 'flux-dev', 'flux-schnell', 
        'flux1.1', 'flux1.0', 'flux.1', 'flux_1'
    ]
    if any(keyword in filename_lower for keyword in flux_keywords):
        return 'Flux'
    
    # RU: SD3 модели - проверяем различные варианты названий
    sd3_keywords = ['sd3', 'sd_3', 'sd-3', 'stable_diffusion_3', 'stable_diffusion3']
    if any(keyword in filename_lower for keyword in sd3_keywords):
        return 'SD3'
    
    # RU: Kolors модели
    kolors_keywords = ['kolors', 'kolor']
    if any(keyword in filename_lower for keyword in kolors_keywords):
        return 'Kolors'
    
    # RU: Wan модели
    wan_keywords = ['wan', 'wan2', 'wan2.2', 'wan_2']
    if any(keyword in filename_lower for keyword in wan_keywords):
        return 'Wan'
    
    # RU: Для некоторых категорий используем специальную логику
    if category == 'loras':
        # RU: LoRA модели часто содержат информацию о базовой модели
        # RU: Flux LoRA - расширенная проверка
        flux_lora_keywords = [
            'flux', 'comfyui_local', 'comfyui_subject', 'comfyui_portrait',
            'detailed_v2_flux', 'flux_realism', 'flux_art', 'flux_disney',
            'flux_mjv6', 'flux_canny', 'flux_depth', 'flux_hed',
            'flux_greenification', 'flux_turbo', 'flux_alpha'
        ]
        if any(keyword in filename_lower for keyword in flux_lora_keywords):
            return 'Flux'
        # RU: SDXL LoRA
        sdxl_lora_keywords = ['sdxl', 'xl_', '_xl', 'xl-', '-xl']
        if any(keyword in filename_lower for keyword in sdxl_lora_keywords):
            return 'SDXL'
        # RU: SD1.5 LoRA
        sd15_lora_keywords = ['sd15', 'sd1.5', 'sd_1_5']
        if any(keyword in filename_lower for keyword in sd15_lora_keywords):
            return 'SD1.5'
    
    # RU: По умолчанию возвращаем "Other" для неопознанных моделей
    return 'Other'


def _get_cache_path(category: str, filename: str) -> Path:
    """RU: Получает путь к кешированной модели с сортировкой по типам."""
    if not _settings:
        return None
    
    # RU: Определяем тип модели для создания подпапки
    model_type = _detect_model_type(category, filename)
    
    # RU: Создаем путь с подпапкой типа модели
    cache_path = _settings.root / category / model_type / filename
    
    # RU: Проверяем обратную совместимость - если модель уже существует в старом месте
    old_cache_path = _settings.root / category / filename
    if old_cache_path.exists() and not cache_path.exists():
        if _settings.verbose:
            print(f"[ArenaAutoCache] Found existing model in old location: {old_cache_path}")
        return old_cache_path
    
    # RU: Создаем папку если не существует
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    return cache_path


def _activate_workflow_analysis():
    """RU: Активирует анализ workflow для автоматического определения моделей."""
    try:
        # RU: Отправляем команду активации анализа в JavaScript
        import json
        import urllib.request
        import urllib.parse
        
        # RU: Подготавливаем данные для активации
        data = {
            "action": "activate_workflow_analysis",
            "timestamp": time.time()
        }
        
        # RU: Отправляем POST запрос к API
        try:
            req = urllib.request.Request(
                'http://localhost:8188/arena/analyze_workflow',
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            response = urllib.request.urlopen(req, timeout=5)
            if response.status == 200:
                print("[ArenaAutoCache] Workflow analysis activated successfully")
            else:
                print(f"[ArenaAutoCache] Failed to activate workflow analysis: {response.status}")
        except Exception as e:
            print(f"[ArenaAutoCache] Could not activate workflow analysis: {e}")
            
    except Exception as e:
        print(f"[ArenaAutoCache] Error activating workflow analysis: {e}")


def _auto_extend_categories_from_workflow():
    """RU: Автоматически расширяет категории кеширования на основе найденных в workflow моделей."""
    global _settings, _workflow_models
    
    if not _settings:
        return
    
    models = _get_workflow_models()
    if not models:
        return
    
    # RU: Получаем уникальные категории из найденных моделей
    workflow_categories = set()
    for category, filename in models:
        if category in KNOWN_CATEGORIES:
            workflow_categories.add(category)
    
    if not workflow_categories:
        return
    
    # RU: Проверяем, какие категории уже есть в эффективных категориях
    new_categories = workflow_categories - set(_settings.effective_categories)
    
    if new_categories:
        print(f"[ArenaAutoCache] Auto-extending categories with workflow models: {', '.join(new_categories)}")
        
        # RU: Добавляем новые категории в эффективные
        _settings.effective_categories.extend(new_categories)
        _settings.effective_categories = list(set(_settings.effective_categories))  # RU: Убираем дубликаты
        
        # RU: Создаем папки для новых категорий
        for category in new_categories:
            (_settings.root / category).mkdir(exist_ok=True)
        
        # RU: Обновляем .env файл с новыми категориями
        if _settings.verbose:
            print(f"[ArenaAutoCache] Updated effective categories: {', '.join(_settings.effective_categories)}")
        
        # RU: НЕ создаем .env файл автоматически - только через Settings Panel
        print(f"[ArenaAutoCache] IS_CHANGED: .env file creation disabled in _auto_extend_categories")
        # env_data = {"ARENA_CACHE_CATEGORIES": ",".join(_settings.effective_categories)}
        # _save_env_file(env_data)
        
        print(f"[ArenaAutoCache] Auto-extended categories: {', '.join(new_categories)}")


def _precache_workflow_models():
    """RU: Предварительно кеширует модели от JavaScript анализа workflow."""
    global _settings, _workflow_models
    
    if not _settings:
        return
    
    models = _get_workflow_models()
    if not models:
        return
    
    print(f"[ArenaAutoCache] Precaching {len(models)} workflow models...")
    
    # RU: Сначала автоматически расширяем категории
    _auto_extend_categories_from_workflow()
    
    for category, filename in models:
        if category in _settings.effective_categories:
            source_path = _get_source_path(category, filename)
            if source_path and source_path.exists():
                cache_path = _get_cache_path(category, filename)
                if not cache_path.exists():
                    _schedule_copy_task(category, filename, str(source_path), str(cache_path))
                else:
                    print(f"[ArenaAutoCache] Model already cached: {filename}")
            else:
                print(f"[ArenaAutoCache] Model not found: {filename}")
        else:
            print(f"[ArenaAutoCache] Category not in effective categories: {category}")


def _setup_workflow_analysis_api():
    """RU: Настраивает API endpoint для получения моделей от JavaScript."""
    try:
        # RU: Импортируем server только если доступен
        from server import PromptServer
        
        # RU: Добавляем custom route для анализа workflow
        @PromptServer.instance.routes.post("/arena/analyze_workflow")
        async def analyze_workflow_endpoint(request):
            try:
                from aiohttp import web
                data = await request.json()
                action = data.get('action', 'analyze')
                
                if action == "activate_workflow_analysis":
                    # RU: Активация анализа workflow
                    print("[ArenaAutoCache] Workflow analysis activation requested")
                    return web.json_response({"status": "success", "message": "Workflow analysis activated"})
                
                elif action == "analyze" or 'models' in data:
                    # RU: Анализ workflow и получение моделей
                    models = data.get('models', [])
                    
                    if models:
                        _add_workflow_models(models)
                        print(f"[ArenaAutoCache] Received {len(models)} models from JavaScript")
                        
                        # RU: Предварительно кешируем модели
                        _precache_workflow_models()
                        
                        return web.json_response({"status": "success", "models_count": len(models)})
                    else:
                        return web.json_response({"status": "error", "message": "No models provided"})
                else:
                    return web.json_response({"status": "error", "message": "Unknown action"})
                    
            except Exception as e:
                from aiohttp import web
                print(f"[ArenaAutoCache] Workflow analysis API error: {e}")
                return web.json_response({"status": "error", "message": str(e)})
        
        print("[ArenaAutoCache] Workflow analysis API endpoint registered")
        
        # RU: Добавляем API для синхронизации .env
        @PromptServer.instance.routes.get("/arena/env")
        async def get_env_endpoint(request):
            """RU: Возвращает текущие env переменные ARENA_*."""
            try:
                from aiohttp import web
                arena_vars = {}
                for key, value in os.environ.items():
                    if key.startswith("ARENA_"):
                        arena_vars[key] = value
                return web.json_response({"status": "success", "env": arena_vars})
            except Exception as e:
                from aiohttp import web
                return web.json_response({"status": "error", "message": str(e)})
        
        @PromptServer.instance.routes.post("/arena/env")
        async def post_env_endpoint(request):
            """RU: Сохраняет env переменные в .env файл."""
            try:
                from aiohttp import web
                data = await request.json()
                env_data = data.get("env", {})
                update_only = data.get("update_only", False)
                
                # RU: Валидируем ключи
                valid_keys = {
                    "ARENA_CACHE_ROOT", "ARENA_CACHE_MIN_SIZE_MB", "ARENA_CACHE_MAX_GB",
                    "ARENA_CACHE_VERBOSE", "ARENA_CACHE_CATEGORIES", "ARENA_CACHE_CATEGORIES_MODE",
                    "ARENA_CACHE_MODE", "ARENA_AUTO_CACHE_ENABLED", "ARENA_AUTOCACHE_AUTOPATCH",
                    "ARENA_CACHE_DISCOVERY", "ARENA_CACHE_PREFETCH_STRATEGY",
                    "ARENA_CACHE_MAX_CONCURRENCY", "ARENA_CACHE_SESSION_BYTE_BUDGET",
                    "ARENA_CACHE_COOLDOWN_MS"
                }
                
                filtered_env = {k: v for k, v in env_data.items() if k in valid_keys}
                
                if filtered_env:
                    # RU: Обновляем os.environ
                    for key, value in filtered_env.items():
                        os.environ[key] = value
                    
                    # RU: Сохраняем в .env файл только если НЕ update_only
                    if not update_only:
                        _save_env_file(filtered_env)
                        return web.json_response({"status": "success", "message": f"Updated {len(filtered_env)} environment variables and saved to .env file"})
                    else:
                        return web.json_response({"status": "success", "message": f"Updated {len(filtered_env)} environment variables (no .env file created)"})
                else:
                    return web.json_response({"status": "error", "message": "No valid ARENA_* variables provided"})
                    
            except Exception as e:
                from aiohttp import web
                return web.json_response({"status": "error", "message": str(e)})
        
        print("[ArenaAutoCache] Environment sync API endpoints registered")
        
        # RU: Добавляем API для autopatch
        @PromptServer.instance.routes.post("/arena/autopatch")
        async def post_autopatch_endpoint(request):
            """RU: Запускает autopatch с поддержкой required_models."""
            try:
                from aiohttp import web
                data = await request.json()
                action = data.get("action", "")
                
                if action == "start":
                    # RU: Проверяем cooldown
                    global _last_autopatch_time
                    current_time = time.time()
                    cooldown_s = _settings.cooldown_ms / 1000.0 if _settings else 5.0
                    
                    if current_time - _last_autopatch_time < cooldown_s:
                        return web.json_response({
                            "status": "skipped",
                            "code": "COOLDOWN_ACTIVE",
                            "message": f"Cooldown active, wait {cooldown_s - (current_time - _last_autopatch_time):.1f}s",
                            "retry_after": cooldown_s - (current_time - _last_autopatch_time),
                            "last_run": _last_autopatch_time
                        })
                    
                    _last_autopatch_time = current_time
                    
                    # RU: Обработка required_models
                    required_models = data.get("required_models", [])
                    if required_models:
                        with _required_models_lock:
                            _required_models.update((m["category"], m["filename"]) for m in required_models)
                        print(f"[ArenaAutoCache] Added {len(required_models)} required models")
                    elif not _required_models:
                        return web.json_response({
                            "status": "error",
                            "code": "EMPTY_REQUIRED_SET",
                            "message": "No required models specified"
                        })
                    
                    print("[ArenaAutoCache] Starting autopatch via API...")
                    _start_deferred_autopatch()
                    return web.json_response({"status": "success", "message": "Autopatch started"})
                else:
                    return web.json_response({"status": "error", "code": "INVALID_ACTION", "message": "Invalid action"})
                    
            except Exception as e:
                from aiohttp import web
                return web.json_response({"status": "error", "code": "INTERNAL_ERROR", "message": str(e)})
        
        print("[ArenaAutoCache] Autopatch API endpoint registered")
        
        # RU: Добавляем API для получения статуса
        @PromptServer.instance.routes.get("/arena/status")
        async def get_status_endpoint(request):
            """RU: Возвращает текущий статус Arena AutoCache."""
            try:
                from aiohttp import web
                status_data = {
                    "enabled": os.environ.get("ARENA_AUTO_CACHE_ENABLED", "0") in ("1", "true"),
                    "mode": os.environ.get("ARENA_CACHE_MODE", "ondemand"),
                    "cache_root": os.environ.get("ARENA_CACHE_ROOT", "D:/ArenaCache"),
                    "min_size_mb": int(os.environ.get("ARENA_CACHE_MIN_SIZE_MB", "50")),
                    "max_cache_gb": int(os.environ.get("ARENA_CACHE_MAX_GB", "100")),
                    "verbose": os.environ.get("ARENA_CACHE_VERBOSE", "0") in ("1", "true"),
                    "categories": os.environ.get("ARENA_CACHE_CATEGORIES", "").split(",") if os.environ.get("ARENA_CACHE_CATEGORIES") else [],
                    "categories_mode": os.environ.get("ARENA_CACHE_CATEGORIES_MODE", "extend"),
                    "autopatch_status": _get_autopatch_status(),
                    "discovery_mode": os.environ.get("ARENA_CACHE_DISCOVERY", "workflow_only"),
                    "prefetch_strategy": os.environ.get("ARENA_CACHE_PREFETCH_STRATEGY", "lazy"),
                    "max_concurrency": int(os.environ.get("ARENA_CACHE_MAX_CONCURRENCY", "2")),
                    "required_models_count": len(_required_models),
                    "session_bytes_downloaded": _session_bytes_downloaded
                }
                
                return web.json_response({"status": "success", **status_data})
                
            except Exception as e:
                from aiohttp import web
                print(f"[ArenaAutoCache] Status API error: {e}")
                return web.json_response({"status": "error", "message": str(e)})
        
        print("[ArenaAutoCache] Status API endpoint registered")
        
        # RU: Добавляем API для dry-run резолвинга моделей
        @PromptServer.instance.routes.post("/arena/resolve")
        async def post_resolve_endpoint(request):
            """RU: Dry-run резолвинг моделей без загрузки."""
            try:
                from aiohttp import web
                data = await request.json()
                models = data.get("models", [])
                
                resolved = []
                for model in models:
                    category = model.get("category", "")
                    filename = model.get("filename", "")
                    
                    # RU: Проверяем наличие в кеше
                    if _settings:
                        cache_path = _settings.root / category / filename
                        exists_in_cache = cache_path.exists()
                    else:
                        exists_in_cache = False
                    
                    resolved.append({
                        "category": category,
                        "filename": filename,
                        "exists_in_cache": exists_in_cache,
                        "would_download": not exists_in_cache
                    })
                
                return web.json_response({"status": "success", "resolved": resolved})
            except Exception as e:
                from aiohttp import web
                return web.json_response({"status": "error", "message": str(e)})
        
        print("[ArenaAutoCache] Resolve API endpoint registered")
        
    except ImportError:
        print("[ArenaAutoCache] Server not available - workflow analysis API not registered")
    except Exception as e:
        print(f"[ArenaAutoCache] Failed to setup workflow analysis API: {e}")


class ArenaAutoCacheSimple:
    """RU: Простая нода Arena AutoCache для кэширования моделей."""

    def __init__(self):
        # RU: Гарантируем загрузку .env файла (идемпотентно)
        _ensure_env_loaded()
        
        # RU: API уже зарегистрированы глобально при загрузке модуля
        
        self.description = "🅰️ Arena AutoCache v5.0.0 - НОВАЯ АРХИТЕКТУРА: Settings Panel как основной интерфейс, автоматическая активация по .env файлу, demand-driven caching с защитой от массового копирования. ЛОКАЛЬНЫЕ OVERRIDES: временные настройки для конкретного workflow с приоритетом над Settings Panel. АНТИМАСС-КЭШ: workflow_only + lazy режим по умолчанию, лимиты concurrency/cooldown/byte-budget, белый список категорий. АВТОАКТИВАЦИЯ: кеширование работает без ноды на канвасе при наличии .env с ARENA_AUTO_CACHE_ENABLED=1. API: расширенные endpoints /arena/status, /arena/autopatch, /arena/resolve с поддержкой required_models и dry-run. БЕЗОПАСНОСТЬ: строгая валидация, защита от path traversal, unified error codes. READ-ONLY РЕЖИМ: нода по умолчанию только для просмотра статуса, overrides через явный чекбокс."
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # RU: Принудительно обновляем интерфейс при изменении enable_caching
        # RU: .env файл создается при первом включении кеширования
        
        enable_caching = kwargs.get("enable_caching", False)
        persist_env = kwargs.get("persist_env", False)
        save_env_now = kwargs.get("save_env_now", False)
        sync_from_env = kwargs.get("sync_from_env", False)
        live_env_sync = kwargs.get("live_env_sync", False)
        
        # RU: Ручная подтяжка из файла
        if sync_from_env:
            print(f"[ArenaAutoCache] IS_CHANGED: Syncing from .env file")
            _ensure_env_loaded()
        
        # RU: Управление live sync watcher
        if live_env_sync:
            _start_env_watcher()
        else:
            _stop_env_watcher()
        
        # RU: НЕ создаем .env файл автоматически - только через Settings Panel или кнопку ARENA
        print(f"[ArenaAutoCache] IS_CHANGED: Node initialized - enable_caching={enable_caching}, persist_env={persist_env}, save_env_now={save_env_now}")
        print(f"[ArenaAutoCache] IS_CHANGED: .env file creation disabled - use Settings Panel or ARENA button instead")
        
        if enable_caching:
            print(f"[ArenaAutoCache] IS_CHANGED: Caching enabled")
            
            if not persist_env:
                print(f"[ArenaAutoCache] IS_CHANGED: Caching enabled for current session only (persist_env=False)")
            
            # RU: Запускаем deferred autopatch сразу
            _start_deferred_autopatch()
            print(f"[ArenaAutoCache] IS_CHANGED: Started deferred autopatch worker")
        
        return float("inf")

    @classmethod
    def INPUT_TYPES(cls):
        # RU: Безопасные значения по умолчанию - все выключено при первом запуске
        # RU: При активации enable_caching=True будут загружены значения из .env файла
        return {
            "required": {
                "cache_root": ("STRING", {"default": "", "multiline": False, "label": "Cache Root Path"}),
                "min_size_mb": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1000.0, "step": 0.1, "label": "Min File Size (MB)"}),
                "max_cache_gb": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1000.0, "step": 1.0, "label": "Max Cache Size (GB)"}),
                "verbose": ("BOOLEAN", {"default": False, "label": "Verbose Logging"}),
                "cache_mode": (["ondemand", "disabled"], {"default": "disabled", "label": "Cache Mode (ondemand=only when used)"}),
                "auto_patch_on_start": ("BOOLEAN", {"default": False, "label": "Auto Patch on Start"}),
                "auto_cache_enabled": ("BOOLEAN", {"default": False, "label": "Auto Cache Enabled"}),
                "persist_env": ("BOOLEAN", {"default": False, "label": "Persist to .env File (WARNING: enables global caching on restart)"}),
                "clear_cache_now": ("BOOLEAN", {"default": False, "label": "Clear Cache Now"}),
                "enable_caching": ("BOOLEAN", {"default": False, "label": "Enable Caching (creates .env and activates caching immediately)"}),
                "save_env_now": ("BOOLEAN", {"default": False, "label": "Save to .env Now (writes current settings to file)"}),
                "sync_from_env": ("BOOLEAN", {"default": False, "label": "Sync from .env (loads settings from file)"}),
                "live_env_sync": ("BOOLEAN", {"default": False, "label": "Live .env Sync (auto-reload when file changes)"}),
                "use_workflow_overrides": ("BOOLEAN", {"default": False, "label": "Use Workflow Overrides (temporarily override Settings Panel for this workflow)"}),
                "override_discovery_mode": (["inherit", "workflow_only", "manual_only"], {"default": "inherit", "label": "Override Discovery Mode"}),
                "override_prefetch_strategy": (["inherit", "lazy", "prefetch_allowlist"], {"default": "inherit", "label": "Override Prefetch Strategy"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "run"
    CATEGORY = "Arena"

    def run(
        self,
        cache_root: str = "",
        min_size_mb: float = 0.0,
        max_cache_gb: float = 0.0,
        verbose: bool = False,
        cache_mode: str = "disabled",
        auto_patch_on_start: bool = False,
        auto_cache_enabled: bool = False,
        persist_env: bool = False,
        clear_cache_now: bool = False,
        enable_caching: bool = False,
        save_env_now: bool = False,
        sync_from_env: bool = False,
        live_env_sync: bool = False,
        use_workflow_overrides: bool = False,
        override_discovery_mode: str = "inherit",
        override_prefetch_strategy: str = "inherit",
    ):
        """RU: Основная функция ноды."""
        global _settings, _copy_thread_started

        # RU: Применяем локальные overrides если указаны
        if use_workflow_overrides:
            if override_discovery_mode != "inherit":
                os.environ["ARENA_CACHE_DISCOVERY"] = override_discovery_mode
            if override_prefetch_strategy != "inherit":
                os.environ["ARENA_CACHE_PREFETCH_STRATEGY"] = override_prefetch_strategy
            
            print(f"[ArenaAutoCache] Applied workflow overrides: discovery={override_discovery_mode}, prefetch={override_prefetch_strategy}")

        # RU: Если кеширование не включено - очищаем переменные окружения и возвращаем статус
        if not enable_caching:
            _cleanup_env_variables()
            status = "Arena AutoCache: Caching DISABLED - Enable caching to configure settings"
            if verbose:
                print(f"[ArenaAutoCache] {status}")
            return (status,)
        
        # RU: .env файл уже создан в IS_CHANGED при включении enable_caching
        # RU: Здесь только проверяем, что файл существует
        comfy_root = _find_comfy_root()
        if comfy_root:
            env_file_path = comfy_root / "user" / "arena_autocache.env"
            if env_file_path.exists():
                print(f"[ArenaAutoCache] Found existing .env file - caching enabled")
            else:
                print(f"[ArenaAutoCache] No .env file found - caching will be disabled")
        
        # RU: Кеширование включено - загружаем .env файл если существует
        _ensure_env_loaded()
        
        # RU: Применяем патч для кеширования
        _ensure_patch_applied()

        try:
            # RU: Инициализируем настройки из параметров ноды
            _settings = _init_settings(
                cache_root, min_size_mb, max_cache_gb, verbose
            )
            
            if verbose:
                print(f"[ArenaAutoCache] Settings initialized: root={_settings.root}, mode={cache_mode}")
            
            # RU: Устанавливаем переменные окружения для кеширования
            os.environ["ARENA_AUTO_CACHE_ENABLED"] = "1" if auto_cache_enabled else "0"
            os.environ["ARENA_AUTOCACHE_AUTOPATCH"] = "1" if auto_patch_on_start else "0"

            # RU: Применяем патч folder_paths (только один раз)
            if not _folder_paths_patched:
                _apply_folder_paths_patch()

            # RU: Запускаем фоновый поток копирования
            if not _copy_thread_started:
                copy_thread = threading.Thread(target=_copy_worker, daemon=True)
                copy_thread.start()
                _copy_thread_started = True
                if verbose:
                    print("[ArenaAutoCache] Started background copy thread")
            
            # RU: Только ondemand режим - кэширование только при использовании моделей
            if cache_mode == "ondemand":
                if verbose:
                    print("[ArenaAutoCache] OnDemand mode - smart caching on first access")
                    print("[ArenaAutoCache] Models will be cached automatically when first used")
                
                # RU: Предварительно кешируем модели от JavaScript анализа workflow
                _precache_workflow_models()
                
                # RU: Активируем анализ workflow для автоматического определения моделей
                _activate_workflow_analysis()
            elif cache_mode == "disabled":
                if verbose:
                    print("[ArenaAutoCache] Disabled mode - no caching")
            else:
                if verbose:
                    print(f"[ArenaAutoCache] Unknown cache mode: {cache_mode}, using ondemand behavior")

            # RU: Очищаем кэш если запрошено
            clear_result = None
            if clear_cache_now:
                clear_result = _clear_cache_folder()

            # RU: Категории моделей определяются автоматически через JavaScript анализ workflow
            # RU: Не нужно управлять категориями вручную - JS анализирует workflow и определяет нужные модели
            
            # RU: Сохраняем настройки в .env только если persist_env=True (НЕ автоматически)
            # RU: ВНИМАНИЕ: persist_env=True включает глобальное кеширование при перезагрузке!
            if persist_env:
                env_data = {
                    "ARENA_CACHE_MIN_SIZE_MB": str(min_size_mb),
                    "ARENA_CACHE_MAX_GB": str(max_cache_gb),
                    "ARENA_CACHE_VERBOSE": "1" if verbose else "0",
                    "ARENA_CACHE_MODE": cache_mode,
                    "ARENA_AUTO_CACHE_ENABLED": "1" if auto_cache_enabled else "0",
                }
                
                # RU: Сохраняем путь кэша в .env только если он указан в ноде
                if cache_root and cache_root.strip():
                    env_data["ARENA_CACHE_ROOT"] = cache_root
                    if verbose:
                        print(f"[ArenaAutoCache] Saving cache root from node to .env: {cache_root}")

                # RU: НЕ создаем .env файл автоматически - только через Settings Panel
                print(f"[ArenaAutoCache] IS_CHANGED: .env file creation disabled in _precache_workflow_models")
                # env_data["ARENA_AUTOCACHE_AUTOPATCH"] = "1"
                # _save_env_file(env_data)
                
                # RU: Запускаем deferred autopatch если еще не запущен
                if not _deferred_autopatch_started:
                    _start_deferred_autopatch()
                    if verbose:
                        print(f"[ArenaAutoCache] Started deferred autopatch worker")
                
                if verbose:
                    print(f"[ArenaAutoCache] Settings saved to .env file (persist_env=True)")
            else:
                if verbose:
                    print(f"[ArenaAutoCache] Settings not persisted (persist_env=False)")

            # RU: Возвращаем результат очистки или статус инициализации
            if clear_result:
                status = clear_result
            else:
                auto_status = "enabled" if auto_cache_enabled else "DISABLED (safe mode)"
                source = "Node Override" if use_workflow_overrides else "Settings Panel"
                status = f"Arena AutoCache initialized: {len(_settings.effective_categories)} categories, {_settings.max_cache_gb}GB limit, mode: {cache_mode}, auto-cache: {auto_status}, source: {source}"

            if verbose:
                print(f"[ArenaAutoCache] {status}")

            return (status,)

        except Exception as e:
            error_msg = f"Arena AutoCache error: {str(e)}"
            print(f"[ArenaAutoCache] {error_msg}")
            return (error_msg,)


# RU: Упрощенный подход - кеширование только при реальном использовании
# RU: Анализ workflow удален как неработающий в ComfyUI


# RU: Регистрация ноды
NODE_CLASS_MAPPINGS = {
    "🅰️ Arena AutoCache v5.0.0": ArenaAutoCacheSimple,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "🅰️ Arena AutoCache v5.0.0": "🅰️ Arena AutoCache v5.0.0",
}

print("[ArenaAutoCache] Loaded v5.0.0 with Settings Panel primary interface, auto-activation, and demand-driven caching")

# RU: Автоматическая активация при наличии .env файла
print("[ArenaAutoCache] Checking for auto-activation...")
comfy_root = _find_comfy_root()
if comfy_root:
    env_file_path = comfy_root / "user" / "arena_autocache.env"
    if env_file_path.exists():
        print("[ArenaAutoCache] Found .env file, loading configuration...")
        _ensure_env_loaded()
        
        # RU: Проверяем флаг автоактивации
        if os.environ.get("ARENA_AUTO_CACHE_ENABLED", "0") in ("1", "true"):
            print("[ArenaAutoCache] Auto-activation enabled, starting deferred autopatch...")
            os.environ["ARENA_AUTOCACHE_AUTOPATCH"] = "1"
            _start_deferred_autopatch()
        else:
            print("[ArenaAutoCache] Auto-activation disabled in .env")
    else:
        print("[ArenaAutoCache] No .env file found, waiting for Settings Panel or node activation")
else:
    print("[ArenaAutoCache] ComfyUI root not found, waiting for Settings Panel or node activation")

# RU: Регистрируем API endpoints глобально для работы через интерфейс
print("[ArenaAutoCache] Registering global API endpoints for UI integration...")
try:
    _setup_workflow_analysis_api()
    print("[ArenaAutoCache] [OK] Global API endpoints registered successfully")
except Exception as e:
    print(f"[ArenaAutoCache] [ERROR] Failed to register global API endpoints: {e}")

# RU: НЕ запускаем автопатч автоматически - только через интерфейс
# autopatch_env = os.environ.get("ARENA_AUTOCACHE_AUTOPATCH")
# print(f"[ArenaAutoCache] Module loaded - ARENA_AUTOCACHE_AUTOPATCH = {autopatch_env}")

# if autopatch_env == "1":
#     print("[ArenaAutoCache] Starting deferred autopatch from module load...")
#     _start_deferred_autopatch()
# else:
#     print(f"[ArenaAutoCache] Deferred autopatch disabled (ARENA_AUTOCACHE_AUTOPATCH = {autopatch_env})")

print("[ArenaAutoCache] Module loaded - NO automatic caching, only through node interface")
