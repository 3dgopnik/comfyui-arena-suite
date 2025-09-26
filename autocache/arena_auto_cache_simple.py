#!/usr/bin/env python3
"""
Arena AutoCache (simple) - Production-ready OnDemand-only node with robust env handling, thread-safety, safe pruning, and autopatch
RU: Production-готовая нода кэширования с надежной обработкой .env, потокобезопасностью, безопасной очисткой и автопатчингом
"""

import json
import os
import shutil
import threading
import time
from pathlib import Path
from queue import Queue
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
import platform

# RU: Глобальные настройки и состояние
_settings = None
_folder_paths_patched = False
_copy_queue = Queue()
_copy_thread_started = False
_scheduled_tasks: Set[Tuple[str, str]] = set()  # (category, filename)
_patch_lock = threading.Lock()
_scheduled_lock = threading.Lock()  # RU: Лок для дедупликации

# RU: Whitelist категорий для кэширования
DEFAULT_WHITELIST = ["checkpoints", "loras", "clip", "clip_vision", "text_encoders"]
KNOWN_CATEGORIES = [
    "checkpoints", "loras", "clip", "clip_vision", "text_encoders", "vae", "controlnet", 
    "upscale_models", "embeddings", "hypernetworks", "ipadapter", "gligen", 
    "animatediff_models", "t2i_adapter", "diffusion_models", "ultralytics", 
    "insightface", "inpaint", "pix2pix", "sams", "pulid"
]

# RU: Статистика копирования
_copy_status = {
    "total_jobs": 0,
    "completed_jobs": 0,
    "failed_jobs": 0,
    "current_file": "",
    "last_update": 0
}

def _now() -> float:
    """RU: Текущее время в секундах."""
    return time.time()

def _compute_effective_categories(cache_categories: str = "", categories_mode: str = "extend", verbose: bool = False) -> List[str]:
    """RU: Вычисляет эффективные категории для кэширования."""
    # RU: Парсим категории из ноды
    node_categories = []
    if cache_categories:
        node_categories = [cat.strip().lower() for cat in cache_categories.split(',') if cat.strip()]
    
    # RU: Парсим категории из .env
    env_categories = []
    env_categories_str = os.environ.get("ARENA_CACHE_CATEGORIES", "")
    if env_categories_str:
        env_categories = [cat.strip().lower() for cat in env_categories_str.split(',') if cat.strip()]
    
    # RU: Определяем режим (приоритет: нода > .env > default)
    mode = categories_mode
    if not mode and "ARENA_CACHE_CATEGORIES_MODE" in os.environ:
        mode = os.environ["ARENA_CACHE_CATEGORIES_MODE"]
    if not mode:
        mode = "extend"
    
    # RU: Выбираем источник категорий (приоритет: нода > .env > default)
    source_categories = node_categories if node_categories else (env_categories if env_categories else [])
    
    # RU: Фильтруем только известные категории
    valid_categories = [cat for cat in source_categories if cat in KNOWN_CATEGORIES]
    unknown_categories = [cat for cat in source_categories if cat not in KNOWN_CATEGORIES]
    
    if unknown_categories and verbose:
        print(f"[ArenaAutoCache] Unknown categories ignored: {', '.join(unknown_categories)}")
    
    # RU: Вычисляем эффективные категории
    if mode == "override":
        effective = valid_categories if valid_categories else DEFAULT_WHITELIST
    else:  # extend
        effective = list(set(DEFAULT_WHITELIST + valid_categories))
    
    # RU: Сортируем для консистентности
    effective.sort()
    
    if verbose:
        print(f"[ArenaAutoCache] Cache categories mode: {mode}; effective: {', '.join(effective)}")
    
    return effective

def _load_env_file():
    """RU: Загружает настройки из user/arena_autocache.env если файл существует."""
    env_file = Path("user/arena_autocache.env")
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            print(f"[ArenaAutoCache] Loaded env from {env_file}")
        except Exception as e:
            print(f"[ArenaAutoCache] Error loading env file: {e}")

