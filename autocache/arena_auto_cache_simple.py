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
DEFAULT_WHITELIST = [
    "checkpoints", "loras", "clip", "clip_vision", "text_encoders", "vae", 
    "controlnet", "diffusion_models", "upscale_models", "embeddings"
]
KNOWN_CATEGORIES = [
    # RU: Основные категории моделей ComfyUI
    "checkpoints", "loras", "clip", "clip_vision", "text_encoders", "vae", "controlnet", 
    "upscale_models", "embeddings", "hypernetworks", "ipadapter", "gligen", 
    "animatediff_models", "t2i_adapter", "diffusion_models", "ultralytics", 
    "insightface", "inpaint", "pix2pix", "sams", "pulid",
    
    # RU: Дополнительные категории из лога ComfyUI
    "llm", "ipadapter_encoders", "animatediff", "download_model_base",
    
    # RU: Специальные категории для GGUF и других форматов
    "gguf_models", "unet_models", "style_models", "flux_models",
    
    # RU: Категории для восстановления лиц и детекции
    "facerestore_models", "antelopev2", "bbox", "segm",
    
    # RU: Категории для апскейлинга
    "apisr", "stablesr", "supir", "ccsr",
    
    # RU: Категории для видео и анимации
    "video_models", "motion_models", "temporal_models"
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
    if cache_categories and cache_categories.strip():
        node_categories = [cat.strip().lower() for cat in cache_categories.split(',') if cat.strip()]
    
    # RU: Парсим категории из .env
    env_categories = []
    env_categories_str = os.environ.get("ARENA_CACHE_CATEGORIES", "")
    if env_categories_str and env_categories_str.strip():
        env_categories = [cat.strip().lower() for cat in env_categories_str.split(',') if cat.strip()]
    
    # RU: Определяем режим (приоритет: нода > .env > default)
    mode = categories_mode
    if not mode and "ARENA_CACHE_CATEGORIES_MODE" in os.environ:
        mode = os.environ["ARENA_CACHE_CATEGORIES_MODE"]
    if not mode:
        mode = "extend"
    
    # RU: Выбираем источник категорий (приоритет: нода > .env > default)
    source_categories = node_categories if node_categories else (env_categories if env_categories else [])
    
    # RU: Если категории пустые - кэшируем все известные категории
    if not source_categories:
        effective = KNOWN_CATEGORIES.copy()
        if verbose:
            print(f"[ArenaAutoCache] No categories specified - caching ALL known categories: {len(effective)} categories")
    else:
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
    effective_categories: List[str]

def _init_settings(cache_root: str = "", min_size_mb: float = 10.0, max_cache_gb: float = 100.0, 
                  verbose: bool = False, cache_categories: str = "checkpoints,loras", 
                  categories_mode: str = "extend") -> CacheSettings:
    """RU: Инициализирует настройки кэширования с резолвингом путей по умолчанию."""
    global _settings
    
    # RU: Загружаем .env файл
    _load_env_file()
    
    # RU: Резолвим корень кэша
    if cache_root:
        root = Path(cache_root)
    else:
        root = Path(os.environ.get("ARENA_CACHE_ROOT", Path.home() / "Documents" / "ComfyUI-Cache"))
    
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
        effective_categories=effective_categories
    )
    
    if verbose:
        print(f"[ArenaAutoCache] Cache root: {root} / Min file size: {min_size_mb}MB / Max cache size: {max_cache_gb}GB / Verbose: {verbose}")
    
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
                        # RU: Планируем копирование в фоне
                        _schedule_copy_task(folder_name, filename, original_path, str(cache_path))
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
            category, filename, source_path, cache_path = _copy_queue.get(timeout=1)
            
            _copy_status["current_file"] = filename
            _copy_status["total_jobs"] += 1
            
            try:
                # RU: Проверяем размер файла
                source_size = os.path.getsize(source_path)
                if source_size < _settings.min_size_mb * 1024 * 1024:
                    if _settings.verbose:
                        print(f"[ArenaAutoCache] Skipping {filename}: too small ({source_size / 1024 / 1024:.1f}MB)")
                    continue
                
                # RU: Проверяем, не существует ли уже в кэше
                if os.path.exists(cache_path):
                    if _settings.verbose:
                        print(f"[ArenaAutoCache] Already cached: {filename}")
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
            
        except:
            break

