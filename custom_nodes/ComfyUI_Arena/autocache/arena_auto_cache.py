# EN identifiers; RU comments for clarity.
import os
import json
import time
import shutil
import threading
from dataclasses import dataclass, replace
from pathlib import Path
from types import ModuleType
from typing import Callable, Optional

ARENA_LANG = (os.getenv("ARENA_LANG", "en") or "en").strip().lower()
if "_" in ARENA_LANG:
    ARENA_LANG = ARENA_LANG.split("_", 1)[0]
if "-" in ARENA_LANG:
    ARENA_LANG = ARENA_LANG.split("-", 1)[0]

I18N: dict[str, dict[str, str]] = {
    "en": {
        "node.config": "🅰️ Arena AutoCache: Config",
        "node.stats": "🅰️ Arena AutoCache: Stats",
        "node.statsex": "🅰️ Arena AutoCache: StatsEx",
        "node.audit": "🅰️ Arena AutoCache Audit",
        "node.warmup": "🅰️ Arena AutoCache Warmup",
        "node.trim": "🅰️ Arena AutoCache: Trim",
        "node.manager": "🅰️ Arena AutoCache: Manager",
        "input.cache_root": "Cache root directory",
        "input.max_size_gb": "Maximum cache size (GB)",
        "input.enable": "Enable AutoCache",
        "input.verbose": "Verbose logging",
        "input.category": "Model category",
        "input.do_trim": "Trim category after applying config",
        "input.items": "Items list (one per line)",
        "input.workflow_json": "Workflow JSON",
        "input.default_category": "Fallback category",
        "output.json": "JSON",
        "output.items": "Items",
        "output.total_gb": "Total size (GB)",
        "output.cache_root": "Cache root",
        "output.session_hits": "Session hits",
        "output.session_misses": "Session misses",
        "output.session_trims": "Session trims",
        "output.total": "Total",
        "output.cached": "Cached",
        "output.missing": "Missing",
        "output.warmed": "Warmed",
        "output.copied": "Copied",
        "output.errors": "Errors",
        "output.stats_json": "Stats JSON",
        "output.action_json": "Action JSON",
    },
    "ru": {
        "node.config": "🅰️ Arena AutoCache: Настройки",
        "node.stats": "🅰️ Arena AutoCache: Статистика",
        "node.statsex": "🅰️ Arena AutoCache: Расширенная статистика",
        "node.audit": "🅰️ Arena AutoCache Аудит",
        "node.warmup": "🅰️ Arena AutoCache Прогрев",
        "node.trim": "🅰️ Arena AutoCache: Очистка",
        "node.manager": "🅰️ Arena AutoCache: Менеджер",
        "input.cache_root": "Корневая папка кэша",
        "input.max_size_gb": "Максимальный размер кэша (ГБ)",
        "input.enable": "Включить AutoCache",
        "input.verbose": "Подробный лог",
        "input.category": "Категория моделей",
        "input.do_trim": "Очистить категорию после применения настроек",
        "input.items": "Список элементов (по одному в строке)",
        "input.workflow_json": "JSON рабочего процесса",
        "input.default_category": "Категория по умолчанию",
        "output.json": "JSON",
        "output.items": "Элементы",
        "output.total_gb": "Общий размер (ГБ)",
        "output.cache_root": "Корень кэша",
        "output.session_hits": "Попадания за сессию",
        "output.session_misses": "Промахи за сессию",
        "output.session_trims": "Очистки за сессию",
        "output.total": "Всего",
        "output.cached": "В кэше",
        "output.missing": "Отсутствует",
        "output.warmed": "Прогрето",
        "output.copied": "Скопировано",
        "output.errors": "Ошибки",
        "output.stats_json": "JSON со статистикой",
        "output.action_json": "JSON действий",
    },
}


def t(key: str) -> str:
    base = I18N.get("en", {})
    lang_map = I18N.get(ARENA_LANG, base)
    return lang_map.get(key, base.get(key, key))

_STALE_LOCK_SECONDS = 60

_lock = threading.RLock()


@dataclass
class ArenaCacheSettings:
    """RU: Отражает текущие настройки кеша во время сессии."""

    root: Path
    max_gb: int
    enable: bool
    verbose: bool


def _normalize_root(value: str | Path) -> Path:
    """RU: Приводит путь к нормализованному виду и поддерживает UNC."""

    try:
        base = Path(value).expanduser()
    except TypeError as exc:  # pragma: no cover - defensive
        raise ValueError(f"invalid cache root: {value!r}") from exc
    normalized = Path(os.path.normpath(str(base)))
    try:
        normalized = normalized.resolve(strict=False)
    except Exception:
        pass
    return normalized


def _initial_root() -> Path:
    env_root = os.getenv("ARENA_CACHE_ROOT")
    if not env_root:
        default_base = Path(os.getenv("LOCALAPPDATA", os.getcwd()))
        env_root = str(default_base / "ArenaAutoCache")
    return _normalize_root(env_root)


def _initial_bool(name: str, default: bool) -> bool:
    return os.getenv(name, "1" if default else "0") == "1"


def _initial_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


_settings = ArenaCacheSettings(
    root=_initial_root(),
    max_gb=max(0, _initial_int("ARENA_CACHE_MAX_GB", 300)),
    enable=_initial_bool("ARENA_CACHE_ENABLE", True),
    verbose=_initial_bool("ARENA_CACHE_VERBOSE", False),
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

NODE_CLASS_MAPPINGS: dict[str, type] = {}
NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}


