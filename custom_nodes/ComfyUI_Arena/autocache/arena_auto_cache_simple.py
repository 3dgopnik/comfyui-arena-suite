# EN identifiers; RU comments for clarity.
import os
import json
import time
import shutil
import threading
from dataclasses import dataclass, replace, field
from pathlib import Path
from types import ModuleType
from typing import Callable, Mapping, Optional, Sequence
from queue import Queue

LABELS: dict[str, str] = {
    "node.autocache": "🅰️ Arena AutoCache",
    "input.cache_root": "Cache root directory",
    "input.max_size_gb": "Maximum cache size (GB)",
    "input.enable": "Enable AutoCache",
    "input.verbose": "Verbose logging",
    "input.min_size_gb": "Minimum size for caching (GB)",
    "input.skip_hardcoded_paths": "Skip hardcoded paths",
    "input.category": "Model category",
    "input.categories": "Model categories to cache",
}

def t(key: str) -> str:
    """RU: Получение переведенного текста по ключу."""
    return LABELS.get(key, key)

@dataclass
class ArenaCacheSettings:
    """RU: Отражает текущие настройки кеша во время сессии."""
    root: Path
    max_gb: float
    enable: bool
    verbose: bool
    min_size_gb: float
    min_size_mb: float
    skip_hardcoded_paths: bool

def _initial_root() -> Path:
    """RU: Инициализация корневой папки кеша."""
    raw = os.environ.get("ARENA_CACHE_ROOT", "C:/ComfyUI/cache")
    return Path(raw)

def _initial_bool(name: str, default: bool) -> bool:
    """RU: Инициализация булевого значения из переменной окружения."""
    raw = os.environ.get(name, str(default))
    return raw.lower() in ("true", "1", "yes", "on")

def _initial_int(name: str, default: int) -> int:
    """RU: Инициализация целого числа из переменной окружения."""
    raw = os.environ.get(name, str(default))
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default

_settings = ArenaCacheSettings(
    root=_initial_root(),
    max_gb=max(0, _initial_int("ARENA_CACHE_MAX_GB", 300)),
    enable=_initial_bool("ARENA_CACHE_ENABLE", True),
    verbose=_initial_bool("ARENA_CACHE_VERBOSE", False),
    min_size_gb=float(os.environ.get("ARENA_CACHE_MIN_SIZE_GB", "1.0")),
    min_size_mb=float(os.environ.get("ARENA_CACHE_MIN_SIZE_MB", "1024.0")),
    skip_hardcoded_paths=_initial_bool("ARENA_CACHE_SKIP_HARDCODED", True),
)

if _settings.enable:
    try:
        _settings.root.mkdir(parents=True, exist_ok=True)
    except Exception as root_err:  # pragma: no cover - logging only
        print(f"[ArenaAutoCache] failed to prepare cache root {_settings.root}: {root_err}")

_folder_paths_module: Optional[ModuleType] = None
_orig_get_folder_paths: Optional[Callable[[str], list[str] | tuple[str, ...]]] = None
_orig_get_full_path: Optional[Callable[[str, str], Optional[str]]] = None
_folder_paths_patched = False

_session_hits = 0
_session_misses = 0
_session_trims = 0

_workflow_allowlist: set[tuple[str, str]] = set()

# RU: Глобальное состояние копирования для визуального индикатора
_copy_status: dict[str, object] = {
    "active_jobs": 0,
    "completed_jobs": 0,
    "failed_jobs": 0,
    "current_file": None,
    "progress_bytes": 0,
    "total_bytes": 0,
    "last_update": 0.0,
}

NODE_CLASS_MAPPINGS: dict[str, type] = {}
NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}

def _now() -> float:
    """RU: Текущее время в секундах."""
    return time.time()

def _duration_since(started: float) -> float:
    """RU: Продолжительность с момента started."""
    return _now() - started