def _prune_cache_if_needed():
    """RU: Очищает кэш при превышении лимита (LRU)."""
    try:
        # RU: Получаем размер кэша
        total_size = 0
        all_files = []
        
        for category in _settings.effective_categories:
            category_path = _settings.root / category
            if category_path.exists():
                for file_path in category_path.iterdir():
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
            
            for file_path, size, _ in all_files:
                if current_size <= target_size:
                    break
                
                try:
                    file_path.unlink()
                    current_size -= size
                    if _settings.verbose:
                        print(f"[ArenaAutoCache] Pruned: {file_path.name}")
                except Exception as e:
                    if _settings.verbose:
                        print(f"[ArenaAutoCache] Error pruning {file_path.name}: {e}")
    
    except Exception as e:
        if _settings.verbose:
            print(f"[ArenaAutoCache] Error pruning cache: {e}")

def _clear_cache_folder():
    """RU: Очищает папку кэша с безопасными проверками."""
    try:
        if not _settings.root.exists():
            return
        
        # RU: Подсчитываем размер перед очисткой
        total_size = 0
        for category in _settings.effective_categories:
            category_path = _settings.root / category
            if category_path.exists():
                for file_path in category_path.iterdir():
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
        
        # RU: Очищаем только эффективные категории
        for category in _settings.effective_categories:
            category_path = _settings.root / category
            if category_path.exists():
                for file_path in category_path.iterdir():
                    if file_path.is_file():
                        file_path.unlink()
        
        # RU: Пересоздаем папки
        for category in _settings.effective_categories:
            (_settings.root / category).mkdir(exist_ok=True)
        
        freed_mb = total_size / 1024 / 1024
        print(f"[ArenaAutoCache] Cleared cache: {freed_mb:.1f}MB freed")
        
    except Exception as e:
        print(f"[ArenaAutoCache] Error clearing cache: {e}")

def _patch_hardcoded_paths():
    """RU: Патчит жестко прописанные пути для перенаправления в кэш."""
    import os
    
    hardcoded_paths = [
        "C:\\ComfyUI\\models\\ultralytics\\bbox",
        "C:\\ComfyUI\\models\\ultralytics\\segm",
    ]
    
    for hardcoded_path in hardcoded_paths:
        if os.path.exists(hardcoded_path):
            if 'ultralytics' in hardcoded_path:
                category = 'ultralytics'
            else:
                category = 'checkpoints'
            
            cache_path = _settings.root / category
            if cache_path.exists():
                try:
                    if os.path.exists(hardcoded_path):
                        import shutil
                        shutil.rmtree(hardcoded_path)
                    
                    os.symlink(str(cache_path), hardcoded_path)
                    if _settings.verbose:
                        print(f"[ArenaAutoCache] Created symlink: {hardcoded_path} -> {cache_path}")
                except Exception as e:
                    if _settings.verbose:
                        print(f"[ArenaAutoCache] Failed to create symlink: {e}")
    
    original_exists = os.path.exists
    
    def patched_exists(path):
        result = original_exists(path)
        
        if not result and path.startswith("C:\\ComfyUI\\models\\"):
            if 'ultralytics' in path:
                category = 'ultralytics'
            elif 'checkpoints' in path:
                category = 'checkpoints'
            elif 'loras' in path:
                category = 'loras'
            else:
                category = 'checkpoints'
            
            filename = os.path.basename(path)
            cache_path = _settings.root / category / filename
            if cache_path.exists():
                if _settings.verbose:
                    print(f"[ArenaAutoCache] Redirecting hardcoded path: {path} -> {cache_path}")
                return True
        
        return result
    
    os.path.exists = patched_exists

# RU: Загружаем настройки при импорте
_load_env_file()

# RU: Автопатч при загрузке модуля
if os.environ.get("ARENA_AUTOCACHE_AUTOPATCH") == "1":
    try:
        # RU: Инициализируем настройки для автопатча
        _settings = _init_settings(
            cache_root=os.environ.get("ARENA_CACHE_ROOT", ""),
            min_size_mb=float(os.environ.get("ARENA_CACHE_MIN_SIZE_MB", "10.0")),
            max_cache_gb=float(os.environ.get("ARENA_CACHE_MAX_GB", "100.0")),
            verbose=os.environ.get("ARENA_CACHE_VERBOSE", "0") == "1",
            cache_categories=os.environ.get("ARENA_CACHE_CATEGORIES", ""),
            categories_mode=os.environ.get("ARENA_CACHE_CATEGORIES_MODE", "extend")
        )
        
        # RU: Применяем патч
        _apply_folder_paths_patch()
        
        # RU: Запускаем фоновый поток
        if not _copy_thread_started:
            copy_thread = threading.Thread(target=_copy_worker, daemon=True)
            copy_thread.start()
            _copy_thread_started = True
        
        print("[ArenaAutoCache] Autopatch enabled - caching models automatically")
        
    except Exception as e:
        print(f"[ArenaAutoCache] Autopatch error: {e}")

