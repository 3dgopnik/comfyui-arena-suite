#!/usr/bin/env python3
"""
Arena AutoCache v3.3.0-optimized - Simplified OnDemand Only Version
RU: Упрощенная версия только с OnDemand режимом кеширования
"""

import json
import os
import shutil
import threading
import time
from pathlib import Path
from queue import Queue
from typing import Dict, List, Optional

# RU: Глобальные настройки кеширования
_settings = None
_folder_paths_patched = False

# RU: Глобальное состояние для неблокирующего копирования
_copy_queue = Queue()
_copy_thread_started = False
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

def _init_settings():
    """RU: Инициализация настроек кеширования."""
    global _settings
    
    if _settings is None:
        from dataclasses import dataclass
        
        @dataclass
        class CacheSettings:
            root: Path = Path(os.environ.get("ARENA_CACHE_ROOT", "C:/ComfyUI/cache"))
            min_size_mb: float = float(os.environ.get("ARENA_CACHE_MIN_SIZE_MB", "10.0"))
            verbose: bool = os.environ.get("ARENA_CACHE_VERBOSE", "false").lower() == "true"
        
        _settings = CacheSettings()
        print(f"[ArenaAutoCache] Cache settings: root={_settings.root}, min_size={_settings.min_size_mb}MB, verbose={_settings.verbose}")
    
    return _settings

def _apply_folder_paths_patch_locked():
    """RU: Применяет патч folder_paths для перехвата загрузки моделей."""
    global _folder_paths_patched
    
    if _folder_paths_patched:
        return
    
    try:
        import folder_paths
        
        # RU: Сохраняем оригинальные функции
        original_get_folder_paths = folder_paths.get_folder_paths
        original_get_full_path = folder_paths.get_full_path
        
        def patched_get_folder_paths(folder_name: str) -> List[str]:
            """RU: Патченная функция get_folder_paths с добавлением кеша."""
            original_paths = original_get_folder_paths(folder_name)
            
            # RU: Добавляем путь кеша для данной категории
            cache_path = str(_settings.root / folder_name)
            if cache_path not in original_paths:
                original_paths = [cache_path] + original_paths
                if _settings.verbose:
                    print(f"[ArenaAutoCache] Added cache path for {folder_name}: {cache_path}")
            
            return original_paths
        
        def patched_get_full_path(folder_name: str, filename: str) -> str:
            """RU: Патченная функция get_full_path с кешированием."""
            # RU: Сначала пробуем найти в оригинальных путях
            try:
                original_path = original_get_full_path(folder_name, filename)
                if os.path.exists(original_path):
                    # RU: Если файл найден в оригинальном пути, кешируем его
                    _schedule_cache_copy(folder_name, filename, original_path)
                    return original_path
            except Exception:
                pass
            
            # RU: Если не найден, пробуем найти в кеше
            cache_path = _settings.root / folder_name / filename
            if cache_path.exists():
                if _settings.verbose:
                    print(f"[ArenaAutoCache] Cache hit: {filename}")
                return str(cache_path)
            
            # RU: Если не найден нигде, возвращаем оригинальный путь
            return original_get_full_path(folder_name, filename)
        
        # RU: Применяем патчи
        folder_paths.get_folder_paths = patched_get_folder_paths
        folder_paths.get_full_path = patched_get_full_path
        
        _folder_paths_patched = True
        print("[ArenaAutoCache] Applied folder_paths patch")
        
    except Exception as e:
        print(f"[ArenaAutoCache] Failed to apply folder_paths patch: {e}")
        raise

def _copy_worker():
    """RU: Воркер для неблокирующего копирования файлов."""
    global _copy_status
    
    while True:
        try:
            folder_type, filename, source_path = _copy_queue.get()
            
            try:
                source_file = Path(source_path)
                if not source_file.exists():
                    continue
                
                # Проверяем размер файла
                file_size_mb = source_file.stat().st_size / (1024 * 1024)
                if file_size_mb < _settings.min_size_mb:
                    if _settings.verbose:
                        print(f"[ArenaAutoCache] Skipping small file: {filename} ({file_size_mb:.1f} MB)")
                    continue
                
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
                    _copy_status["completed_jobs"] += 1
                    _copy_status["current_file"] = filename
                    _copy_status["last_update"] = _now()
                    
            except Exception as e:
                print(f"[ArenaAutoCache] Error caching {filename}: {e}")
                _copy_status["failed_jobs"] += 1
            finally:
                _copy_queue.task_done()
                
        except Exception as e:
            print(f"[ArenaAutoCache] Error in copy worker: {e}")
            _copy_queue.task_done()

