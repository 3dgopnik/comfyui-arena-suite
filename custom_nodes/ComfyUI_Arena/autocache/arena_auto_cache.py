# EN identifiers; RU comments for clarity.
import os
import json
import time
import shutil
import threading
from pathlib import Path

# RU: Конфигурация через переменные окружения
ARENA_CACHE_ENABLE = os.getenv("ARENA_CACHE_ENABLE", "1") == "1"
ARENA_CACHE_MAX_GB = int(os.getenv("ARENA_CACHE_MAX_GB", "300"))
ARENA_CACHE_ROOT = os.getenv(
    "ARENA_CACHE_ROOT",
    os.path.join(os.getenv("LOCALAPPDATA", os.getcwd()), "ArenaAutoCache"),
)
ARENA_CACHE_VERBOSE = os.getenv("ARENA_CACHE_VERBOSE", "0") == "1"

_STALE_LOCK_SECONDS = 60

# RU: Потокобезопасность
_lock = threading.RLock()

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

def _v(msg: str) -> None:
    if ARENA_CACHE_VERBOSE:
        print(f"[ArenaAutoCache] {msg}")

# RU: Патч ComfyUI.folder_paths при импорте
try:
    import folder_paths  # type: ignore

    if ARENA_CACHE_ENABLE:
        _v("patching folder_paths ...")

        _orig_get_paths = folder_paths.get_folder_paths
        _orig_get_full = folder_paths.get_full_path

        def _ensure_category_root(category: str) -> Path:
            root = Path(ARENA_CACHE_ROOT) / category
            root.mkdir(parents=True, exist_ok=True)
            return root

        def get_folder_paths_patched(category: str):  # type: ignore
            # RU: Кеш-путь добавляем первым
            cache_root = str(_ensure_category_root(category))
            paths = _orig_get_paths(category)
            if cache_root not in paths:
                paths = [cache_root] + list(paths)
            return paths

        def get_full_path_patched(category: str, filename: str):  # type: ignore
            # RU: Если файл уже в кеше — вернуть сразу
            cache_root = _ensure_category_root(category)
            dst = cache_root / filename
            lock_path = dst.with_suffix(dst.suffix + ".copying")
            prefer_source = False
            if dst.exists():
                if lock_path.exists():
                    # RU: Ждём завершения копирования, чтобы не читать недокопированный файл
                    wait_deadline = time.monotonic() + 5.0
                    while lock_path.exists() and time.monotonic() < wait_deadline:
                        time.sleep(0.05)
                    if lock_path.exists():
                        # RU: Если лок не исчез, проверим, не устарел ли он
                        try:
                            lock_age = time.time() - lock_path.stat().st_mtime
                        except Exception:
                            lock_age = None
                        if lock_age is not None and lock_age > _STALE_LOCK_SECONDS:
                            _v(f"stale lock detected for {dst}, will prefer source")
                        else:
                            _v(f"lock active for {dst}, will prefer source")
                        prefer_source = True
                    else:
                        try:
                            os.utime(dst, None)  # RU: обновим atime для LRU
                        except Exception:
                            pass
                        return str(dst)
                else:
                    try:
                        os.utime(dst, None)  # RU: обновим atime для LRU
                    except Exception:
                        pass
                    return str(dst)

            # RU: Иначе найдём исходник по оригинальным путям (без кеша первым)
            for p in _orig_get_paths(category):
                src = Path(p) / filename
                if src.exists():
                    if prefer_source:
                        _v(f"using original path due to cache lock: {src}")
                        return str(src)
                    with _lock:
                        _copy_into_cache_lru(src, dst, category)
                    return str(dst)
            return None

        def _copy_into_cache_lru(src: Path, dst: Path, category: str) -> None:
            cache_root = Path(ARENA_CACHE_ROOT) / category
            cache_root.mkdir(parents=True, exist_ok=True)
            dst.parent.mkdir(parents=True, exist_ok=True)

            # RU: .copying lock-файл предотвращает раннее чтение из кеша во время копирования
            lock_path = dst.with_suffix(dst.suffix + ".copying")
            if lock_path.exists():
                stale_lock = False
                if not dst.exists():
                    stale_lock = True
                else:
                    try:
                        lock_age = time.time() - lock_path.stat().st_mtime
                    except Exception:
                        lock_age = None
                    if lock_age is not None and lock_age > _STALE_LOCK_SECONDS:
                        stale_lock = True
                if stale_lock:
                    _v(f"remove stale lock before copy: {lock_path}")
                    try:
                        lock_path.unlink()
                    except Exception as lock_err:
                        _v(f"failed to remove stale lock {lock_path}: {lock_err}")
            size = src.stat().st_size
            if dst.exists():
                try:
                    dst_size = dst.stat().st_size
                except Exception:
                    dst_size = None
                if dst_size is not None and dst_size != size:
                    _v(f"remove stale cache (size mismatch): {dst}")
                    try:
                        dst.unlink()
                    except Exception as cleanup_err:
                        _v(f"failed to remove stale cache file {dst}: {cleanup_err}")
                    if lock_path.exists():
                        try:
                            lock_path.unlink()
                        except Exception as lock_err:
                            _v(f"failed to remove stale lock {lock_path}: {lock_err}")
                else:
                    _v(f"skip copy (exists): {dst}")
                    return

            _lru_ensure_room(cache_root, size)

            try:
                lock_path.touch(exist_ok=True)
                _v(f"copy {src} -> {dst}")
                try:
                    shutil.copy2(src, dst)
                except Exception as copy_err:
                    if dst.exists():
                        try:
                            # RU: Очищаем недокопированный файл, чтобы следующий запрос повторил попытку
                            dst.unlink()
                        except Exception as cleanup_err:
                            _v(f"failed to clean partial cache file {dst}: {cleanup_err}")
                    msg = f"copy failed for {src} -> {dst}: {copy_err}"
                    print(f"[ArenaAutoCache] {msg}")
                    raise
            finally:
                if lock_path.exists():
                    try:
                        lock_path.unlink()
                    except Exception:
                        pass

            try:
                os.utime(dst, None)
            except Exception:
                pass

        def _index_path(root: Path) -> Path:
            return root / ".arena_cache_index.json"

        def _load_index(root: Path) -> dict:
            p = _index_path(root)
            if not p.exists():
                return {"items": {}, "max_gb": ARENA_CACHE_MAX_GB}
            try:
                return json.loads(p.read_text("utf-8"))
            except Exception:
                return {"items": {}, "max_gb": ARENA_CACHE_MAX_GB}

        def _save_index(root: Path, idx: dict) -> None:
            p = _index_path(root)
            p.write_text(json.dumps(idx, ensure_ascii=False, indent=2), "utf-8")

        def _bytes_limit() -> int:
            return ARENA_CACHE_MAX_GB * (1024**3)

        def _lru_ensure_room(root: Path, incoming_size: int) -> None:
            idx = _load_index(root)
            items = idx.get("items", {})

            def total_bytes() -> int:
                return sum(v.get("size", 0) for v in items.values())

            # RU: Очистка, если не влезаем
            while total_bytes() + incoming_size > _bytes_limit():
                # RU: LRU по atime
                if not items:
                    break
                victim_rel = min(items.keys(), key=lambda k: items[k].get("atime", 0))
                victim = root / victim_rel
                try:
                    _v(f"evict {victim}")
                    if victim.exists():
                        victim.unlink()
                except Exception:
                    pass
                items.pop(victim_rel, None)
                _save_index(root, idx)

            # RU: здесь индекс не пополняем — пополним после копии

        def _update_index_touch(root: Path, file_path: Path) -> None:
            # RU: Индекс обновляем под глобальной блокировкой, чтобы чтение/запись файла были атомарными.
            with _lock:
                idx = _load_index(root)
                items = idx.get("items", {})
                try:
                    rel = str(file_path.relative_to(root))
                except Exception:
                    # RU: файл вне кеша
                    return
                try:
                    size = file_path.stat().st_size
                except Exception:
                    size = 0
                items[rel] = {"size": size, "atime": time.time()}
                idx["items"] = items
                _save_index(root, idx)

        # RU: Переопределяем и подменяем
        folder_paths.get_folder_paths = get_folder_paths_patched  # type: ignore

        def _get_full_proxy(category: str, filename: str):  # type: ignore
            path = get_full_path_patched(category, filename)
            if path is not None:
                # RU: обновим индекс
                root = _ensure_category_root(category)
                _update_index_touch(root, Path(path))
            return path

        folder_paths.get_full_path = _get_full_proxy  # type: ignore
        _v("folder_paths patched")
    else:
        _v("disabled by ARENA_CACHE_ENABLE=0")