class ArenaAutoCacheSimple:
    """RU: Простая нода Arena AutoCache для кэширования моделей."""
    
    def __init__(self):
        self.description = "🅰️ Arena AutoCache (simple) v3.6.4 - Production-ready node with autopatch and OnDemand caching, robust env handling, thread-safety, and safe pruning"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "cache_root": ("STRING", {"default": "", "multiline": False}),
                "min_size_mb": ("FLOAT", {"default": 10.0, "min": 0.1, "max": 1000.0, "step": 0.1}),
                "max_cache_gb": ("FLOAT", {"default": 100.0, "min": 1.0, "max": 1000.0, "step": 1.0}),
                "verbose": ("BOOLEAN", {"default": True}),
                "cache_categories": ("STRING", {"default": "checkpoints,loras", "multiline": False}),
                "categories_mode": (["extend", "override"], {"default": "extend"}),
                "clear_cache_now": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "run"
    CATEGORY = "Arena"
    
    def run(self, cache_root: str = "", min_size_mb: float = 10.0, max_cache_gb: float = 100.0, 
            verbose: bool = True, cache_categories: str = "checkpoints,loras", 
            categories_mode: str = "extend", clear_cache_now: bool = False):
        """RU: Основная функция ноды."""
        global _settings, _copy_thread_started
        
        try:
            # RU: Обновляем переменные окружения
            os.environ["ARENA_CACHE_ROOT"] = cache_root
            os.environ["ARENA_CACHE_VERBOSE"] = "1" if verbose else "0"
            os.environ["ARENA_CACHE_CATEGORIES"] = cache_categories
            os.environ["ARENA_CACHE_CATEGORIES_MODE"] = categories_mode
            
            # RU: Инициализируем настройки
            _settings = _init_settings(cache_root, min_size_mb, max_cache_gb, verbose, cache_categories, categories_mode)
            
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
            
            # RU: Патчим жестко прописанные пути
            _patch_hardcoded_paths()
            
            # RU: Очищаем кэш если запрошено
            if clear_cache_now:
                _clear_cache_folder()
            
            # RU: Сохраняем настройки в .env
            _save_env_file({
                "ARENA_CACHE_ROOT": cache_root,
                "ARENA_CACHE_MIN_SIZE_MB": str(min_size_mb),
                "ARENA_CACHE_MAX_GB": str(max_cache_gb),
                "ARENA_CACHE_VERBOSE": "1" if verbose else "0",
                "ARENA_CACHE_CATEGORIES": cache_categories,
                "ARENA_CACHE_CATEGORIES_MODE": categories_mode,
            })
            
            # RU: Обновляем глобальные настройки для autopatch
            if _settings:
                _settings.root = Path(cache_root) if cache_root else Path(os.environ.get("ARENA_CACHE_ROOT", Path.home() / "Documents" / "ComfyUI-Cache"))
                _settings.min_size_mb = min_size_mb
                _settings.max_cache_gb = max_cache_gb
                _settings.verbose = verbose
                _settings.effective_categories = _compute_effective_categories(cache_categories, categories_mode, verbose)
            
            status = f"Arena AutoCache initialized: {len(_settings.effective_categories)} categories, {_settings.max_cache_gb}GB limit"
            if verbose:
                print(f"[ArenaAutoCache] {status}")
            
            return (status,)
            
        except Exception as e:
            error_msg = f"Arena AutoCache error: {str(e)}"
            print(f"[ArenaAutoCache] {error_msg}")
            return (error_msg,)

# RU: Регистрация ноды
NODE_CLASS_MAPPINGS = {
    "ArenaAutoCache (simple)": ArenaAutoCacheSimple,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArenaAutoCache (simple)": "🅰️ Arena AutoCache (simple) v3.6.4",
}

print("[ArenaAutoCache] Loaded production-ready node with autopatch and OnDemand caching")
print("[ArenaAutoCache] Autopatch: models are cached automatically on startup")
print("[ArenaAutoCache] OnDemand: models are cached when node is used in workflows")
print("[ArenaAutoCache] Loaded simplified version - single node for model caching")
print("[Arena Suite] Loaded Arena AutoCache Base")