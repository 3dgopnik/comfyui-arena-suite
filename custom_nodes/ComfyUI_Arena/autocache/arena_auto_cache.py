# EN identifiers; RU comments for clarity.
import os
import json
import time
import shutil
import threading
from pathlib import Path


def _default_index() -> dict:
    return {
        "items": {},
        "max_gb": ARENA_CACHE_MAX_GB,
        "last_op": None,
        "last_path": None,
    }


def _ensure_index_defaults(idx: dict | None) -> dict:
    if not isinstance(idx, dict):
        idx = {}
    if "items" not in idx or not isinstance(idx["items"], dict):
        idx["items"] = {}
    idx.setdefault("max_gb", ARENA_CACHE_MAX_GB)
    idx.setdefault("last_op", None)
    idx.setdefault("last_path", None)
    return idx

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


def _ensure_category_root(category: str) -> Path:
    root = Path(ARENA_CACHE_ROOT) / category
    if ARENA_CACHE_ENABLE:
        root.mkdir(parents=True, exist_ok=True)
    return root


def _index_path(root: Path) -> Path:
    return root / ".arena_cache_index.json"


def _load_index(root: Path) -> dict:
    p = _index_path(root)
    if not p.exists():
        return _default_index()
    try:
        data = json.loads(p.read_text("utf-8"))
    except Exception:
        data = None
    return _ensure_index_defaults(data)


def _save_index(root: Path, idx: dict) -> None:
    if ARENA_CACHE_ENABLE and not root.exists():
        root.mkdir(parents=True, exist_ok=True)
    p = _index_path(root)
    p.write_text(
        json.dumps(_ensure_index_defaults(dict(idx)), ensure_ascii=False, indent=2),
        "utf-8",
    )


def _bytes_limit() -> int:
    return ARENA_CACHE_MAX_GB * (1024**3)


def _lru_ensure_room(root: Path, incoming_size: int) -> dict:
    trimmed: list[str] = []
    with _lock:
        idx = _load_index(root)
        items = idx.get("items", {})

        def total_bytes() -> int:
            return sum(v.get("size", 0) for v in items.values())

        while total_bytes() + incoming_size > _bytes_limit():
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
            trimmed.append(str(victim))

        if trimmed:
            idx["items"] = items
            idx["last_op"] = "TRIM"
            idx["last_path"] = trimmed[-1]
            _save_index(root, idx)

        result = {
            "trimmed": trimmed,
            "total_bytes": sum(v.get("size", 0) for v in items.values()),
            "items": len(items),
        }
    return result


def _update_index_meta(root: Path, op: str, path: Path | str | None) -> None:
    with _lock:
        idx = _load_index(root)
        idx["last_op"] = op
        idx["last_path"] = str(path) if path is not None else None
        _save_index(root, idx)


def _update_index_touch(
    root: Path,
    file_path: Path | str,
    op: str = "HIT",
    *,
    update_item: bool = True,
) -> None:
    file_path = Path(file_path)
    with _lock:
        idx = _load_index(root)
        items = idx.get("items", {})
        rel: str | None = None
        if update_item:
            try:
                rel = str(file_path.relative_to(root))
            except Exception:
                rel = None
            if rel is not None:
                try:
                    size = file_path.stat().st_size
                except Exception:
                    size = 0
                items[rel] = {"size": size, "atime": time.time()}
                idx["items"] = items
        idx["last_op"] = op
        idx["last_path"] = str(file_path)
        _save_index(root, idx)


def _copy_into_cache_lru(src: Path, dst: Path, category: str) -> None:
    cache_root = _ensure_category_root(category)
    dst.parent.mkdir(parents=True, exist_ok=True)

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

    _update_index_touch(cache_root, dst, op="COPY")

