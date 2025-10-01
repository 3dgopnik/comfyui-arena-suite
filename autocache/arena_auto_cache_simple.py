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
        _load_env_file()
        _env_loaded = True


def _compute_effective_categories(
    cache_categories: str = "", categories_mode: str = "extend", verbose: bool = False
) -> list[str]:
    """RU: Вычисляет эффективные категории для кэширования."""
    # RU: Маппинг для правильных названий категорий (поддерживает разные регистры)
    CATEGORY_MAPPING = {
        # RU: Основные модели (разные регистры)
        "checkpoint": "checkpoints",
        "Checkpoint": "checkpoints",
        "CHECKPOINT": "checkpoints",
        "lora": "loras",
        "LoRA": "loras", 
        "LoRa": "loras",
        "LORA": "loras",
        "lora": "loras",
        
        # RU: Остальные категории
        "vae": "vae",
        "clip": "clip",
        "controlnet": "controlnet",
        "upscale": "upscale_models",
        "embedding": "embeddings",
        "hypernetwork": "hypernetworks",
        "ipadapter": "ipadapter",
        "gligen": "gligen",
        "animatediff": "animatediff_models",
        "t2i_adapter": "t2i_adapter",
        "diffusion": "diffusion_models",
        "ultralytics": "ultralytics",
        "insightface": "insightface",
        "inpaint": "inpaint",
        "pix2pix": "pix2pix",
        "sams": "sams",
        "pulid": "pulid",
        "llm": "llm",
        "ipadapter_encoder": "ipadapter_encoders",
        "download_model": "download_model_base",
        "gguf": "gguf_models",
        "unet": "unet_models",
        "style": "style_models",
        "flux": "flux_models",
        "facerestore": "facerestore_models",
        "antelope": "antelopev2",
        "bbox": "bbox",
        "segm": "segm",
        "apisr": "apisr",
        "stablesr": "stablesr",
        "supir": "supir",
        "ccsr": "ccsr",
        "video": "video_models",
        "motion": "motion_models",
        "temporal": "temporal_models",
    }
    
    # RU: Парсим категории из ноды
    node_categories = []
    if cache_categories and cache_categories.strip():
        raw_categories = [cat.strip() for cat in cache_categories.split(",") if cat.strip()]
        # RU: Применяем маппинг для правильных названий (сохраняем регистр)
        node_categories = [CATEGORY_MAPPING.get(cat, cat.lower()) for cat in raw_categories]

    # RU: Парсим категории из .env
    env_categories = []
    env_categories_str = os.environ.get("ARENA_CACHE_CATEGORIES", "")
    if env_categories_str and env_categories_str.strip():
        raw_env_categories = [cat.strip() for cat in env_categories_str.split(",") if cat.strip()]
        # RU: Применяем маппинг для правильных названий (сохраняем регистр)
        env_categories = [CATEGORY_MAPPING.get(cat, cat.lower()) for cat in raw_env_categories]

    # RU: Определяем режим (приоритет: нода > .env > default)
    mode = categories_mode
    if not mode and "ARENA_CACHE_CATEGORIES_MODE" in os.environ:
        mode = os.environ["ARENA_CACHE_CATEGORIES_MODE"]
    if not mode:
        mode = "extend"

    # RU: Выбираем источник категорий (приоритет: нода > .env > default)
    source_categories = (
        node_categories if node_categories else (env_categories if env_categories else [])
    )

    # RU: Умная логика взаимодействия с .env файлом
    if not source_categories:
        # RU: Если категории пустые - используем DEFAULT_WHITELIST
        effective = DEFAULT_WHITELIST.copy()
        if verbose:
            print(
                f"[ArenaAutoCache] No categories specified - using DEFAULT_WHITELIST: {', '.join(effective)}"
            )
    else:
        # RU: Фильтруем только известные категории
        valid_categories = [cat for cat in source_categories if cat in KNOWN_CATEGORIES]
        unknown_categories = [cat for cat in source_categories if cat not in KNOWN_CATEGORIES]

        if unknown_categories and verbose:
            print(f"[ArenaAutoCache] Unknown categories ignored: {', '.join(unknown_categories)}")

        # RU: Умная логика: дополняем недостающие категории из DEFAULT_WHITELIST
        if valid_categories:
            # RU: Добавляем недостающие категории из DEFAULT_WHITELIST
            missing_categories = [cat for cat in DEFAULT_WHITELIST if cat not in valid_categories]
            if missing_categories and verbose:
                print(f"[ArenaAutoCache] Adding missing categories: {', '.join(missing_categories)}")
            
            # RU: Объединяем существующие + недостающие
            effective = list(set(valid_categories + missing_categories))
        else:
            # RU: Если все категории неизвестные - используем DEFAULT_WHITELIST
            effective = DEFAULT_WHITELIST.copy()
            if verbose:
                print(f"[ArenaAutoCache] All categories unknown - using DEFAULT_WHITELIST: {', '.join(effective)}")

    # RU: Сортируем для консистентности
    effective.sort()

    # RU: НЕ обновляем .env файл автоматически в _compute_effective_categories
    # RU: Обновление .env происходит только в функции run() при режиме "extend"

    if verbose:
        print(f"[ArenaAutoCache] Cache categories mode: {mode}; effective: {', '.join(effective)}")

    return effective


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
        return

    env_file = comfy_root / "user" / "arena_autocache.env"
    
    # RU: НЕ создаем .env файл автоматически - только при включении переключателя в ноде
    if not env_file.exists():
        print(f"[ArenaAutoCache] No .env file found - caching disabled by default")
        return
    
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
                            "ARENA_CACHE_MODE", "ARENA_AUTO_CACHE_ENABLED", "ARENA_AUTOCACHE_AUTOPATCH"
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
                            if value.lower() not in ("ondemand", "eager", "disabled"):
                                print(f"[ArenaAutoCache] Warning: Invalid cache mode '{value}' for {key} in {env_file}:{line_num} (valid: ondemand, eager, disabled)")
                        
                        os.environ[key] = value
                        loaded_count += 1
            
            if loaded_count > 0:
                print(f"[ArenaAutoCache] Loaded {loaded_count} settings from {env_file}")
            else:
                print(f"[ArenaAutoCache] No valid settings found in {env_file}")
                
        except Exception as e:
            print(f"[ArenaAutoCache] Error loading env file: {e}")


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
    cache_categories: str = "",
    categories_mode: str = "extend",
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
    
    # RU: Вычисляем эффективные категории
    effective_categories = _compute_effective_categories(cache_categories, categories_mode, verbose)
    
    # RU: Создаем подпапки для эффективных категорий
    for category in effective_categories:
        (root / category).mkdir(exist_ok=True)
    
    _settings = CacheSettings(
        root=root,
        min_size_mb=min_size_mb,
        max_cache_gb=max_cache_gb,
        verbose=verbose,
        effective_categories=effective_categories,
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
            # RU: Кэширование только для эффективных категорий
            if folder_name in _settings.effective_categories:
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
                        auto_cache_enabled = os.environ.get("ARENA_AUTO_CACHE_ENABLED", "true").lower() in ("true", "1", "yes")
                        if auto_cache_enabled:
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


def _schedule_copy_task(category: str, filename: str, source_path: str, cache_path: str):
    """RU: Планирует задачу копирования с дедупликацией."""
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


def _eager_cache_all_models():
    """RU: Eager режим - копирует все модели из эффективных категорий в кэш."""
    if not _settings:
        print("[ArenaAutoCache] ERROR: Settings not initialized for eager caching")
        return
    
    try:
        import folder_paths
        
        total_files = 0
        cached_files = 0
        skipped_files = 0
        
        print(f"[ArenaAutoCache] Starting eager caching for {len(_settings.effective_categories)} categories...")
        print(f"[ArenaAutoCache] Cache root: {_settings.root}")
        
        # RU: Проверяем, что корень кэша правильный
        if not _settings.root or str(_settings.root) == ".":
            print("[ArenaAutoCache] ERROR: Invalid cache root, skipping eager caching")
            return
        
        for category in _settings.effective_categories:
            if not hasattr(folder_paths, 'folder_names_and_paths'):
                continue
                
            # RU: Получаем все пути для категории
            category_paths = folder_paths.folder_names_and_paths.get(category, [])
            if not category_paths:
                continue
                
            print(f"[ArenaAutoCache] Eager caching category '{category}' from {len(category_paths)} paths...")
            
            for source_path in category_paths:
                source_path = Path(source_path)
                if not source_path.exists():
                    continue
                    
                # RU: Сканируем все файлы в папке
                for file_path in source_path.rglob("*"):
                    if not file_path.is_file():
                        continue
                        
                    total_files += 1
                    filename = file_path.name
                    cache_path = _settings.root / category / filename
                    
                    # RU: Проверяем размер файла
                    try:
                        file_size = file_path.stat().st_size
                        if file_size < _settings.min_size_mb * 1024 * 1024:
                            skipped_files += 1
                            if _settings.verbose:
                                print(f"[ArenaAutoCache] Skipping {filename}: too small ({file_size / 1024 / 1024:.1f}MB)")
                            continue
                    except Exception:
                        skipped_files += 1
                        continue
                    
                    # RU: Проверяем, не существует ли уже в кэше
                    if cache_path.exists():
                        cached_files += 1
                        if _settings.verbose:
                            print(f"[ArenaAutoCache] Already cached: {filename}")
                        continue
                    
                    # RU: Копируем файл
                    try:
                        cache_path.parent.mkdir(parents=True, exist_ok=True)
                        temp_path = cache_path.with_suffix(cache_path.suffix + ".part")
                        shutil.copy2(file_path, temp_path)
                        temp_path.rename(cache_path)
                        cached_files += 1
                        
                        if _settings.verbose:
                            print(f"[ArenaAutoCache] Eager cached: {filename}")
                        
                        # RU: Проверяем размер кэша и очищаем при необходимости
                        _prune_cache_if_needed()
                        
                    except Exception as e:
                        skipped_files += 1
                        if _settings.verbose:
                            print(f"[ArenaAutoCache] Error eager caching {filename}: {e}")
        
        print(f"[ArenaAutoCache] Eager caching completed: {cached_files} cached, {skipped_files} skipped, {total_files} total files")
        
    except Exception as e:
        print(f"[ArenaAutoCache] Error in eager caching: {e}")


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


def _get_cache_path(category: str, filename: str) -> Path:
    """RU: Получает путь к кешированной модели."""
    if not _settings:
        return None
    return _settings.root / category / filename


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
        
        # RU: Сохраняем обновленные категории в .env
        env_data = {"ARENA_CACHE_CATEGORIES": ",".join(_settings.effective_categories)}
        _save_env_file(env_data)
        
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
                data = await request.json()
                action = data.get('action', 'analyze')
                
                if action == "activate_workflow_analysis":
                    # RU: Активация анализа workflow
                    print("[ArenaAutoCache] Workflow analysis activation requested")
                    return {"status": "success", "message": "Workflow analysis activated"}
                
                elif action == "analyze" or 'models' in data:
                    # RU: Анализ workflow и получение моделей
                    models = data.get('models', [])
                    
                    if models:
                        _add_workflow_models(models)
                        print(f"[ArenaAutoCache] Received {len(models)} models from JavaScript")
                        
                        # RU: Предварительно кешируем модели
                        _precache_workflow_models()
                        
                        return {"status": "success", "models_count": len(models)}
                    else:
                        return {"status": "error", "message": "No models provided"}
                else:
                    return {"status": "error", "message": "Unknown action"}
                    
            except Exception as e:
                print(f"[ArenaAutoCache] Workflow analysis API error: {e}")
                return {"status": "error", "message": str(e)}
        
        print("[ArenaAutoCache] Workflow analysis API endpoint registered")
        
    except ImportError:
        print("[ArenaAutoCache] Server not available - workflow analysis API not registered")
    except Exception as e:
        print(f"[ArenaAutoCache] Failed to setup workflow analysis API: {e}")


class ArenaAutoCacheSimple:
    """RU: Простая нода Arena AutoCache для кэширования моделей."""

    def __init__(self):
        # RU: Гарантируем загрузку .env файла (идемпотентно)
        _ensure_env_loaded()
        
        # RU: Настраиваем API для анализа workflow
        _setup_workflow_analysis_api()
        
        self.description = "Arena AutoCache (simple) v4.5.0 - Production-ready node with enable toggle: caching works only when enable_caching=True. Smart preset categories (checkpoints, loras, clip, vae, controlnet, upscale_models, embeddings, hypernetworks, gguf_models, unet_models, diffusion_models), automatic .env management, deferred autopatch, flexible caching modes (ondemand/eager/disabled), SAFE BY DEFAULT - caching disabled by default with activation toggle, instant .env updates, robust env handling, thread-safety, safe pruning, enhanced diagnostics, and proper .env loading architecture"
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # RU: Принудительно обновляем интерфейс при изменении enable_caching
        # RU: .env файл создается при первом включении кеширования
        
        # RU: Проверяем, включено ли кеширование
        enable_caching = kwargs.get("enable_caching", False)
        if enable_caching:
            # RU: Создаем .env файл при первом включении кеширования
            comfy_root = _find_comfy_root()
            if comfy_root:
                env_file_path = comfy_root / "user" / "arena_autocache.env"
                if not env_file_path.exists():
                    print(f"[ArenaAutoCache] IS_CHANGED: First time enabling caching - creating .env file")
                    
                    # RU: Получаем параметры из kwargs
                    cache_root = kwargs.get("cache_root", "")
                    min_size_mb = kwargs.get("min_size_mb", 0.0)
                    max_cache_gb = kwargs.get("max_cache_gb", 0.0)
                    verbose = kwargs.get("verbose", False)
                    cache_categories = kwargs.get("cache_categories", "")
                    categories_mode = kwargs.get("categories_mode", "extend")
                    cache_mode = kwargs.get("cache_mode", "disabled")
                    auto_patch_on_start = kwargs.get("auto_patch_on_start", False)
                    auto_cache_enabled = kwargs.get("auto_cache_enabled", False)
                    
                    # RU: Создаем .env файл с настройками из ноды
                    cache_root_final = cache_root if cache_root and cache_root.strip() else str(comfy_root / "models" / "arena_cache")
                    
                    # RU: При режиме extend - базовые категории всегда + дополнительные
                    base_categories = "checkpoints,loras,clip,vae,controlnet,upscale_models,embeddings,hypernetworks,gguf_models,unet_models,diffusion_models"
                    if categories_mode == "extend":
                        if cache_categories and cache_categories.strip():
                            all_categories = f"{base_categories},{cache_categories}"
                        else:
                            all_categories = base_categories
                    else:
                        all_categories = cache_categories if cache_categories and cache_categories.strip() else base_categories
                    
                    env_data = {
                        "ARENA_CACHE_ROOT": cache_root_final,
                        "ARENA_CACHE_MIN_SIZE_MB": str(min_size_mb),
                        "ARENA_CACHE_MAX_GB": str(max_cache_gb),
                        "ARENA_CACHE_VERBOSE": "true" if verbose else "false",
                        "ARENA_CACHE_CATEGORIES": all_categories,
                        "ARENA_CACHE_CATEGORIES_MODE": categories_mode,
                        "ARENA_CACHE_MODE": cache_mode,
                        "ARENA_AUTOCACHE_AUTOPATCH": "true" if auto_patch_on_start else "false",
                        "ARENA_AUTO_CACHE_ENABLED": "true" if auto_cache_enabled else "false",
                    }
                    
                    env_file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(env_file_path, "w", encoding="utf-8") as f:
                        f.write("# Arena AutoCache Environment Settings\n")
                        f.write("# Created when enable_caching=True\n\n")
                        for key, value in env_data.items():
                            f.write(f"{key}={value}\n")
                    
                    print(f"[ArenaAutoCache] IS_CHANGED: Created .env file with node settings")
                    
                    # RU: Сразу активируем deferred autopatch для глобального кеширования
                    os.environ["ARENA_AUTOCACHE_AUTOPATCH"] = "1"
                    print(f"[ArenaAutoCache] IS_CHANGED: Activated deferred autopatch for global caching")
                    
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
                "cache_categories": ("STRING", {"default": "", "multiline": False, "label": "Additional Cache Categories (comma-separated, will be added to base categories in extend mode)"}),
                "categories_mode": (["extend", "override"], {"default": "extend", "label": "Categories Mode"}),
                "cache_mode": (["ondemand", "eager", "disabled"], {"default": "disabled", "label": "Cache Mode (ondemand=only when used)"}),
                "auto_patch_on_start": ("BOOLEAN", {"default": False, "label": "Auto Patch on Start"}),
                "auto_cache_enabled": ("BOOLEAN", {"default": False, "label": "Auto Cache Enabled"}),
                "persist_env": ("BOOLEAN", {"default": True, "label": "Persist to .env File"}),
                "clear_cache_now": ("BOOLEAN", {"default": False, "label": "Clear Cache Now"}),
                "enable_caching": ("BOOLEAN", {"default": False, "label": "Enable Caching (creates .env and activates caching immediately)"}),
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
        cache_categories: str = "",
        categories_mode: str = "extend",
        cache_mode: str = "disabled",
        auto_patch_on_start: bool = False,
        auto_cache_enabled: bool = False,
        persist_env: bool = True,
        clear_cache_now: bool = False,
        enable_caching: bool = False,
    ):
        """RU: Основная функция ноды."""
        global _settings, _copy_thread_started

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
                cache_root, min_size_mb, max_cache_gb, verbose, cache_categories, categories_mode
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
            
            # RU: Для eager режима запускаем массовое кэширование ТОЛЬКО если режим eager
            if cache_mode == "eager" and auto_cache_enabled:
                if verbose:
                    print("[ArenaAutoCache] Starting eager caching in background...")
                # RU: Запускаем eager кэширование в отдельном потоке
                eager_thread = threading.Thread(target=_eager_cache_all_models, daemon=True)
                eager_thread.start()
            elif cache_mode == "ondemand":
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

            # RU: Автоматическое дополнение .env файла категориями из ноды
            # RU: Принцип: .env файл главный, нода только дополняет недостающие категории
            if categories_mode == "extend" and cache_categories:
                # RU: Получаем текущие категории из .env
                current_env_categories = os.environ.get("ARENA_CACHE_CATEGORIES", "")
                if current_env_categories:
                    # RU: Проверяем, есть ли новые категории в ноде
                    env_cats = [cat.strip() for cat in current_env_categories.split(",") if cat.strip()]
                    node_cats = [cat.strip() for cat in cache_categories.split(",") if cat.strip()]
                    # RU: Добавляем только новые категории (НЕ перезаписываем существующие)
                    new_cats = [cat for cat in node_cats if cat not in env_cats]
                    if new_cats:
                        # RU: Дополняем .env только новыми категориями
                        combined_cats = current_env_categories + "," + ",".join(new_cats)
                        env_data = {"ARENA_CACHE_CATEGORIES": combined_cats}
                        _save_env_file(env_data)
                        if verbose:
                            print(f"[ArenaAutoCache] Auto-extended .env with new categories: {', '.join(new_cats)}")
                else:
                    # RU: Если в .env нет категорий - добавляем категории из ноды
                    env_data = {"ARENA_CACHE_CATEGORIES": cache_categories}
                    _save_env_file(env_data)
                    if verbose:
                        print(f"[ArenaAutoCache] Auto-added categories to .env from node: {cache_categories}")
            
            # RU: Сохраняем настройки в .env только если persist_env=True (НЕ автоматически)
            if persist_env:
                # RU: При режиме extend - базовые категории всегда + дополнительные из ноды
                base_categories = "checkpoints,loras,clip,vae,controlnet,upscale_models,embeddings,hypernetworks,gguf_models,unet_models,diffusion_models"
                
                if categories_mode == "extend":
                    # RU: Режим extend - базовые + дополнительные
                    if cache_categories and cache_categories.strip():
                        all_categories = f"{base_categories},{cache_categories}"
                    else:
                        all_categories = base_categories
                else:
                    # RU: Режим override - только то, что указал пользователь
                    all_categories = cache_categories if cache_categories and cache_categories.strip() else base_categories
                
                env_data = {
                    "ARENA_CACHE_MIN_SIZE_MB": str(min_size_mb),
                    "ARENA_CACHE_MAX_GB": str(max_cache_gb),
                    "ARENA_CACHE_VERBOSE": "1" if verbose else "0",
                    "ARENA_CACHE_CATEGORIES": all_categories,  # RU: Базовые + дополнительные категории
                    "ARENA_CACHE_CATEGORIES_MODE": categories_mode,
                    "ARENA_CACHE_MODE": cache_mode,
                    "ARENA_AUTO_CACHE_ENABLED": "1" if auto_cache_enabled else "0",
                }
                
                # RU: Сохраняем путь кэша в .env только если он указан в ноде
                if cache_root and cache_root.strip():
                    env_data["ARENA_CACHE_ROOT"] = cache_root
                    if verbose:
                        print(f"[ArenaAutoCache] Saving cache root from node to .env: {cache_root}")

                # RU: Всегда включаем автопатч для глобальной работы
                env_data["ARENA_AUTOCACHE_AUTOPATCH"] = "1"
                _save_env_file(env_data)
                
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
                status = f"Arena AutoCache initialized: {len(_settings.effective_categories)} categories, {_settings.max_cache_gb}GB limit, mode: {cache_mode}, auto-cache: {auto_status}"

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
    "ArenaAutoCache (simple)": ArenaAutoCacheSimple,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArenaAutoCache (simple)": "Arena AutoCache (simple) v4.5.0",
}

print("[ArenaAutoCache] Loaded production-ready node with smart preset categories and OnDemand caching")

# RU: Отложенный автопатч - ждем готовности ComfyUI
# RU: Загружаем .env файл идемпотентно для deferred autopatch
_ensure_env_loaded()

# RU: Проверяем, есть ли .env файл с настройками
comfy_root = _find_comfy_root()
if comfy_root:
    env_file_path = comfy_root / "user" / "arena_autocache.env"
    if env_file_path.exists():
        print("[ArenaAutoCache] Found .env file - enabling global caching")
        # RU: Принудительно включаем автопатч для глобальной работы
        os.environ["ARENA_AUTOCACHE_AUTOPATCH"] = "1"

autopatch_env = os.environ.get("ARENA_AUTOCACHE_AUTOPATCH")
print(f"[ArenaAutoCache] Module loaded - ARENA_AUTOCACHE_AUTOPATCH = {autopatch_env}")

if autopatch_env == "1":
    print("[ArenaAutoCache] Starting deferred autopatch from module load...")
    _start_deferred_autopatch()
else:
    print(f"[ArenaAutoCache] Deferred autopatch disabled (ARENA_AUTOCACHE_AUTOPATCH = {autopatch_env})")