_ALLOWED_ITEM_SUFFIXES = {
    ".bin",
    ".ckpt",
    ".ckpt.index",
    ".gguf",
    ".model",
    ".npz",
    ".onnx",
    ".pb",
    ".pt",
    ".pth",
    ".safetensors",
    ".tflite",
    ".vae",
    ".yaml",
    ".yml",
}


def _normalize_category_name(raw: str | None, default: str) -> str:
    value = (raw or "").strip()
    if not value:
        return default
    return value


def _normalize_item_name(raw: str) -> str:
    candidate = (raw or "").strip()
    if not candidate:
        return ""
    candidate = candidate.replace("\\", "/")
    while "//" in candidate:
        candidate = candidate.replace("//", "/")
    candidate = candidate.lstrip("/")
    parts: list[str] = []
    for part in candidate.split("/"):
        part = part.strip()
        if not part or part == "." or part == "..":
            continue
        parts.append(part)
    if not parts:
        return ""
    normalized = "/".join(parts)
    try:
        path_obj = Path(normalized)
    except Exception:
        return normalized
    if path_obj.is_absolute():
        return path_obj.name
    return path_obj.as_posix()


def _item_suffix_allowed(name: str) -> bool:
    try:
        suffixes = Path(name.lower()).suffixes
    except Exception:
        return False
    if not suffixes:
        return False
    for idx in range(len(suffixes)):
        compound = "".join(suffixes[idx:])
        if compound in _ALLOWED_ITEM_SUFFIXES:
            return True
    return suffixes[-1] in _ALLOWED_ITEM_SUFFIXES


def _guess_category_from_hints(
    key_hint: str | None, class_hint: str | None, default: str
) -> str:
    hints = []
    if class_hint:
        hints.append(class_hint)
    if key_hint:
        hints.append(key_hint)
    for hint in hints:
        lowered = hint.lower()
        if "lora" in lowered or "lyco" in lowered or "lycoris" in lowered:
            return "loras"
        if "hyper" in lowered:
            return "hypernetworks"
        if "textual" in lowered or "embedding" in lowered or lowered.startswith("ti_"):
            return "embeddings"
        if "vae" in lowered:
            return "vae"
        if "clip" in lowered:
            return "clip"
        if "control" in lowered and "controller" not in lowered:
            return "controlnet"
        if "unet" in lowered:
            return "unet"
        if "upscale" in lowered or "esrgan" in lowered or "gfpgan" in lowered:
            return "upscale_models"
        if "checkpoint" in lowered or "ckpt" in lowered or lowered.endswith("_model"):
            return "checkpoints"
    return default


def parse_items_spec(
    items: object, workflow_json: object, default_category: str
) -> list[dict[str, str]]:
    """RU: Преобразует спецификацию элементов в уникальный список категорий и файлов."""

    normalized_default = _normalize_category_name(default_category, "checkpoints")
    seen: set[tuple[str, str]] = set()
    result: list[dict[str, str]] = []

    def register(category: str | None, name: object) -> None:
        if not isinstance(name, str):
            return
        normalized_name = _normalize_item_name(name)
        if not normalized_name or not _item_suffix_allowed(normalized_name):
            return
        normalized_category = _normalize_category_name(category, normalized_default)
        key = (normalized_category, normalized_name)
        if key in seen:
            return
        seen.add(key)
        result.append({"category": normalized_category, "name": normalized_name})

    def consume_entry(entry: object, category_hint: str | None = None) -> None:
        if entry is None:
            return
        if isinstance(entry, str):
            text = entry.strip()
            if not text or text.startswith("#"):
                return
            cat = category_hint or normalized_default
            name = text
            if ":" in text:
                prefix, suffix = text.split(":", 1)
                if prefix.strip() and "/" not in prefix and "\\" not in prefix:
                    cat = prefix.strip()
                    name = suffix
            register(cat, name)
            return
        if isinstance(entry, dict):
            local_category = category_hint
            for key in ("category", "cat", "folder"):
                value = entry.get(key)
                if isinstance(value, str) and value.strip():
                    local_category = value
                    break
            for key in ("name", "filename", "file", "path"):
                if key in entry:
                    consume_entry(entry[key], local_category)
            if "items" in entry:
                consume_entry(entry["items"], local_category)
            return
        if isinstance(entry, (list, tuple, set)):
            for item in entry:
                consume_entry(item, category_hint)

    def load_json(value: object) -> object | None:
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return None
        return value

    loaded_items = load_json(items)
    if loaded_items is None and isinstance(items, str):
        prepared = items.replace(",", "\n").replace(";", "\n")
        for line in prepared.splitlines():
            consume_entry(line, None)
    else:
        consume_entry(loaded_items, None)

    workflow_obj = load_json(workflow_json)

    def walk_workflow(obj: object, key_hint: str | None = None, class_hint: str | None = None) -> None:
        if isinstance(obj, dict):
            next_class = obj.get("class_type") if isinstance(obj.get("class_type"), str) else class_hint
            for key, value in obj.items():
                if key == "class_type":
                    continue
                walk_workflow(value, key, next_class if isinstance(next_class, str) else class_hint)
            return
        if isinstance(obj, list):
            for item in obj:
                walk_workflow(item, key_hint, class_hint)
            return
        if isinstance(obj, str):
            stripped = obj.strip()
            if stripped and _item_suffix_allowed(stripped):
                category = _guess_category_from_hints(key_hint, class_hint, normalized_default)
                register(category, stripped)

    walk_workflow(workflow_obj)

    return result