def _apply_folder_paths_patch_locked():
    """RU: Применяет патч folder_paths для перехвата загрузки моделей."""
    global _folder_paths_patched, _folder_paths_module, _orig_get_folder_paths, _orig_get_full_path
    
    if _folder_paths_patched:
        return
    
    try:
        import folder_paths
        _folder_paths_module = folder_paths
        
        # Сохраняем оригинальные функции
        if hasattr(folder_paths, 'get_folder_paths'):
            _orig_get_folder_paths = folder_paths.get_folder_paths
        if hasattr(folder_paths, 'get_full_path'):
            _orig_get_full_path = folder_paths.get_full_path
        
        # Применяем патч
        def patched_get_folder_paths(folder_type: str) -> list[str] | tuple[str, ...]:
            """RU: Патчированная версия get_folder_paths с кешированием."""
            if not _settings.enable:
                return _orig_get_folder_paths(folder_type) if _orig_get_folder_paths else []
            
            # Получаем оригинальные пути
            original_paths = _orig_get_folder_paths(folder_type) if _orig_get_folder_paths else []
            
            # Добавляем путь к кешу
            cache_path = str(_settings.root / folder_type)
            if cache_path not in original_paths:
                return list(original_paths) + [cache_path]
            return original_paths
        
        def patched_get_full_path(folder_type: str, filename: str) -> Optional[str]:
            """RU: Патчированная версия get_full_path с проверкой кеша."""
            if not _settings.enable:
                return _orig_get_full_path(folder_type, filename) if _orig_get_full_path else None
            
            # Сначала проверяем кеш
            cache_path = _settings.root / folder_type / filename
            if cache_path.exists():
                if _settings.verbose:
                    print(f"[ArenaAutoCache] Cache hit: {filename}")
                global _session_hits
                _session_hits += 1
                return str(cache_path)
            
            # Если нет в кеше, используем оригинальную функцию
            original_path = _orig_get_full_path(folder_type, filename) if _orig_get_full_path else None
            if original_path and Path(original_path).exists():
                if _settings.verbose:
                    print(f"[ArenaAutoCache] Cache miss: {filename}")
                global _session_misses
                _session_misses += 1
                
                # Кешируем файл в фоне
                _schedule_cache_copy(folder_type, filename, original_path)
            
            return original_path
        
        # Применяем патчи
        folder_paths.get_folder_paths = patched_get_folder_paths
        folder_paths.get_full_path = patched_get_full_path
        
        _folder_paths_patched = True
        print(f"[ArenaAutoCache] Applied folder_paths patch")
        
    except Exception as e:
        print(f"[ArenaAutoCache] Failed to apply folder_paths patch: {e}")

def _schedule_cache_copy(folder_type: str, filename: str, source_path: str):
    """RU: Планирует копирование файла в кеш."""
    try:
        source_file = Path(source_path)
        if not source_file.exists():
            return
        
        # Проверяем размер файла
        file_size_mb = source_file.stat().st_size / (1024 * 1024)
        if file_size_mb < _settings.min_size_mb:
            if _settings.verbose:
                print(f"[ArenaAutoCache] Skipping small file: {filename} ({file_size_mb:.1f} MB)")
            return
        
        # Создаем папку кеша
        cache_dir = _settings.root / folder_type
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Копируем файл
        cache_file = cache_dir / filename
        if not cache_file.exists():
            if _settings.verbose:
                print(f"[ArenaAutoCache] Caching: {filename}")
            shutil.copy2(source_file, cache_file)
            
            # Обновляем статистику
            global _copy_status
            _copy_status["completed_jobs"] += 1
            _copy_status["current_file"] = filename
            _copy_status["last_update"] = _now()
            
    except Exception as e:
        print(f"[ArenaAutoCache] Error caching {filename}: {e}")
        global _copy_status
        _copy_status["failed_jobs"] += 1