# RU: Патч ComfyUI.folder_paths при импорте
try:
    import folder_paths  # type: ignore

    if ARENA_CACHE_ENABLE:
        _v("patching folder_paths ...")

        _orig_get_paths = folder_paths.get_folder_paths
        _orig_get_full = folder_paths.get_full_path

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
            force_recopy = False
            if dst.exists():
                if lock_path.exists():
                    # RU: Проверим, не устарел ли лок, прежде чем ждать
                    lock_age = None
                    try:
                        lock_age = time.time() - lock_path.stat().st_mtime
                    except Exception:
                        lock_age = None
                    if lock_age is not None and lock_age > _STALE_LOCK_SECONDS:
                        _v(f"stale lock detected for {dst}, removing {lock_path}")
                        try:
                            lock_path.unlink()
                            force_recopy = True
                        except Exception as lock_err:
                            _v(f"failed to remove stale lock {lock_path}: {lock_err}")
                            prefer_source = True
                    if lock_path.exists() and not prefer_source:
                        # RU: Лок актуален — ждём кратко и при необходимости отдаём исходник
                        wait_deadline = time.monotonic() + 5.0
                        while lock_path.exists() and time.monotonic() < wait_deadline:
                            time.sleep(0.05)
                        if lock_path.exists():
                            _v(f"lock active for {dst}, will prefer source")
                            prefer_source = True
                        else:
                            if not dst.exists():
                                _v(f"cache target missing after lock release, prefer source: {dst}")
                                prefer_source = True
                                force_recopy = True
                            else:
                                try:
                                    os.utime(dst, None)  # RU: обновим atime для LRU
                                except Exception:
                                    pass
                                _update_index_touch(cache_root, dst, op="HIT")
                                return str(dst)
                elif not prefer_source:
                    try:
                        os.utime(dst, None)  # RU: обновим atime для LRU
                    except Exception:
                        pass
                    _update_index_touch(cache_root, dst, op="HIT")
                    return str(dst)

            # RU: Иначе найдём исходник по оригинальным путям (без кеша первым)
            for p in _orig_get_paths(category):
                src = Path(p) / filename
                if src.exists():
                    if prefer_source:
                        _v(f"using original path due to cache lock: {src}")
                        _update_index_meta(cache_root, "MISS", src)
                        return str(src)
                    with _lock:
                        if force_recopy and dst.exists():
                            try:
                                dst.unlink()
                            except Exception as cleanup_err:
                                _v(f"failed to remove stale cache file before recopy {dst}: {cleanup_err}")
                        _copy_into_cache_lru(src, dst, category)
                    return str(dst)
            return None
        # RU: Переопределяем и подменяем
        folder_paths.get_folder_paths = get_folder_paths_patched  # type: ignore

        def _get_full_proxy(category: str, filename: str):  # type: ignore
            return get_full_path_patched(category, filename)

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
        idx = _default_index()
        if root.exists():
            try:
                idx = _load_index(root)
            except Exception:
                idx = _default_index()
        items = idx.get("items", {})
        total_bytes = sum(v.get("size", 0) for v in items.values())
        total_gb = total_bytes / float(1024**3)
        data = {
            "category": category,
            "cache_root": str(root),
            "enabled": ARENA_CACHE_ENABLE,
            "items": len(items),
            "total_bytes": total_bytes,
            "total_gb": total_gb,
            "max_size_gb": idx.get("max_gb", ARENA_CACHE_MAX_GB),
            "last_op": idx.get("last_op"),
            "last_path": idx.get("last_path"),
        }
        if not ARENA_CACHE_ENABLE:
            data["note"] = "cache disabled"
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
        if not ARENA_CACHE_ENABLE:
            data = {
                "ok": True,
                "category": category,
                "note": "cache disabled",
                "trimmed": [],
                "items": 0,
                "total_bytes": 0,
                "total_gb": 0.0,
                "max_size_gb": ARENA_CACHE_MAX_GB,
            }
            return (json.dumps(data, ensure_ascii=False, indent=2),)
        if not root.exists():
            data = {
                "ok": True,
                "category": category,
                "note": "no cache yet",
                "trimmed": [],
                "items": 0,
                "total_bytes": 0,
                "total_gb": 0.0,
                "max_size_gb": ARENA_CACHE_MAX_GB,
            }
            return (json.dumps(data, ensure_ascii=False, indent=2),)
        try:
            trim_result = _lru_ensure_room(root, 0)
        except Exception as e:
            return (
                json.dumps({"ok": False, "category": category, "error": str(e)}, ensure_ascii=False, indent=2),
            )

        if not trim_result.get("trimmed"):
            _update_index_meta(root, "TRIM", None)

        idx = _load_index(root)
        total_bytes = trim_result.get(
            "total_bytes",
            sum(v.get("size", 0) for v in idx.get("items", {}).values()),
        )
        data = {
            "ok": True,
            "category": category,
            "note": "trimmed to limit",
            "trimmed": trim_result.get("trimmed", []),
            "items": trim_result.get("items", len(idx.get("items", {}))),
            "total_bytes": total_bytes,
            "total_gb": total_bytes / float(1024**3),
            "max_size_gb": idx.get("max_gb", ARENA_CACHE_MAX_GB),
        }
        return (json.dumps(data, ensure_ascii=False, indent=2),)

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