def get_settings() -> ArenaCacheSettings:
    """RU: Возвращает копию настроек кеша."""

    with _lock:
        return replace(_settings)


def get_session_counters() -> dict[str, int]:
    """RU: Текущие счётчики операций за сессию."""

    with _lock:
        return {
            "hits": _session_hits,
            "misses": _session_misses,
            "trims": _session_trims,
        }


def _record_session_event(op: str, count: int = 1) -> None:
    """RU: Увеличивает счётчики событий (HIT/MISS/TRIM)."""

    if count <= 0:
        return
    global _session_hits, _session_misses, _session_trims
    with _lock:
        if op == "HIT":
            _session_hits += count
        elif op == "MISS":
            _session_misses += count
        elif op == "TRIM":
            _session_trims += count


def _category_root(category: str, *, settings: Optional[ArenaCacheSettings] = None) -> Path:
    """RU: Путь к каталогу категории без авто-создания."""

    if settings is None:
        settings = get_settings()
    return settings.root / category


def _ensure_category_root(category: str, *, settings: Optional[ArenaCacheSettings] = None) -> Path:
    """RU: Возвращает каталог категории, создавая его при включённом кеше."""

    if settings is None:
        settings = get_settings()
    root = _category_root(category, settings=settings)
    if settings.enable:
        root.mkdir(parents=True, exist_ok=True)
    return root


def _v(msg: str) -> None:
    """RU: Отладочная печать при verbose."""

    with _lock:
        verbose = _settings.verbose
    if verbose:
        print(f"[ArenaAutoCache] {msg}")


def set_cache_settings(
    *,
    root: str | Path | None = None,
    max_gb: int | None = None,
    enable: bool | None = None,
    verbose: bool | None = None,
) -> dict:
    """RU: Обновляет настройки кеша и перепатчивает folder_paths в рантайме."""

    global _settings
    with _lock:
        current = _settings
        if isinstance(root, str) and not root.strip():
            root = None
        new_root = current.root
        if root is not None:
            try:
                new_root = _normalize_root(root)
            except Exception as exc:
                return {
                    "ok": False,
                    "error": f"invalid cache_root: {exc}",
                    "effective_root": str(current.root),
                    "max_size_gb": current.max_gb,
                    "enable": current.enable,
                    "verbose": current.verbose,
                }

        if max_gb is None:
            new_max = current.max_gb
        else:
            try:
                new_max = max(0, int(max_gb))
            except (TypeError, ValueError) as exc:
                return {
                    "ok": False,
                    "error": f"invalid max_size_gb: {exc}",
                    "effective_root": str(current.root),
                    "max_size_gb": current.max_gb,
                    "enable": current.enable,
                    "verbose": current.verbose,
                }

        new_enable = current.enable if enable is None else bool(enable)
        new_verbose = current.verbose if verbose is None else bool(verbose)

        tentative = ArenaCacheSettings(
            root=new_root,
            max_gb=new_max,
            enable=new_enable,
            verbose=new_verbose,
        )

        if tentative.enable:
            try:
                tentative.root.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                return {
                    "ok": False,
                    "error": f"failed to prepare cache root '{tentative.root}': {exc}",
                    "effective_root": str(current.root),
                    "max_size_gb": current.max_gb,
                    "enable": current.enable,
                    "verbose": current.verbose,
                }

        _settings = tentative
        _apply_folder_paths_patch_locked()
        snapshot = replace(_settings)

    return {
        "ok": True,
        "effective_root": str(snapshot.root),
        "max_size_gb": snapshot.max_gb,
        "enable": snapshot.enable,
        "verbose": snapshot.verbose,
    }


def _default_index(*, settings: Optional[ArenaCacheSettings] = None) -> dict:
    """RU: Пустой индекс с актуальными настройками."""

    if settings is None:
        settings = get_settings()
    return {
        "items": {},
        "max_gb": settings.max_gb,
        "last_op": None,
        "last_path": None,
    }


def _ensure_index_defaults(idx: dict | None, *, settings: Optional[ArenaCacheSettings] = None) -> dict:
    """RU: Дополняет индекс обязательными полями."""

    if settings is None:
        settings = get_settings()
    if not isinstance(idx, dict):
        idx = {}
    if not isinstance(idx.get("items"), dict):
        idx["items"] = {}
    idx.setdefault("max_gb", settings.max_gb)
    idx.setdefault("last_op", None)
    idx.setdefault("last_path", None)
    return idx


def _index_path(root: Path) -> Path:
    return root / ".arena_cache_index.json"


def _load_index(root: Path, *, settings: Optional[ArenaCacheSettings] = None) -> dict:
    if settings is None:
        settings = get_settings()
    p = _index_path(root)
    if not p.exists():
        return _default_index(settings=settings)
    try:
        data = json.loads(p.read_text("utf-8"))
    except Exception:
        data = None
    return _ensure_index_defaults(data, settings=settings)