def _save_env_file(kv: Dict[str, str], remove_keys: List[str] = None):
    """RU: Сохраняет настройки в user/arena_autocache.env с поддержкой удаления ключей."""
    try:
        env_dir = Path("user")
        env_dir.mkdir(exist_ok=True)
        env_file = env_dir / "arena_autocache.env"
        
        # RU: Читаем существующие настройки
        existing_settings = {}
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
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
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# Arena AutoCache Environment Settings\n")
            f.write("# Generated automatically - do not edit manually\n\n")
            for key, value in existing_settings.items():
                f.write(f"{key}={value}\n")
        
        print(f"[ArenaAutoCache] Saved env to {env_file}")
    except Exception as e:
        print(f"[ArenaAutoCache] Error saving env file: {e}")

@dataclass
class CacheSettings:
    """RU: Настройки кэширования."""
    root: Path
    min_size_mb: float
    max_cache_gb: float
    verbose: bool
    auto_patch: bool
    effective_categories: List[str]

def _init_settings(cache_root: str = "", min_size_mb: float = 10.0, max_cache_gb: float = 0.0, 
                  verbose: bool = False, auto_patch: bool = False, cache_categories: str = "", 
                  categories_mode: str = "extend") -> CacheSettings:
    """RU: Инициализирует настройки кэширования с резолвингом путей по умолчанию."""
    global _settings
    
    # RU: Определяем корневую папку кэша
    if cache_root:
        root = Path(cache_root)
    else:
        # RU: Пути по умолчанию для разных ОС
        if platform.system() == "Windows":
            root = Path("C:/ComfyUI/cache")
        else:
            root = Path.home() / ".cache/comfyui/arena"
    
    # RU: Вычисляем эффективные категории
    effective_categories = _compute_effective_categories(cache_categories, categories_mode, verbose)
    
    # RU: Создаем структуру папок только для эффективных категорий
    for category in effective_categories:
        (root / category).mkdir(parents=True, exist_ok=True)
    
    _settings = CacheSettings(
        root=root,
        min_size_mb=min_size_mb,
        max_cache_gb=max_cache_gb,
        verbose=verbose,
        auto_patch=auto_patch,
        effective_categories=effective_categories
    )
    
    # RU: Логируем настройки
    max_size_str = f"{max_cache_gb}GB" if max_cache_gb > 0 else "unlimited"
    print(f"[ArenaAutoCache] Cache root: {root} / Min file size: {min_size_mb}MB / Max cache size: {max_size_str} / Verbose: {1 if verbose else 0}")
    
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
            if not hasattr(folder_paths, 'get_full_path_origin'):
                folder_paths.get_full_path_origin = original_get_full_path
            
            def patched_get_folder_paths(folder_name: str) -> List[str]:
                """RU: Патченная функция get_folder_paths с добавлением кэша."""
                original_paths = original_get_folder_paths(folder_name)
                
                # RU: Добавляем путь кэша только для эффективных категорий
                if folder_name in _settings.effective_categories:
                    cache_path = str(_settings.root / folder_name)
                    if cache_path not in original_paths:
                        original_paths = [cache_path] + original_paths
                        if _settings.verbose:
                            print(f"[ArenaAutoCache] Added cache path for {folder_name}: {cache_path}")
                
                return original_paths
            
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
                            # RU: Планируем копирование в фоне только для существующих файлов
                            _schedule_cache_copy(folder_name, filename, original_path)
                            if _settings.verbose:
                                print(f"[ArenaAutoCache] Cache miss: {filename}")
                            return original_path
                        elif _settings.verbose:
                            print(f"[ArenaAutoCache] Skipping non-existent file: {filename}")
                    except Exception as e:
                        if _settings.verbose:
                            print(f"[ArenaAutoCache] Error resolving {filename}: {e}")
                
                # RU: Для неэффективных категорий или при ошибках - делегируем оригиналу
                return folder_paths.get_full_path_origin(folder_name, filename)
            
            # RU: Применяем патчи
            folder_paths.get_folder_paths = patched_get_folder_paths
            folder_paths.get_full_path = patched_get_full_path
            
            _folder_paths_patched = True
            print("[ArenaAutoCache] Applied folder_paths patch")
            
        except Exception as e:
            print(f"[ArenaAutoCache] Failed to apply folder_paths patch: {e}")
            raise