class ArenaAutoCache:
    """RU: Упрощенная нода для автоматического кеширования моделей.

    Автоматически обнаруживает модели в текущем workflow и кеширует их.
    Одна нода для всех задач кеширования.
    """

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        return {
            "required": {},
            "optional": {
                "categories": (
                    "STRING",
                    {
                        "default": "checkpoints,loras,vaes,upscale_models,controlnet",
                        "description": "Model categories to cache",
                        "tooltip": "Comma-separated list of model categories to automatically cache",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result",)
    RETURN_DESCRIPTIONS = ("Cache operation result",)
    OUTPUT_TOOLTIPS = ("Shows which models were cached",)
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache"
    DESCRIPTION = "Automatically cache models from current workflow"
    OUTPUT_NODE = True

    def run(
        self,
        categories: str = "checkpoints,loras,vaes,upscale_models,controlnet"
    ):
        """Automatically detect and cache models from current workflow."""
        print("[ArenaAutoCache] Starting automatic model detection and caching")
        
        # Убеждаемся, что патч путей активен
        _apply_folder_paths_patch_locked()
        
        # Анализируем текущий canvas для поиска моделей
        found_models = self._analyze_current_canvas(categories)
        
        if not found_models:
            print("[ArenaAutoCache] No models found in current canvas")
            return json.dumps({
                "ok": False,
                "message": "No models found in current canvas",
                "details": [
                    "Add model loading nodes to your canvas first",
                    "Use Load Checkpoint, Load VAE, or other model nodes"
                ]
            }, ensure_ascii=False, indent=2)
        
        print(f"[ArenaAutoCache] Found {len(found_models)} models in current canvas")
        
        # Кешируем найденные модели
        print(f"[ArenaAutoCache] Starting cache process for {len(found_models)} models")
        cache_results = self._cache_models_with_progress(found_models)
        print(f"[ArenaAutoCache] Cache process completed. Results: {len(cache_results)}")
        
        # Формируем результат
        cached_count = len([r for r in cache_results if r["status"] == "cached"])
        skipped_count = len([r for r in cache_results if r["status"].startswith("skipped")])
        error_count = len([r for r in cache_results if r["status"] in ["error", "not_found"]])
        
        result = {
            "ok": True,
            "message": f"Successfully processed {len(found_models)} models",
            "models_found": len(found_models),
            "cached": cached_count,
            "skipped": skipped_count,
            "errors": error_count,
            "categories_checked": [cat.strip() for cat in categories.split(",")],
            "models": found_models,
            "cache_results": cache_results,
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)

    def _analyze_current_canvas(self, categories: str) -> list[dict]:
        """RU: Анализирует текущий canvas для поиска моделей."""
        categories_list = [cat.strip() for cat in categories.split(",")]
        found_models = []
        
        try:
            # Получаем папки с моделями
            try:
                from folder_paths import get_folder_paths
                model_folders = get_folder_paths()
            except (TypeError, ImportError):
                # Если get_folder_paths не работает, пробуем folder_paths напрямую
                try:
                    from folder_paths import folder_paths
                    model_folders = folder_paths
                except ImportError:
                    print("[ArenaAutoCache] Could not access folder_paths")
                    return []
            
            # Ищем модели в папках
            for category in categories_list:
                if category in model_folders:
                    category_path = Path(model_folders[category])
                    if category_path.exists():
                        for model_file in category_path.iterdir():
                            if model_file.is_file() and model_file.suffix.lower() in ['.ckpt', '.safetensors', '.pt', '.pth', '.bin']:
                                found_models.append({
                                    "name": model_file.name,
                                    "category": category,
                                    "path": str(model_file),
                                    "size_mb": model_file.stat().st_size / (1024 * 1024)
                                })
            
            return found_models
            
        except Exception as e:
            print(f"[ArenaAutoCache] Error analyzing canvas: {e}")
            return []

    def _cache_models_with_progress(self, models: list[dict]) -> list[dict]:
        """RU: Кеширует модели с отображением прогресса."""
        results = []
        
        for model in models:
            try:
                source_path = Path(model["path"])
                if not source_path.exists():
                    results.append({
                        "name": model["name"],
                        "status": "not_found",
                        "message": f"Source file not found: {model['path']}"
                    })
                    continue
                
                # Проверяем размер файла
                file_size_mb = source_path.stat().st_size / (1024 * 1024)
                if file_size_mb < _settings.min_size_mb:
                    results.append({
                        "name": model["name"],
                        "status": "skipped_small",
                        "message": f"File too small: {file_size_mb:.1f} MB < {_settings.min_size_mb} MB"
                    })
                    continue
                
                # Создаем папку кеша
                cache_dir = _settings.root / model["category"]
                cache_dir.mkdir(parents=True, exist_ok=True)
                
                # Копируем файл
                cache_file = cache_dir / model["name"]
                if cache_file.exists():
                    results.append({
                        "name": model["name"],
                        "status": "skipped_exists",
                        "message": "Already cached"
                    })
                    continue
                
                shutil.copy2(source_path, cache_file)
                results.append({
                    "name": model["name"],
                    "status": "cached",
                    "message": f"Cached successfully ({file_size_mb:.1f} MB)"
                })
                
            except Exception as e:
                results.append({
                    "name": model["name"],
                    "status": "error",
                    "message": f"Error: {str(e)}"
                })
        
        return results

# Версия нод
ARENA_NODES_VERSION = "v2.23"

NODE_CLASS_MAPPINGS.update(
    {
        # Единственная нода Arena AutoCache - упрощенная версия
        "ArenaAutoCache": ArenaAutoCache,
        f"ArenaAutoCache {ARENA_NODES_VERSION}": ArenaAutoCache,
    }
)

NODE_DISPLAY_NAME_MAPPINGS.update(
    {
        # Единственная нода Arena AutoCache - упрощенная версия
        "ArenaAutoCache": "🅰️ Arena AutoCache",
        f"ArenaAutoCache {ARENA_NODES_VERSION}": f"🅰️ Arena AutoCache {ARENA_NODES_VERSION}",
    }
)