except Exception as e:  # noqa: BLE001
    print(f"[ArenaAutoCache] disabled: {e}")

# RU: Узловые классы для UI (минимум)
class ArenaAutoCacheStats:
    """RU: Возвращает JSON со статистикой кеша по категории."""

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        return {"required": {"category": ("STRING", {"default": "checkpoints"})}}

    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache"

    def run(self, category: str):
        root = Path(ARENA_CACHE_ROOT) / category
        idx = {"items": {}}
        if root.exists():
            try:
                idx = _load_index(root)
            except Exception:
                idx = {"items": {}}
        data = {
            "cache_root": str(root),
            "items": len(idx.get("items", {})),
            "max_size_gb": ARENA_CACHE_MAX_GB,
            "enabled": ARENA_CACHE_ENABLE,
        }
        return (json.dumps(data, ensure_ascii=False, indent=2),)

class ArenaAutoCacheTrim:
    """RU: Принудительная очистка до лимита."""

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        return {"required": {"category": ("STRING", {"default": "checkpoints"})}}

    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache"

    def run(self, category: str):
        root = Path(ARENA_CACHE_ROOT) / category
        if not root.exists():
            return (json.dumps({"ok": True, "note": "no cache yet"}),)
        try:
            _lru_ensure_room(root, 0)
        except Exception as e:
            return (json.dumps({"ok": False, "error": str(e)}),)
        return (json.dumps({"ok": True, "note": "trimmed to limit"}),)

NODE_CLASS_MAPPINGS.update(
    {
        "ArenaAutoCacheStats": ArenaAutoCacheStats,
        "ArenaAutoCacheTrim": ArenaAutoCacheTrim,
    }
)

NODE_DISPLAY_NAME_MAPPINGS.update(
    {
        "ArenaAutoCacheStats": "Arena AutoCache: Stats",
        "ArenaAutoCacheTrim": "Arena AutoCache: Trim",
    }
)