def _save_index(root: Path, idx: dict, *, settings: Optional[ArenaCacheSettings] = None) -> None:
    if settings is None:
        settings = get_settings()
    if settings.enable and not root.exists():
        root.mkdir(parents=True, exist_ok=True)
    p = _index_path(root)
    payload = json.dumps(
        _ensure_index_defaults(dict(idx), settings=settings),
        ensure_ascii=False,
        indent=2,
    )
    p.write_text(payload, "utf-8")


def _bytes_limit(*, settings: Optional[ArenaCacheSettings] = None) -> int:
    if settings is None:
        settings = get_settings()
    return max(0, settings.max_gb) * (1024**3)


def _lru_ensure_room(root: Path, incoming_size: int) -> dict:
    """RU: Гарантирует наличие свободного места для нового файла."""

    trimmed: list[str] = []
    with _lock:
        settings = _settings
        idx = _load_index(root, settings=settings)
        items = idx.get("items", {})

        def total_bytes() -> int:
            return sum(v.get("size", 0) for v in items.values())

        limit = _bytes_limit(settings=settings)

        while total_bytes() + incoming_size > limit:
            if not items:
                break
            victim_rel = min(items.keys(), key=lambda key: items[key].get("atime", 0))
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
            _save_index(root, idx, settings=settings)
            _record_session_event("TRIM", len(trimmed))

        result = {
            "trimmed": trimmed,
            "total_bytes": sum(v.get("size", 0) for v in items.values()),
            "items": len(items),
        }
    return result


def _update_index_meta(root: Path, op: str, path: Path | str | None) -> None:
    with _lock:
        settings = _settings
        idx = _load_index(root, settings=settings)
        idx["last_op"] = op
        idx["last_path"] = str(path) if path is not None else None
        _save_index(root, idx, settings=settings)
    _record_session_event(op)


def _update_index_touch(
    root: Path,
    file_path: Path | str,
    op: str = "HIT",
    *,
    update_item: bool = True,
) -> None:
    file_path = Path(file_path)
    with _lock:
        settings = _settings
        idx = _load_index(root, settings=settings)
        items = idx.get("items", {})
        rel: Optional[str] = None
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
        _save_index(root, idx, settings=settings)
    _record_session_event(op)


def _copy_into_cache_lru(src: Path, dst: Path, category: str) -> None:
    """RU: Копирует файл в кеш с учётом LRU."""

    settings = get_settings()
    cache_root = _ensure_category_root(category, settings=settings)
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


def _ensure_folder_paths_module() -> Optional[ModuleType]:
    """RU: Подгружает ComfyUI.folder_paths с мемоизацией."""

    global _folder_paths_module
    if _folder_paths_module is not None:
        return _folder_paths_module
    try:
        import folder_paths  # type: ignore
    except Exception as exc:
        print(f"[ArenaAutoCache] folder_paths unavailable: {exc}")
        return None
    _folder_paths_module = folder_paths
    return folder_paths


def _apply_folder_paths_patch_locked() -> None:
    """RU: Включает/отключает патч ComfyUI.folder_paths согласно настройкам."""

    global _folder_paths_patched, _orig_get_folder_paths, _orig_get_full_path
    module = _ensure_folder_paths_module()
    if module is None:
        return

    if _orig_get_folder_paths is None or _orig_get_full_path is None:
        _orig_get_folder_paths = module.get_folder_paths  # type: ignore[attr-defined]
        _orig_get_full_path = module.get_full_path  # type: ignore[attr-defined]

    settings = _settings

    if not settings.enable:
        if _folder_paths_patched and _orig_get_folder_paths and _orig_get_full_path:
            module.get_folder_paths = _orig_get_folder_paths  # type: ignore[attr-defined]
            module.get_full_path = _orig_get_full_path  # type: ignore[attr-defined]
            _folder_paths_patched = False
            _v("folder_paths patch disabled")
        else:
            _v("disabled by settings")
        return

    orig_get_paths = _orig_get_folder_paths
    if orig_get_paths is None:
        return

    def get_folder_paths_patched(category: str):
        """RU: Добавляет кешевую директорию в список путей."""

        settings_snapshot = get_settings()
        cache_root = str(_ensure_category_root(category, settings=settings_snapshot))
        try:
            raw_paths = orig_get_paths(category)
        except Exception:
            raw_paths = []
        paths = list(raw_paths)
        if cache_root not in paths:
            paths.insert(0, cache_root)
        return paths

    def get_full_path_patched(category: str, filename: str):
        """RU: Подменяет выдачу на кеш с автоматической синхронизацией."""

        settings_snapshot = get_settings()
        cache_root = _ensure_category_root(category, settings=settings_snapshot)
        dst = cache_root / filename
        lock_path = dst.with_suffix(dst.suffix + ".copying")
        prefer_source = False
        force_recopy = False

        if dst.exists():
            if lock_path.exists():
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
                                os.utime(dst, None)
                            except Exception:
                                pass
                            _update_index_touch(cache_root, dst, op="HIT")
                            return str(dst)
            elif not prefer_source:
                try:
                    os.utime(dst, None)
                except Exception:
                    pass
                _update_index_touch(cache_root, dst, op="HIT")
                return str(dst)

        try:
            source_paths = list(orig_get_paths(category))
        except Exception:
            source_paths = []

        for base in source_paths:
            src = Path(base) / filename
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

    module.get_folder_paths = get_folder_paths_patched  # type: ignore[attr-defined]
    module.get_full_path = get_full_path_patched  # type: ignore[attr-defined]
    _folder_paths_patched = True
    _v("folder_paths patched")