def _copy_worker():
    """RU: Воркер для фонового копирования файлов."""
    global _copy_status, _scheduled_tasks
    
    while True:
        try:
            category, filename, source_path = _copy_queue.get()
            
            # RU: Удаляем из запланированных под локом
            task_key = (category, filename)
            with _scheduled_lock:
                _scheduled_tasks.discard(task_key)
            
            try:
                source_file = Path(source_path)
                if not source_file.exists():
                    continue
                
                # RU: Проверяем размер файла
                file_size_mb = source_file.stat().st_size / (1024 * 1024)
                if file_size_mb < _settings.min_size_mb:
                    if _settings.verbose:
                        print(f"[ArenaAutoCache] Skipping small file: {filename} ({file_size_mb:.1f} MB)")
                    continue
                
                # RU: Создаем папку кэша
                cache_dir = _settings.root / category
                cache_dir.mkdir(parents=True, exist_ok=True)
                
                # RU: Копируем файл с временным именем
                cache_file = cache_dir / filename
                if not cache_file.exists():
                    temp_file = cache_file.with_suffix(cache_file.suffix + '.part')
                    try:
                        shutil.copy2(source_file, temp_file)
                        temp_file.rename(cache_file)
                        
                        if _settings.verbose:
                            print(f"[ArenaAutoCache] Caching: {filename}")
                        
                        # RU: Обновляем статистику
                        _copy_status["completed_jobs"] += 1
                        _copy_status["current_file"] = filename
                        _copy_status["last_update"] = _now()
                        
                        # RU: Проверяем лимит кэша и очищаем если нужно
                        if _settings.max_cache_gb > 0:
                            _prune_cache_if_needed()
                            
                    except Exception as e:
                        if temp_file.exists():
                            temp_file.unlink()
                        raise e
                
            except Exception as e:
                print(f"[ArenaAutoCache] Error caching {filename}: {e}")
                _copy_status["failed_jobs"] += 1
            finally:
                _copy_queue.task_done()
                
        except Exception as e:
            print(f"[ArenaAutoCache] Error in copy worker: {e}")
            _copy_queue.task_done()

def _ensure_copy_thread():
    """RU: Запускает поток для фонового копирования."""
    global _copy_thread_started
    
    if not _copy_thread_started:
        copy_thread = threading.Thread(target=_copy_worker, daemon=True)
        copy_thread.start()
        _copy_thread_started = True
        print("[ArenaAutoCache] Started background copy thread")

def _schedule_cache_copy(category: str, filename: str, source_path: str):
    """RU: Планирует копирование файла в кэш с потокобезопасной дедупликацией."""
    task_key = (category, filename)
    
    # RU: Проверяем дедупликацию под локом
    with _scheduled_lock:
        if task_key in _scheduled_tasks:
            return
        
        try:
            _ensure_copy_thread()
            _scheduled_tasks.add(task_key)
            _copy_queue.put((category, filename, source_path))
            _copy_status["total_jobs"] += 1
            
            if _settings.verbose:
                print(f"[ArenaAutoCache] Scheduled cache copy: {filename}")
        except Exception as e:
            print(f"[ArenaAutoCache] Error scheduling cache for {filename}: {e}")

def _get_cache_size_gb() -> float:
    """RU: Вычисляет общий размер кэша в GB."""
    total_size = 0
    for file_path in _settings.root.rglob('*'):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    return total_size / (1024 * 1024 * 1024)

def _prune_cache_if_needed():
    """RU: Очищает кэш если превышен лимит размера."""
    if _settings.max_cache_gb <= 0:
        return
    
    current_size = _get_cache_size_gb()
    if current_size <= _settings.max_cache_gb:
        return
    
    target_size = _settings.max_cache_gb * 0.95  # RU: Очищаем до 95% от лимита
    
    # RU: Собираем все файлы с временными метками
    files_with_mtime = []
    for file_path in _settings.root.rglob('*'):
        if file_path.is_file() and not file_path.name.endswith('.part'):
            files_with_mtime.append((file_path.stat().st_mtime, file_path))
    
    # RU: Сортируем по времени модификации (старые сначала)
    files_with_mtime.sort(key=lambda x: x[0])
    
    removed_count = 0
    removed_size = 0
    
    for mtime, file_path in files_with_mtime:
        if current_size <= target_size:
            break
        
        try:
            file_size = file_path.stat().st_size
            file_path.unlink()
            current_size -= file_size / (1024 * 1024 * 1024)
            removed_size += file_size
            removed_count += 1
        except Exception as e:
            if _settings.verbose:
                print(f"[ArenaAutoCache] Error removing {file_path}: {e}")
    
    if removed_count > 0:
        removed_mb = removed_size / (1024 * 1024)
        print(f"[ArenaAutoCache] Pruned {removed_count} files, freed {removed_mb:.1f} MB")