def _ensure_copy_thread():
    """RU: Запускает поток для неблокирующего копирования."""
    global _copy_thread_started
    
    if not _copy_thread_started:
        copy_thread = threading.Thread(target=_copy_worker, daemon=True)
        copy_thread.start()
        _copy_thread_started = True
        print("[ArenaAutoCache] Started background copy thread")

def _schedule_cache_copy(folder_type: str, filename: str, source_path: str):
    """RU: Планирует копирование файла в кеш (неблокирующее)."""
    try:
        _ensure_copy_thread()
        _copy_queue.put((folder_type, filename, source_path))
        if _settings.verbose:
            print(f"[ArenaAutoCache] Scheduled cache copy: {filename}")
    except Exception as e:
        print(f"[ArenaAutoCache] Error scheduling cache for {filename}: {e}")

class ArenaAutoCache:
    """RU: Упрощенная нода для автоматического кеширования моделей в режиме OnDemand."""

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
                        "tooltip": "Comma-separated list of model categories to automatically cache.",
                    },
                ),
                "min_size_mb": (
                    "FLOAT",
                    {
                        "default": float(os.environ.get("ARENA_CACHE_MIN_SIZE_MB", "10.0")),
                        "min": 0.1,
                        "max": 1000.0,
                        "step": 0.1,
                        "description": "Minimum file size for caching (MB)",
                        "tooltip": "Files smaller than this size will be skipped. Set via ARENA_CACHE_MIN_SIZE_MB env var.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result",)
    RETURN_DESCRIPTIONS = ("Cache operation result",)
    OUTPUT_TOOLTIPS = ("Shows which models were cached",)

    FUNCTION = "run"
    CATEGORY = "🅰️ Arena/AutoCache"
    DESCRIPTION = "OnDemand model caching with folder_paths patching for transparent caching."
    OUTPUT_NODE = True

    def run(
        self,
        categories: str = "checkpoints,loras,vaes,upscale_models,controlnet",
        min_size_mb: float = None,
    ):
        """RU: Автоматически определяет и кеширует модели в режиме OnDemand."""
        global _folder_paths_patched, _settings
        
        # RU: Инициализируем настройки
        _init_settings()
        
        print("[ArenaAutoCache] Starting OnDemand caching")
        
        # RU: Обновляем минимальный размер файла если указан
        if min_size_mb is not None:
            old_min_size = _settings.min_size_mb
            _settings.min_size_mb = min_size_mb
            print(f"[ArenaAutoCache] Updated minimum file size: {old_min_size} MB -> {min_size_mb} MB")
        
        # RU: OnDemand режим - патч folder_paths + get_full_path
        print("[ArenaAutoCache] OnDemand caching enabled - models will be cached on first use")
        
        # RU: Применяем патч folder_paths (проверенный метод)
        if not _folder_paths_patched:
            try:
                _apply_folder_paths_patch_locked()
                _folder_paths_patched = True
                print("[ArenaAutoCache] Applied folder_paths patch")
            except Exception as e:
                print(f"[ArenaAutoCache] Failed to apply folder_paths patch: {e}")
                return json.dumps({
                    "ok": False,
                    "message": f"Failed to apply folder_paths patch: {e}",
                    "description": "OnDemand caching requires folder_paths patching"
                }, ensure_ascii=False, indent=2)
        
        return json.dumps({
            "ok": True,
            "message": "OnDemand caching enabled - models will be cached on first use",
            "description": "Models will be cached transparently when first accessed via patched get_full_path",
            "min_size_mb": _settings.min_size_mb,
            "categories": categories
        }, ensure_ascii=False, indent=2)

# RU: Регистрация ноды
NODE_CLASS_MAPPINGS = {
    "ArenaAutoCache Base": ArenaAutoCache,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArenaAutoCache Base": "🅰️ Arena AutoCache Base",
}

print("[ArenaAutoCache] Loaded simplified version - OnDemand only for model caching")