def apply_folder_paths_patch() -> None:
    """RU: Публичная точка входа для патча (вызывается при импорте)."""

    with _lock:
        _apply_folder_paths_patch_locked()


def _collect_stats(category: str) -> tuple[dict, str, int, float, dict[str, int]]:
    """RU: Общий сбор статистики по категории."""

    settings = get_settings()
    root = _category_root(category, settings=settings)
    idx = _default_index(settings=settings)
    if root.exists():
        try:
            idx = _load_index(root, settings=settings)
        except Exception:
            idx = _default_index(settings=settings)
    items_map = idx.get("items", {})
    total_bytes = sum(v.get("size", 0) for v in items_map.values())
    total_gb = total_bytes / float(1024**3) if total_bytes else 0.0
    data = {
        "category": category,
        "cache_root": str(root),
        "enabled": settings.enable,
        "items": len(items_map),
        "total_bytes": total_bytes,
        "total_gb": total_gb,
        "max_size_gb": idx.get("max_gb", settings.max_gb),
        "last_op": idx.get("last_op"),
        "last_path": idx.get("last_path"),
    }
    if not settings.enable:
        data["note"] = "cache disabled"
    counters = get_session_counters()
    return data, str(root), len(items_map), total_gb, counters


def _trim_category(category: str) -> dict:
    """RU: Общая логика LRU-трима для узлов."""

    settings = get_settings()
    root = _category_root(category, settings=settings)
    if not settings.enable:
        return {
            "ok": True,
            "category": category,
            "note": "cache disabled",
            "trimmed": [],
            "items": 0,
            "total_bytes": 0,
            "total_gb": 0.0,
            "max_size_gb": settings.max_gb,
        }
    if not root.exists():
        return {
            "ok": True,
            "category": category,
            "note": "no cache yet",
            "trimmed": [],
            "items": 0,
            "total_bytes": 0,
            "total_gb": 0.0,
            "max_size_gb": settings.max_gb,
        }
    try:
        trim_result = _lru_ensure_room(root, 0)
    except Exception as exc:
        return {"ok": False, "category": category, "error": str(exc)}
    if not trim_result.get("trimmed"):
        _update_index_meta(root, "TRIM", None)
    idx = _load_index(root, settings=settings)
    total_bytes = trim_result.get(
        "total_bytes",
        sum(v.get("size", 0) for v in idx.get("items", {}).values()),
    )
    total_gb = total_bytes / float(1024**3) if total_bytes else 0.0
    return {
        "ok": True,
        "category": category,
        "note": "trimmed to limit",
        "trimmed": trim_result.get("trimmed", []),
        "items": trim_result.get("items", len(idx.get("items", {}))),
        "total_bytes": total_bytes,
        "total_gb": total_gb,
        "max_size_gb": idx.get("max_gb", settings.max_gb),
    }


apply_folder_paths_patch()