def _clear_cache_folder():
    """RU: Очищает папку кэша с проверками безопасности."""
    try:
        cache_path = _settings.root.resolve()
        
        # RU: Проверки безопасности
        if not cache_path.exists() or not cache_path.is_dir():
            return "Error: Cache path does not exist or is not a directory"
        
        # RU: Проверяем, что это не корень диска
        if cache_path == Path("/") or cache_path == Path("C:/") or cache_path == Path("C:\\"):
            return "Error: Cannot delete root directory"
        
        # RU: Проверяем UNC/сетевые пути
        if str(cache_path).startswith('\\\\'):
            return "Error: Cannot delete UNC/network paths"
        
        # RU: Проверяем глубину пути (минимум 2 сегмента)
        if len(cache_path.parts) < 2:
            return "Error: Cache path too short for safety"
        
        # RU: Подсчитываем размер перед очисткой
        total_size = 0
        file_count = 0
        for file_path in cache_path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
        
        # RU: Удаляем содержимое
        for item in cache_path.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        
        # RU: Пересоздаем структуру только для эффективных категорий
        for category in _settings.effective_categories:
            (cache_path / category).mkdir(parents=True, exist_ok=True)
        
        freed_mb = total_size / (1024 * 1024)
        return f"Cache cleared: freed {freed_mb:.1f} MB"
        
    except Exception as e:
        return f"Error clearing cache: {e}"