class ArenaAutoCacheConfig:
    """RU: Узел для настройки кеша в рантайме."""

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        settings = get_settings()
        return {
            "required": {
                "cache_root": (
                    "STRING",
                    {
                        "default": str(settings.root),
                        "description": t("input.cache_root"),
                        "tooltip": t("input.cache_root"),
                    },
                ),
                "max_size_gb": (
                    "INT",
                    {
                        "default": settings.max_gb,
                        "min": 0,
                        "max": 4096,
                        "step": 1,
                        "description": t("input.max_size_gb"),
                        "tooltip": t("input.max_size_gb"),
                    },
                ),
                "enable": (
                    "BOOLEAN",
                    {
                        "default": settings.enable,
                        "description": t("input.enable"),
                        "tooltip": t("input.enable"),
                    },
                ),
                "verbose": (
                    "BOOLEAN",
                    {
                        "default": settings.verbose,
                        "description": t("input.verbose"),
                        "tooltip": t("input.verbose"),
                    },
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = (t("output.json"),)
    RETURN_DESCRIPTIONS = (t("output.json"),)
    OUTPUT_TOOLTIPS = RETURN_DESCRIPTIONS
    FUNCTION = "apply"
    CATEGORY = "Arena/AutoCache"
    DESCRIPTION = t("node.config")

    def apply(self, cache_root: str, max_size_gb: int, enable: bool, verbose: bool):
        root_value = cache_root.strip()
        result = set_cache_settings(
            root=root_value or None,
            max_gb=max_size_gb,
            enable=enable,
            verbose=verbose,
        )
        if result.get("ok"):
            result.setdefault("note", "settings applied")
        else:
            result.setdefault("note", "settings unchanged")
        return (json.dumps(result, ensure_ascii=False, indent=2),)


class ArenaAutoCacheStats:
    """RU: Возвращает JSON со сводкой кеша."""

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        return {
            "required": {
                "category": (
                    "STRING",
                    {
                        "default": "checkpoints",
                        "description": t("input.category"),
                        "tooltip": t("input.category"),
                    },
                )
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = (t("output.json"),)
    RETURN_DESCRIPTIONS = (t("output.json"),)
    OUTPUT_TOOLTIPS = RETURN_DESCRIPTIONS
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache"
    DESCRIPTION = t("node.stats")

    def run(self, category: str):
        data, _, _, _, _ = _collect_stats(category)
        return (json.dumps(data, ensure_ascii=False, indent=2),)


class ArenaAutoCacheStatsEx:
    """RU: Расширенная статистика кеша с отдельными выходами."""

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        return {
            "required": {
                "category": (
                    "STRING",
                    {
                        "default": "checkpoints",
                        "description": t("input.category"),
                        "tooltip": t("input.category"),
                    },
                )
            }
        }

    RETURN_TYPES = ("STRING", "INT", "FLOAT", "STRING", "INT", "INT", "INT")
    RETURN_NAMES = (
        t("output.json"),
        t("output.items"),
        t("output.total_gb"),
        t("output.cache_root"),
        t("output.session_hits"),
        t("output.session_misses"),
        t("output.session_trims"),
    )
    RETURN_DESCRIPTIONS = (
        t("output.json"),
        t("output.items"),
        t("output.total_gb"),
        t("output.cache_root"),
        t("output.session_hits"),
        t("output.session_misses"),
        t("output.session_trims"),
    )
    OUTPUT_TOOLTIPS = RETURN_DESCRIPTIONS
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache"
    DESCRIPTION = t("node.statsex")

    def run(self, category: str):
        data, root, items, total_gb, counters = _collect_stats(category)
        stats_json = json.dumps(data, ensure_ascii=False, indent=2)
        return (
            stats_json,
            items,
            total_gb,
            root,
            counters.get("hits", 0),
            counters.get("misses", 0),
            counters.get("trims", 0),
        )


class ArenaAutoCacheAudit:
    """RU: Проверяет доступность исходников и наличие файлов в кэше."""

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        return {
            "required": {
                "items": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "description": t("input.items"),
                        "tooltip": t("input.items"),
                    },
                ),
                "workflow_json": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "description": t("input.workflow_json"),
                        "tooltip": t("input.workflow_json"),
                    },
                ),
                "default_category": (
                    "STRING",
                    {
                        "default": "checkpoints",
                        "description": t("input.default_category"),
                        "tooltip": t("input.default_category"),
                    },
                ),
            }
        }

    RETURN_TYPES = ("STRING", "INT", "INT", "INT")
    RETURN_NAMES = (
        t("output.json"),
        t("output.total"),
        t("output.cached"),
        t("output.missing"),
    )
    RETURN_DESCRIPTIONS = (
        t("output.json"),
        t("output.total"),
        t("output.cached"),
        t("output.missing"),
    )
    OUTPUT_TOOLTIPS = RETURN_DESCRIPTIONS
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache"
    DESCRIPTION = t("node.audit")

    def run(self, items: str, workflow_json: str, default_category: str):
        module = _ensure_folder_paths_module()
        if module is None:
            payload = {
                "ok": False,
                "error": "folder_paths unavailable",
                "items": [],
            }
            return (json.dumps(payload, ensure_ascii=False, indent=2), 0, 0, 0)

        parsed = parse_items_spec(items, workflow_json, default_category)
        if not parsed:
            payload = {"ok": True, "items": [], "note": "no items"}
            return (json.dumps(payload, ensure_ascii=False, indent=2), 0, 0, 0)

        settings = get_settings()
        with _lock:
            _apply_folder_paths_patch_locked()

        category_roots: dict[str, Path] = {}
        results: list[dict[str, object]] = []
        cached_count = 0
        missing_count = 0

        for entry in parsed:
            category = entry["category"]
            name = entry["name"]
            cache_root = category_roots.get(category)
            if cache_root is None:
                cache_root = _ensure_category_root(category, settings=settings)
                category_roots[category] = cache_root
            cache_path = cache_root / name

            try:
                raw_paths = module.get_folder_paths(category)  # type: ignore[attr-defined]
            except Exception:
                raw_paths = []
            source_path: Path | None = None
            for base in raw_paths:
                candidate = Path(base) / name
                if candidate.exists():
                    source_path = candidate
                    break

            cache_exists = cache_path.exists()
            entry_info: dict[str, object] = {
                "category": category,
                "name": name,
                "cache_path": str(cache_path),
                "cache_exists": cache_exists,
                "source_path": str(source_path) if source_path else None,
            }

            if cache_exists:
                cached_count += 1
                entry_info["status"] = "cached"
                if settings.enable:
                    try:
                        _update_index_touch(cache_root, cache_path, op="HIT")
                    except Exception:
                        pass
            elif source_path is not None:
                missing_count += 1
                entry_info["status"] = "missing_cache"
                if settings.enable:
                    try:
                        _update_index_meta(cache_root, "MISS", str(source_path))
                    except Exception:
                        pass
            else:
                missing_count += 1
                entry_info["status"] = "missing_source"
                if settings.enable:
                    try:
                        _update_index_meta(cache_root, "MISS", f"{category}:{name}")
                    except Exception:
                        pass

            results.append(entry_info)

        payload = {
            "ok": True,
            "enable": settings.enable,
            "items": results,
            "counts": {
                "total": len(parsed),
                "cached": cached_count,
                "missing": missing_count,
            },
        }
        if not settings.enable:
            payload["note"] = "cache disabled"

        return (
            json.dumps(payload, ensure_ascii=False, indent=2),
            len(parsed),
            cached_count,
            missing_count,
        )


class ArenaAutoCacheWarmup:
    """RU: Готовит указанные элементы в SSD-кэше."""

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        return {
            "required": {
                "items": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "description": t("input.items"),
                        "tooltip": t("input.items"),
                    },
                ),
                "workflow_json": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "description": t("input.workflow_json"),
                        "tooltip": t("input.workflow_json"),
                    },
                ),
                "default_category": (
                    "STRING",
                    {
                        "default": "checkpoints",
                        "description": t("input.default_category"),
                        "tooltip": t("input.default_category"),
                    },
                ),
            }
        }

    RETURN_TYPES = ("STRING", "INT", "INT", "INT", "INT", "INT")
    RETURN_NAMES = (
        t("output.json"),
        t("output.total"),
        t("output.warmed"),
        t("output.copied"),
        t("output.missing"),
        t("output.errors"),
    )
    RETURN_DESCRIPTIONS = (
        t("output.json"),
        t("output.total"),
        t("output.warmed"),
        t("output.copied"),
        t("output.missing"),
        t("output.errors"),
    )
    OUTPUT_TOOLTIPS = RETURN_DESCRIPTIONS
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache"
    DESCRIPTION = t("node.warmup")

    def run(self, items: str, workflow_json: str, default_category: str):
        module = _ensure_folder_paths_module()
        if module is None:
            payload = {
                "ok": False,
                "error": "folder_paths unavailable",
                "items": [],
            }
            return (json.dumps(payload, ensure_ascii=False, indent=2), 0, 0, 0, 0, 1)

        parsed = parse_items_spec(items, workflow_json, default_category)
        if not parsed:
            payload = {"ok": True, "items": [], "note": "no items"}
            return (json.dumps(payload, ensure_ascii=False, indent=2), 0, 0, 0, 0, 0)

        settings = get_settings()
        with _lock:
            _apply_folder_paths_patch_locked()

        category_roots: dict[str, Path] = {}
        results: list[dict[str, object]] = []
        counts = {
            "total": len(parsed),
            "warmed": 0,
            "copied": 0,
            "missing": 0,
            "errors": 0,
            "skipped": 0,
        }

        for entry in parsed:
            category = entry["category"]
            name = entry["name"]
            cache_root = category_roots.get(category)
            if cache_root is None:
                cache_root = _ensure_category_root(category, settings=settings)
                category_roots[category] = cache_root
            cache_path = cache_root / name

            try:
                raw_paths = module.get_folder_paths(category)  # type: ignore[attr-defined]
            except Exception:
                raw_paths = []
            source_path: Path | None = None
            for base in raw_paths:
                candidate = Path(base) / name
                if candidate.exists():
                    source_path = candidate
                    break

            entry_info: dict[str, object] = {
                "category": category,
                "name": name,
                "cache_path": str(cache_path),
                "source_path": str(source_path) if source_path else None,
            }

            if not settings.enable:
                counts["skipped"] += 1
                if source_path is None:
                    counts["missing"] += 1
                    entry_info["status"] = "missing_source"
                else:
                    entry_info["status"] = "skipped_disabled"
                entry_info["cache_exists"] = cache_path.exists()
                results.append(entry_info)
                continue

            if source_path is None:
                counts["missing"] += 1
                entry_info["status"] = "missing_source"
                try:
                    _update_index_meta(cache_root, "MISS", f"{category}:{name}")
                except Exception:
                    pass
                entry_info["cache_exists"] = cache_path.exists()
                results.append(entry_info)
                continue

            try:
                size = source_path.stat().st_size
            except Exception:
                size = 0

            was_cached = cache_path.exists()
            if was_cached:
                try:
                    cache_size = cache_path.stat().st_size
                except Exception:
                    cache_size = None
                else:
                    if size and cache_size is not None and cache_size != size:
                        try:
                            cache_path.unlink()
                            was_cached = False
                        except Exception as exc:
                            counts["errors"] += 1
                            entry_info["status"] = "error_remove_stale"
                            entry_info["error"] = str(exc)
                            try:
                                _update_index_meta(cache_root, "MISS", str(source_path))
                            except Exception:
                                pass
                            entry_info["cache_exists"] = cache_path.exists()
                            results.append(entry_info)
                            continue

            if not was_cached:
                try:
                    _lru_ensure_room(cache_root, size)
                except Exception as exc:
                    counts["errors"] += 1
                    entry_info["status"] = "error_trim"
                    entry_info["error"] = str(exc)
                    try:
                        _update_index_meta(cache_root, "MISS", str(source_path))
                    except Exception:
                        pass
                    entry_info["cache_exists"] = cache_path.exists()
                    results.append(entry_info)
                    continue

                try:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                except Exception:
                    pass

                try:
                    shutil.copy2(source_path, cache_path)
                except Exception as exc:
                    counts["errors"] += 1
                    entry_info["status"] = "error_copy"
                    entry_info["error"] = str(exc)
                    if cache_path.exists():
                        try:
                            cache_path.unlink()
                        except Exception:
                            pass
                    try:
                        _update_index_meta(cache_root, "MISS", str(source_path))
                    except Exception:
                        pass
                    entry_info["cache_exists"] = cache_path.exists()
                    results.append(entry_info)
                    continue

                try:
                    os.utime(cache_path, None)
                except Exception:
                    pass

                try:
                    _update_index_touch(cache_root, cache_path, op="COPY")
                except Exception:
                    pass

                counts["copied"] += 1
                status = "copied"
            else:
                try:
                    _update_index_touch(cache_root, cache_path, op="HIT")
                except Exception:
                    pass
                status = "cached"

            counts["warmed"] += 1
            entry_info["status"] = status

            try:
                resolved = module.get_full_path(category, name)  # type: ignore[attr-defined]
            except Exception:
                resolved = None
            if resolved:
                entry_info["resolved_path"] = str(resolved)

            entry_info["cache_exists"] = cache_path.exists()
            results.append(entry_info)

        payload = {
            "ok": counts["errors"] == 0,
            "enable": settings.enable,
            "items": results,
            "counts": counts,
        }
        if not settings.enable:
            payload["note"] = "cache disabled"

        return (
            json.dumps(payload, ensure_ascii=False, indent=2),
            counts["total"],
            counts["warmed"],
            counts["copied"],
            counts["missing"],
            counts["errors"],
        )