class ArenaAutoCacheSimple:
    """RU: Production-готовая нода кэширования с надежной обработкой .env, потокобезопасностью и безопасной очисткой."""

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        return {
            "required": {
                "cache_mode": (
                    ["OnDemand"],
                    {"default": "OnDemand"}
                ),
            },
            "optional": {
                "cache_root": (
                    "STRING",
                    {
                        "default": os.environ.get("ARENA_CACHE_ROOT", ""),
                        "description": "Cache root folder path (empty = auto-detect)",
                        "tooltip": "Root folder for cache. Empty = auto-detect based on OS."
                    }
                ),
                "min_size_mb": (
                    "FLOAT",
                    {
                        "default": float(os.environ.get("ARENA_CACHE_MIN_SIZE_MB", "10.0")),
                        "min": 0.1,
                        "max": 1000.0,
                        "step": 0.1,
                        "description": "Minimum file size for caching (MB)",
                        "tooltip": "Files smaller than this will be skipped."
                    }
                ),
                "max_cache_gb": (
                    "FLOAT",
                    {
                        "default": float(os.environ.get("ARENA_CACHE_MAX_GB", "0.0")),
                        "min": 0.0,
                        "max": 1000.0,
                        "step": 0.1,
                        "description": "Maximum cache size (GB, 0 = unlimited)",
                        "tooltip": "Automatic pruning when exceeded (LRU by mtime to 95%)."
                    }
                ),
                "auto_patch_on_start": (
                    "BOOLEAN",
                    {
                        "default": os.environ.get("ARENA_AUTOCACHE_AUTOPATCH", "0") == "1",
                        "description": "Auto-patch on start (toggle for env var)",
                        "tooltip": "Enable/disable autopatch via environment variable."
                    }
                ),
                "persist_env": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "description": "Persist settings to .env file",
                        "tooltip": "Save current settings to user/arena_autocache.env for future sessions."
                    }
                ),
                "verbose": (
                    "BOOLEAN",
                    {
                        "default": os.environ.get("ARENA_CACHE_VERBOSE", "0") == "1",
                        "description": "Enable verbose logging",
                        "tooltip": "Show detailed cache operations in console."
                    }
                ),
                "clear_cache_now": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "description": "Clear cache folder now",
                        "tooltip": "Wipe cache folder with safety checks, then auto-reset to False."
                    }
                ),
                "cache_categories": (
                    "STRING",
                    {
                        "default": os.environ.get("ARENA_CACHE_CATEGORIES", ""),
                        "description": "Additional cache categories (comma-separated)",
                        "tooltip": "Extra categories to cache beyond defaults. Empty = use defaults only."
                    }
                ),
                "categories_mode": (
                    ["extend", "override"],
                    {
                        "default": os.environ.get("ARENA_CACHE_CATEGORIES_MODE", "extend"),
                        "description": "Categories mode",
                        "tooltip": "extend = add to defaults, override = replace defaults"
                    }
                ),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result",)
    RETURN_DESCRIPTIONS = ("Cache operation result",)
    OUTPUT_TOOLTIPS = ("Shows cache operation status and results",)

    FUNCTION = "run"
    CATEGORY = "utils/Arena"
    DESCRIPTION = "Production-ready OnDemand-only node with robust env handling, thread-safety, safe pruning, and autopatch"
    OUTPUT_NODE = True

    def run(
        self,
        cache_mode: str = "OnDemand",
        cache_root: str = "",
        min_size_mb: float = 10.0,
        max_cache_gb: float = 0.0,
        auto_patch_on_start: bool = False,
        persist_env: bool = False,
        verbose: bool = False,
        clear_cache_now: bool = False,
        cache_categories: str = "",
        categories_mode: str = "extend",
    ):
        """RU: Основная функция ноды кэширования."""
        global _settings, _folder_paths_patched
        
        # RU: Применяем настройки к environment
        env_updates = {}
        remove_keys = []
        
        # RU: Настраиваем переменные окружения
        if cache_root:
            env_updates["ARENA_CACHE_ROOT"] = cache_root
        else:
            remove_keys.append("ARENA_CACHE_ROOT")
        
        env_updates["ARENA_CACHE_MIN_SIZE_MB"] = str(min_size_mb)
        env_updates["ARENA_CACHE_MAX_GB"] = str(max_cache_gb)
        env_updates["ARENA_CACHE_VERBOSE"] = "1" if verbose else "0"
        
        # RU: Настраиваем категории
        if cache_categories:
            env_updates["ARENA_CACHE_CATEGORIES"] = cache_categories
        else:
            remove_keys.append("ARENA_CACHE_CATEGORIES")
        
        env_updates["ARENA_CACHE_CATEGORIES_MODE"] = categories_mode
        
        if auto_patch_on_start:
            env_updates["ARENA_AUTOCACHE_AUTOPATCH"] = "1"
        else:
            remove_keys.append("ARENA_AUTOCACHE_AUTOPATCH")
        
        # RU: Применяем к environment
        for key, value in env_updates.items():
            os.environ[key] = value
        
        # RU: Сохраняем в .env если нужно
        if persist_env:
            _save_env_file(env_updates, remove_keys)
        
        # RU: Инициализируем настройки
        _settings = _init_settings(cache_root, min_size_mb, max_cache_gb, verbose, auto_patch_on_start, cache_categories, categories_mode)
        
        # RU: Применяем патч и запускаем воркер
        if not _folder_paths_patched:
            try:
                _apply_folder_paths_patch()
                _folder_paths_patched = True
            except Exception as e:
                return f"Error applying folder_paths patch: {e}"
        
        _ensure_copy_thread()
        
        # RU: Очистка кэша
        if clear_cache_now:
            result = _clear_cache_folder()
            return f"Cache cleared: {result}"
        
        # RU: OnDemand режим
        return "OnDemand enabled — models will be cached on first use"

# RU: Автопатч при импорте (критический порядок!)
_load_env_file()  # RU: Сначала загружаем .env

# RU: Отключаем автоматическое кэширование при старте
# Arena AutoCache должен кэшировать ТОЛЬКО модели, используемые в активном workflow
if os.environ.get("ARENA_AUTOCACHE_AUTOPATCH") == "1":
    try:
        _settings = _init_settings()
        _apply_folder_paths_patch()
        _ensure_copy_thread()
        print("[ArenaAutoCache] Autopatch on import enabled - OnDemand caching only")
    except Exception as e:
        print(f"[ArenaAutoCache] Error in autopatch on import: {e}")

# RU: Регистрация ноды
NODE_CLASS_MAPPINGS = {
    "ArenaAutoCache (simple)": ArenaAutoCacheSimple,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArenaAutoCache (simple)": "🅰️ Arena AutoCache (simple) v3.4.0",
}

print("[ArenaAutoCache] Loaded production-ready OnDemand-only node with robust env handling, thread-safety, safe pruning, and autopatch")
print("[ArenaAutoCache] OnDemand caching: models are cached ONLY when used in active workflows")