class ArenaAutoCacheTrim:
    """RU: Принудительный запуск LRU-трима для категории."""

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        return {
            "required": {
                "category": (
                    "STRING",
                    {
                        "default": "checkpoints",
                        "description": t("input.category"),
                        "tooltip": t("input.category"),
                    },
                )
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = (t("output.json"),)
    RETURN_DESCRIPTIONS = (t("output.json"),)
    OUTPUT_TOOLTIPS = RETURN_DESCRIPTIONS
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache"
    DESCRIPTION = t("node.trim")

    def run(self, category: str):
        data = _trim_category(category)
        return (json.dumps(data, ensure_ascii=False, indent=2),)


class ArenaAutoCacheManager:
    """RU: Компоновщик конфигурации, статистики и опционального трима."""

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        settings = get_settings()
        return {
            "required": {
                "cache_root": (
                    "STRING",
                    {
                        "default": str(settings.root),
                        "description": t("input.cache_root"),
                        "tooltip": t("input.cache_root"),
                    },
                ),
                "max_size_gb": (
                    "INT",
                    {
                        "default": settings.max_gb,
                        "min": 0,
                        "max": 4096,
                        "step": 1,
                        "description": t("input.max_size_gb"),
                        "tooltip": t("input.max_size_gb"),
                    },
                ),
                "enable": (
                    "BOOLEAN",
                    {
                        "default": settings.enable,
                        "description": t("input.enable"),
                        "tooltip": t("input.enable"),
                    },
                ),
                "verbose": (
                    "BOOLEAN",
                    {
                        "default": settings.verbose,
                        "description": t("input.verbose"),
                        "tooltip": t("input.verbose"),
                    },
                ),
                "category": (
                    "STRING",
                    {
                        "default": "checkpoints",
                        "description": t("input.category"),
                        "tooltip": t("input.category"),
                    },
                ),
                "do_trim": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "description": t("input.do_trim"),
                        "tooltip": t("input.do_trim"),
                    },
                ),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = (t("output.stats_json"), t("output.action_json"))
    RETURN_DESCRIPTIONS = (t("output.stats_json"), t("output.action_json"))
    OUTPUT_TOOLTIPS = RETURN_DESCRIPTIONS
    FUNCTION = "manage"
    CATEGORY = "Arena/AutoCache"
    DESCRIPTION = t("node.manager")

    def manage(
        self,
        cache_root: str,
        max_size_gb: int,
        enable: bool,
        verbose: bool,
        category: str,
        do_trim: bool,
    ):
        root_value = cache_root.strip()
        config_result = set_cache_settings(
            root=root_value or None,
            max_gb=max_size_gb,
            enable=enable,
            verbose=verbose,
        )
        if config_result.get("ok"):
            config_result.setdefault("note", "settings applied")
        else:
            config_result.setdefault("note", "settings unchanged")

        action_payload: dict[str, object] = {
            "config": config_result,
            "category": category,
        }

        if do_trim:
            action_payload["trim"] = _trim_category(category)

        stats_json, *_ = ArenaAutoCacheStatsEx().run(category)
        action_json = json.dumps(action_payload, ensure_ascii=False, indent=2)
        return (stats_json, action_json)


NODE_CLASS_MAPPINGS.update(
    {
        "ArenaAutoCacheAudit": ArenaAutoCacheAudit,
        "ArenaAutoCacheConfig": ArenaAutoCacheConfig,
        "ArenaAutoCacheStats": ArenaAutoCacheStats,
        "ArenaAutoCacheStatsEx": ArenaAutoCacheStatsEx,
        "ArenaAutoCacheTrim": ArenaAutoCacheTrim,
        "ArenaAutoCacheWarmup": ArenaAutoCacheWarmup,
        "ArenaAutoCacheManager": ArenaAutoCacheManager,
    }
)

NODE_DISPLAY_NAME_MAPPINGS.update(
    {
        "ArenaAutoCacheAudit": t("node.audit"),
        "ArenaAutoCacheConfig": t("node.config"),
        "ArenaAutoCacheStats": t("node.stats"),
        "ArenaAutoCacheStatsEx": t("node.statsex"),
        "ArenaAutoCacheTrim": t("node.trim"),
        "ArenaAutoCacheWarmup": t("node.warmup"),
        "ArenaAutoCacheManager": t("node.manager"),
    }
)
