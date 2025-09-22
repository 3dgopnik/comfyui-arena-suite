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
    "node.config": "🅰️ Arena AutoCache: Config",
    "node.stats": "🅰️ Arena AutoCache: Stats",
    "node.statsex": "🅰️ Arena AutoCache: StatsEx",
    "node.audit": "🅰️ Arena AutoCache Audit",
    "node.warmup": "🅰️ Arena AutoCache Warmup",
    "node.trim": "🅰️ Arena AutoCache: Trim",
    "node.manager": "🅰️ Arena AutoCache: Manager",
    "node.dashboard": "🅰️ Arena AutoCache: Dashboard",
    "node.ops": "🅰️ Arena AutoCache: Ops",
    "node.analyze": "🅰️ Arena AutoCache: Analyze",
    "node.get_workflow": "🅰️ Arena AutoCache: Get Active Workflow",
    "input.cache_root": "Cache root directory",
    "input.max_size_gb": "Maximum cache size (GB)",
    "input.enable": "Enable AutoCache",
    "input.verbose": "Verbose logging",
    "input.category": "Model category",
    "input.do_trim": "Trim category after applying config",
    "input.do_warmup": "Warmup cache for listed items",
    "input.mode": "Operation mode",
    "input.mode.tooltip": "Select operation mode: audit_then_warmup, audit, warmup, or trim",
    "input.benchmark_samples": "Benchmark sample count",
    "input.benchmark_read_mb": "Benchmark read limit (MiB)",
    "input.do_trim_now": "Trim category immediately",
    "input.apply_settings": "Apply cache settings overrides",
    "input.extended_stats": "Include extended statistics block",
    "input.settings_json": "Settings overrides JSON",
    "input.items": "Items list (one per line)",
    "input.workflow_json": "Workflow JSON",
    "input.default_category": "Fallback category",
    "input.log_context": "Copy log context (JSON or text)",
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
    "output.summary_json": "Summary JSON",
    "output.audit_json": "Audit JSON",
    "output.warmup_json": "Warmup JSON",
    "output.trim_json": "Trim JSON",
}


def t(key: str) -> str:
    return LABELS.get(key, key)

_STALE_LOCK_SECONDS = 60

_lock = threading.RLock()


COPY_EVENT_CHANNEL = "arena/autocache/copy_event"
COPY_EVENT_STARTED = "copy_started"
COPY_EVENT_COMPLETED = "copy_completed"
COPY_EVENT_SKIPPED = "copy_skipped"
COPY_EVENT_FAILED = "copy_failed"


@dataclass
class _CopyJob:
    """Background copy request scheduled for the copy worker."""

    category: str
    filename: str
    src: Path
    dst: Path
    enqueued_at: float
    context: dict[str, object] | None = None
    done: threading.Event = field(default_factory=threading.Event)
    success: bool | None = None
    error: Exception | None = None

    @property
    def key(self) -> tuple[str, str]:
        return (self.category, self.filename)


_copy_queue: "Queue[_CopyJob]" = Queue()
_copy_jobs: dict[tuple[str, str], _CopyJob] = {}
_copy_worker_thread: threading.Thread | None = None


def _now() -> float:
    """Return a monotonic timestamp for timing measurements."""

    return time.perf_counter()


def _duration_since(start: float) -> float:
    """Return elapsed seconds since ``start`` using monotonic clocks."""

    return max(0.0, _now() - start)


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
    # Важно: не вызываем resolve(strict=False), чтобы не менять представление
    # пути (например, короткие 8.3 имена на Windows). Тесты сравнивают путь
    # байт-в-байт с тем, что было передано через переменные окружения.
    normalized = Path(os.path.normpath(str(base)))
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

_workflow_allowlist: set[tuple[str, str]] = set()

NODE_CLASS_MAPPINGS: dict[str, type] = {}
NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}


def _load_active_workflow() -> object | None:
    """Return the current workflow payload exposed by ComfyUI, if available."""

    try:
        from server import PromptServer  # type: ignore
    except Exception:
        return None

    prompt_server = getattr(PromptServer, "instance", None)
    if prompt_server is None:
        return None

    def _extract(candidate: object) -> object | None:
        if candidate is None:
            return None
        if isinstance(candidate, tuple) and len(candidate) >= 2:
            return _extract(candidate[1])
        if isinstance(candidate, dict):
            for key in ("workflow", "prompt"):
                nested = candidate.get(key)
                extracted = _extract(nested)
                if extracted is not None:
                    return extracted
            if "nodes" in candidate:
                return candidate
            return None
        if isinstance(candidate, list):
            for item in candidate:
                extracted = _extract(item)
                if extracted is not None:
                    return extracted
            return None
        if isinstance(candidate, str):
            if candidate.strip():
                return candidate
            return None
        return None

    candidates: list[object] = []

    prompt_queue = getattr(prompt_server, "prompt_queue", None)
    if prompt_queue is not None:
        for attr in ("workflow", "current_prompt", "current_workflow", "last_prompt", "last_workflow"):
            if hasattr(prompt_queue, attr):
                candidates.append(getattr(prompt_queue, attr))
        for method_name in ("get_current_prompt", "get_current_workflow", "get_last_prompt", "peek"):
            method = getattr(prompt_queue, method_name, None)
            if callable(method):
                try:
                    candidates.append(method())
                except TypeError:
                    try:
                        candidates.append(method(None))
                    except Exception:
                        pass
                except Exception:
                    pass
        queue_data = getattr(prompt_queue, "queue", None)
        if isinstance(queue_data, list):
            candidates.extend(reversed(queue_data))

    for attr in ("workflow", "last_prompt", "last_workflow"):
        if hasattr(prompt_server, attr):
            candidates.append(getattr(prompt_server, attr))
    for method_name in ("get_current_prompt", "get_last_prompt"):
        method = getattr(prompt_server, method_name, None)
        if callable(method):
            try:
                candidates.append(method())
            except Exception:
                pass

    for candidate in candidates:
        extracted = _extract(candidate)
        if extracted is not None:
            return extracted

    return None


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
    processed: list[tuple[str, str]] = []
    for hint in hints:
        lowered = hint.lower()
        normalized = lowered.replace("-", "_").replace(" ", "_")
        processed.append((lowered, normalized))

    for lowered, normalized in processed:
        if "clip_vision" in normalized or "clipvision" in normalized:
            return "clip_vision"
        if "ipadapter" in normalized or "ip_adapter" in normalized:
            return "ipadapter"
        if "insightface" in normalized or "insight_face" in normalized:
            return "insightface"
        if "clip_g" in normalized:
            return "clip_g"
        if "clip_l" in normalized:
            return "clip_l"

    for lowered, _normalized in processed:
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


def _set_workflow_allowlist(parsed: Sequence[dict[str, str]]) -> None:
    """Refresh the in-memory allowlist with the provided parsed items."""

    with _lock:
        _workflow_allowlist.clear()
        for entry in parsed:
            category = _normalize_category_name(entry.get("category"), "checkpoints")
            name = _normalize_item_name(entry.get("name", ""))
            if not category or not name:
                continue
            _workflow_allowlist.add((category, name))


def _resolve_workflow_json(workflow_json: object) -> object:
    """Return the provided workflow JSON or fall back to the active workflow."""

    if isinstance(workflow_json, str):
        if workflow_json.strip():
            return workflow_json
    elif workflow_json:
        return workflow_json

    fallback = _load_active_workflow()
    return fallback if fallback is not None else workflow_json


def reset_workflow_allowlist() -> None:
    """Clear the workflow allowlist (primarily for tests)."""

    with _lock:
        _workflow_allowlist.clear()


def register_workflow_items(
    items: object, workflow_json: object, default_category: str
) -> list[dict[str, str]]:
    """Parse the workflow inputs and refresh the allowlist."""

    effective_workflow = _resolve_workflow_json(workflow_json)
    parsed = parse_items_spec(items, effective_workflow, default_category)
    # Fallback: если ничего не распознано из воркфлоу, попробуем взять
    # последний использованный путь из индекса категории, чтобы не требовать
    # ручного ввода даже при несовместимом формате воркфлоу.
    if not parsed:
        try:
            stats = collect_stats(default_category)
            payload = stats.get("payload", {}) if isinstance(stats, dict) else {}
            last_path = None
            if isinstance(payload, dict):
                last_path = payload.get("last_path")
            if isinstance(last_path, str) and last_path.strip():
                name = _normalize_item_name(Path(last_path).name)
                if name:
                    parsed = [{"category": _normalize_category_name(default_category, "checkpoints"), "name": name}]
        except Exception:
            pass
    _set_workflow_allowlist(parsed)
    return parsed


def _is_item_allowlisted(category: str, filename: str) -> bool:
    """Return ``True`` when the tuple is currently allowlisted."""

    normalized_category = _normalize_category_name(category, "checkpoints")
    normalized_name = _normalize_item_name(filename)
    if not normalized_category or not normalized_name:
        return False
    with _lock:
        return (normalized_category, normalized_name) in _workflow_allowlist


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


def _sanitize_metadata(context: Mapping[str, object] | None) -> dict[str, object] | None:
    """Normalize metadata dictionaries for logging/output transports."""

    if not context:
        return None
    sanitized: dict[str, object] = {}
    for key, value in context.items():
        key_str = str(key)
        if isinstance(value, (str, int, float, bool)) or value is None:
            sanitized[key_str] = value
        else:
            sanitized[key_str] = str(value)
    return sanitized


def _format_context_for_message(context: Mapping[str, object] | None) -> str:
    """Format context mapping for human-readable logging output."""

    if not context:
        return ""
    parts = [f"{key}={value}" for key, value in context.items()]
    return f" ({', '.join(parts)})"


def _notify_copy_event(
    event: str,
    *,
    category: str | None = None,
    src: Path | None = None,
    dst: Path | None = None,
    context: Mapping[str, object] | None = None,
    note: str | None = None,
) -> None:
    """Emit copy lifecycle notifications regardless of verbose mode."""

    context_payload = _sanitize_metadata(context)
    payload: dict[str, object] = {
        "event": event,
        "category": category,
        "src": str(src) if src is not None else None,
        "dst": str(dst) if dst is not None else None,
        "filename": dst.name if dst is not None else (src.name if src is not None else None),
        "timestamp": time.time(),
        "context": context_payload,
    }
    if note:
        payload["note"] = note

    identifier = payload.get("filename") or payload.get("dst") or payload.get("src") or category or "unknown"
    message = f"{event.replace('_', ' ')}: {identifier}"
    if context_payload:
        message += _format_context_for_message(context_payload)
    if note:
        message += f" ({note})"
    print(f"[ArenaAutoCache] {message}")

    try:
        from server import PromptServer  # type: ignore
    except Exception:
        prompt_server = None
    else:
        prompt_server = getattr(PromptServer, "instance", None)

    if prompt_server is not None:
        send_sync = getattr(prompt_server, "send_sync", None)
        if callable(send_sync):
            try:
                send_sync(COPY_EVENT_CHANNEL, payload)
            except Exception:
                pass


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


def _copy_into_cache_lru(
    src: Path,
    dst: Path,
    category: str,
    *,
    context: Mapping[str, object] | None = None,
) -> None:
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
            _notify_copy_event(
                COPY_EVENT_SKIPPED,
                category=category,
                src=src,
                dst=dst,
                context=context,
                note="exists",
            )
            return

    _lru_ensure_room(cache_root, size)

    copy_successful = False
    try:
        lock_path.touch(exist_ok=True)
        _notify_copy_event(
            COPY_EVENT_STARTED,
            category=category,
            src=src,
            dst=dst,
            context=context,
        )
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
            _notify_copy_event(
                COPY_EVENT_FAILED,
                category=category,
                src=src,
                dst=dst,
                context=context,
                note=str(copy_err),
            )
            raise
        else:
            copy_successful = True
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

    if copy_successful:
        _notify_copy_event(
            COPY_EVENT_COMPLETED,
            category=category,
            src=src,
            dst=dst,
            context=context,
        )


def _copy_worker() -> None:
    """Process queued copy jobs sequentially in the background."""

    while True:
        job = _copy_queue.get()
        try:
            _copy_into_cache_lru(job.src, job.dst, job.category, context=job.context)
        except Exception as exc:  # pragma: no cover - error path
            job.success = False
            job.error = exc
        else:
            job.success = True
        finally:
            job.done.set()
            with _lock:
                current = _copy_jobs.get(job.key)
                if current is job:
                    _copy_jobs.pop(job.key, None)
            _copy_queue.task_done()


def _ensure_copy_worker_started() -> None:
    """Start the background copy worker if it isn't running."""

    global _copy_worker_thread
    thread = _copy_worker_thread
    if thread is not None and thread.is_alive():
        return
    worker = threading.Thread(
        target=_copy_worker,
        name="ArenaAutoCacheCopyWorker",
        daemon=True,
    )
    _copy_worker_thread = worker
    worker.start()


def _enqueue_copy_job(
    category: str,
    filename: str,
    src: Path,
    dst: Path,
    *,
    force_recopy: bool,
    context: Mapping[str, object] | None = None,
) -> bool:
    """Schedule a copy job unless one is already running."""

    job_key = (category, filename)
    with _lock:
        existing = _copy_jobs.get(job_key)
        if existing is not None and not existing.done.is_set():
            return False
        if existing is not None and existing.done.is_set():
            _copy_jobs.pop(job_key, None)
        if force_recopy and dst.exists():
            try:
                dst.unlink()
            except Exception as cleanup_err:  # pragma: no cover - logging only
                _v(f"failed to remove stale cache file before recopy {dst}: {cleanup_err}")
        job = _CopyJob(
            category=category,
            filename=filename,
            src=Path(src),
            dst=Path(dst),
            enqueued_at=_now(),
            context=_sanitize_metadata(context),
        )
        _copy_jobs[job_key] = job

    _ensure_copy_worker_started()
    _copy_queue.put(job)
    _v(f"queued cache copy {src} -> {dst}")
    return True


def wait_for_copy_queue(timeout: float = 5.0) -> bool:
    """Wait until all queued copy jobs are processed (primarily for tests)."""

    join_event = threading.Event()

    def _joiner() -> None:
        _copy_queue.join()
        join_event.set()

    waiter = threading.Thread(
        target=_joiner,
        name="ArenaAutoCacheQueueJoin",
        daemon=True,
    )
    waiter.start()
    finished = join_event.wait(max(0.0, timeout))
    if not finished:
        return False
    with _lock:
        return not _copy_jobs


_ensure_copy_worker_started()


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
        job_key = (category, filename)

        job_in_progress = False
        with _lock:
            active_job = _copy_jobs.get(job_key)
            if active_job is not None and not active_job.done.is_set():
                job_in_progress = True

        if dst.exists():
            if job_in_progress:
                prefer_source = True
            elif lock_path.exists():
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
                        with _lock:
                            existing = _copy_jobs.get(job_key)
                            if existing is not None and not existing.done.is_set():
                                _copy_jobs.pop(job_key, None)
                                job_in_progress = False
                                prefer_source = False
                    except Exception as lock_err:
                        _v(f"failed to remove stale lock {lock_path}: {lock_err}")
                        prefer_source = True
                if lock_path.exists():
                    _v(f"lock active for {dst}, using source")
                    prefer_source = True
                else:
                    if not dst.exists():
                        _v(f"cache target missing after lock release, prefer source: {dst}")
                        prefer_source = True
                        force_recopy = True
                    elif not force_recopy:
                        try:
                            os.utime(dst, None)
                        except Exception:
                            pass
                        _update_index_touch(cache_root, dst, op="HIT")
                        return str(dst)
            elif not force_recopy:
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
            if not src.exists():
                continue

            if not settings_snapshot.enable:
                prefer_source = True

            if prefer_source or job_in_progress:
                _update_index_meta(cache_root, "MISS", str(src))
                return str(src)

            if not _is_item_allowlisted(category, filename):
                _v(f"skip cache copy (allowlist): {category}:{filename}")
                _update_index_meta(cache_root, "MISS", str(src))
                return str(src)

            scheduled = _enqueue_copy_job(category, filename, src, dst, force_recopy=force_recopy)
            if not scheduled:
                _v(f"copy already in progress for {category}:{filename}, using source")

            _update_index_meta(cache_root, "MISS", str(src))
            return str(src)

        return None

    module.get_folder_paths = get_folder_paths_patched  # type: ignore[attr-defined]
    module.get_full_path = get_full_path_patched  # type: ignore[attr-defined]
    _folder_paths_patched = True
    _v("folder_paths patched")


def apply_folder_paths_patch() -> None:
    """RU: Публичная точка входа для патча (вызывается при импорте)."""

    with _lock:
        _apply_folder_paths_patch_locked()


def _collect_stats_impl(category: str) -> tuple[dict, str, int, float, dict[str, int]]:
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


def collect_stats(category: str) -> dict[str, object]:
    """RU: Публичная обёртка статистики для переиспользования в узлах."""

    data, root, items, total_gb, counters = _collect_stats_impl(category)
    payload = {
        "payload": data,
        "json": json.dumps(data, ensure_ascii=False, indent=2),
        "items": items,
        "total_gb": total_gb,
        "cache_root": root,
        "session_hits": counters.get("hits", 0),
        "session_misses": counters.get("misses", 0),
        "session_trims": counters.get("trims", 0),
    }
    return payload


def _trim_category_impl(category: str) -> dict:
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


def trim_category(category: str) -> dict[str, object]:
    """RU: Публичная обёртка для LRU-трима категории."""

    data = _trim_category_impl(category)
    return {"payload": data, "json": json.dumps(data, ensure_ascii=False, indent=2)}


def audit_items(
    items: str,
    workflow_json: str,
    default_category: str,
    *,
    parsed_items: Optional[Sequence[dict[str, str]]] = None,
) -> dict[str, object]:
    """Check source/cache availability for the provided items."""

    started_at = _now()

    def _finalize(
        payload: dict[str, object],
        *,
        total: int,
        cached: int,
        missing: int,
    ) -> dict[str, object]:
        counts = {"total": total, "cached": cached, "missing": missing}
        payload = dict(payload)
        payload.setdefault("counts", counts)

        duration = _duration_since(started_at)
        timings = payload.get("timings") if isinstance(payload.get("timings"), dict) else {}
        timings = dict(timings)
        timings.setdefault("duration_seconds", duration)
        payload["timings"] = timings

        ui_block = payload.get("ui") if isinstance(payload.get("ui"), dict) else {}
        ui_block = dict(ui_block)
        ui_block.setdefault(
            "headline",
            f"Audit: {cached} cached / {total} total",
        )
        ui_block.setdefault(
            "details",
            [
                f"Missing: {missing}",
                f"Duration: {duration:.4f}s",
            ],
        )
        payload["ui"] = ui_block

        json_text = json.dumps(payload, ensure_ascii=False, indent=2)
        return {
            "payload": payload,
            "json": json_text,
            "total": total,
            "cached": cached,
            "missing": missing,
            "timings": timings,
            "ui": ui_block,
        }

    module = _ensure_folder_paths_module()
    if module is None:
        payload = {"ok": False, "error": "folder_paths unavailable", "items": []}
        return _finalize(payload, total=0, cached=0, missing=0)

    effective_workflow = _resolve_workflow_json(workflow_json)
    if parsed_items is None:
        parsed = register_workflow_items(items, effective_workflow, default_category)
    else:
        parsed = list(parsed_items)
        _set_workflow_allowlist(parsed)
    if not parsed:
        payload = {"ok": True, "items": [], "note": "no items"}
        return _finalize(payload, total=0, cached=0, missing=0)

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

    counts = {
        "total": len(parsed),
        "cached": cached_count,
        "missing": missing_count,
    }
    payload: dict[str, object] = {
        "ok": True,
        "enable": settings.enable,
        "items": results,
        "counts": counts,
    }
    if not settings.enable:
        payload["note"] = "cache disabled"

    return _finalize(
        payload,
        total=counts["total"],
        cached=cached_count,
        missing=missing_count,
    )


def _parse_log_context(raw: str) -> dict[str, object] | None:
    """Convert optional JSON/text payload into a metadata mapping."""

    text = str(raw or "").strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
    except Exception:
        return {"text": text}
    if isinstance(parsed, dict):
        sanitized = _sanitize_metadata(parsed)
        return sanitized or {}
    return {"text": text}


def warmup_items(
    items: str,
    workflow_json: str,
    default_category: str,
    *,
    parsed_items: Optional[Sequence[dict[str, str]]] = None,
    copy_context: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Prepare the selected cache entries by copying missing files."""

    started_at = _now()

    def _finalize(
        payload: dict[str, object],
        *,
        total: int,
        warmed: int,
        copied: int,
        missing: int,
        errors: int,
    ) -> dict[str, object]:
        counts = {
            "total": total,
            "warmed": warmed,
            "copied": copied,
            "missing": missing,
            "errors": errors,
        }
        payload = dict(payload)
        payload.setdefault("counts", counts)

        duration = _duration_since(started_at)
        timings = payload.get("timings") if isinstance(payload.get("timings"), dict) else {}
        timings = dict(timings)
        timings.setdefault("duration_seconds", duration)
        payload["timings"] = timings

        ui_block = payload.get("ui") if isinstance(payload.get("ui"), dict) else {}
        ui_block = dict(ui_block)
        ui_block.setdefault(
            "headline",
            f"Warmup: {warmed}/{total} prepared",
        )
        ui_block.setdefault(
            "details",
            [
                f"Copied: {copied}",
                f"Missing: {missing}",
                f"Errors: {errors}",
                f"Duration: {duration:.4f}s",
            ],
        )
        payload["ui"] = ui_block

        json_text = json.dumps(payload, ensure_ascii=False, indent=2)
        return {
            "payload": payload,
            "json": json_text,
            "total": total,
            "warmed": warmed,
            "copied": copied,
            "missing": missing,
            "errors": errors,
            "timings": timings,
            "ui": ui_block,
        }

    module = _ensure_folder_paths_module()
    if module is None:
        payload = {"ok": False, "error": "folder_paths unavailable", "items": []}
        return _finalize(payload, total=0, warmed=0, copied=0, missing=0, errors=0)

    effective_workflow = _resolve_workflow_json(workflow_json)
    if parsed_items is None:
        parsed = register_workflow_items(items, effective_workflow, default_category)
    else:
        parsed = list(parsed_items)
        _set_workflow_allowlist(parsed)
    if not parsed:
        payload = {"ok": True, "items": [], "note": "no items"}
        return _finalize(payload, total=0, warmed=0, copied=0, missing=0, errors=0)

    settings = get_settings()
    with _lock:
        _apply_folder_paths_patch_locked()

    results: list[dict[str, object]] = []
    counts = {
        "total": len(parsed),
        "warmed": 0,
        "copied": 0,
        "missing": 0,
        "errors": 0,
    }
    category_roots: dict[str, Path] = {}
    copy_context_payload = _sanitize_metadata(copy_context)

    for entry in parsed:
        category = entry["category"]
        name = entry["name"]
        cache_root = category_roots.get(category)
        if cache_root is None:
            cache_root = _ensure_category_root(category, settings=settings)
            category_roots[category] = cache_root
        cache_path = cache_root / name
        entry_info: dict[str, object] = {
            "category": category,
            "name": name,
            "cache_path": str(cache_path),
        }

        if not settings.enable:
            entry_info["status"] = "disabled"
            results.append(entry_info)
            continue

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

        if source_path is None:
            counts["missing"] += 1
            entry_info["status"] = "missing_source"
            results.append(entry_info)
            continue

        if not cache_path.exists():
            try:
                _copy_into_cache_lru(
                    source_path,
                    cache_path,
                    category,
                    context=copy_context_payload,
                )
            except Exception as copy_err:
                counts["errors"] += 1
                entry_info["status"] = "copy_failed"
                entry_info["error"] = str(copy_err)
                try:
                    _update_index_meta(cache_root, "MISS", str(source_path))
                except Exception:
                    pass
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

    return _finalize(
        payload,
        total=counts["total"],
        warmed=counts["warmed"],
        copied=counts["copied"],
        missing=counts["missing"],
        errors=counts["errors"],
    )


def _extract_benchmark_candidates(*blocks: dict[str, object] | None) -> list[dict[str, object]]:
    """Collect cache entry metadata dictionaries from warmup/audit payloads."""

    entries: list[dict[str, object]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        payload = block.get("payload") if isinstance(block.get("payload"), dict) else block
        if not isinstance(payload, dict):
            continue
        items = payload.get("items")
        if not isinstance(items, list):
            continue
        for entry in items:
            if isinstance(entry, dict):
                entries.append(entry)
    return entries


def _benchmark_cache_entries(
    entries: list[dict[str, object]],
    *,
    sample_limit: int,
    read_limit_bytes: int,
) -> dict[str, object]:
    """Read cached files to estimate throughput respecting sampling limits."""

    if sample_limit <= 0:
        return {
            "requested_samples": sample_limit,
            "available_samples": len(entries),
            "read_samples": 0,
            "bytes": 0,
            "seconds": 0.0,
            "throughput_bytes_per_s": 0.0,
            "read_limit_bytes": read_limit_bytes,
        }

    unique_paths: list[Path] = []
    seen: set[str] = set()
    for entry in entries:
        cache_path = entry.get("cache_path")
        if not isinstance(cache_path, str):
            continue
        if cache_path in seen:
            continue
        candidate = Path(cache_path)
        if not candidate.exists():
            continue
        unique_paths.append(candidate)
        seen.add(cache_path)
        if len(unique_paths) >= sample_limit:
            break

    start = _now()
    total_bytes = 0
    read_files = 0
    for path in unique_paths:
        try:
            size = path.stat().st_size
        except Exception:
            continue
        to_read = size if read_limit_bytes <= 0 else min(size, read_limit_bytes)
        if to_read <= 0:
            continue
        remaining = to_read
        try:
            with path.open("rb") as handle:
                while remaining > 0:
                    chunk = handle.read(min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    remaining -= len(chunk)
        except Exception:
            continue
        read_files += 1

    elapsed = _duration_since(start)
    throughput = total_bytes / elapsed if elapsed > 0 else 0.0
    return {
        "requested_samples": sample_limit,
        "available_samples": len(entries),
        "read_samples": read_files,
        "bytes": total_bytes,
        "seconds": elapsed,
        "throughput_bytes_per_s": throughput,
        "read_limit_bytes": read_limit_bytes,
    }


def make_ui_summary(
    *,
    config: dict[str, object] | None = None,
    stats: dict[str, object] | None = None,
    audit: dict[str, object] | None = None,
    warmup: dict[str, object] | None = None,
    trim: dict[str, object] | None = None,
) -> dict[str, object]:
    """RU: Сводка для UI-компонентов, собирающая метрики и результаты операций."""

    summary: dict[str, object] = {"timestamp": time.time()}
    ok = True

    def _extract(block: dict[str, object] | None) -> dict[str, object] | None:
        if block is None:
            return None
        payload_obj = block.get("payload")
        if isinstance(payload_obj, dict):
            return payload_obj
        return block

    if config is not None:
        payload = _extract(config) or {}
        summary["config"] = payload
        if isinstance(payload, dict) and payload.get("ok") is False:
            ok = False

    if stats is not None:
        payload = _extract(stats) or {}
        summary["stats"] = payload
        summary["stats_meta"] = {
            "items": stats.get("items"),
            "total_gb": stats.get("total_gb"),
            "cache_root": stats.get("cache_root"),
            "session": {
                "hits": stats.get("session_hits"),
                "misses": stats.get("session_misses"),
                "trims": stats.get("session_trims"),
            },
        }
        if isinstance(payload, dict) and payload.get("ok") is False:
            ok = False

    if audit is not None:
        payload = _extract(audit) or {}
        summary["audit"] = payload
        summary["audit_meta"] = {
            "total": audit.get("total"),
            "cached": audit.get("cached"),
            "missing": audit.get("missing"),
        }
        if isinstance(payload, dict) and payload.get("ok") is False:
            ok = False

    if warmup is not None:
        payload = _extract(warmup) or {}
        summary["warmup"] = payload
        summary["warmup_meta"] = {
            "total": warmup.get("total"),
            "warmed": warmup.get("warmed"),
            "copied": warmup.get("copied"),
            "missing": warmup.get("missing"),
            "errors": warmup.get("errors"),
        }
        if isinstance(payload, dict) and payload.get("ok") is False:
            ok = False

    if trim is not None:
        payload = _extract(trim) or {}
        summary["trim"] = payload
        if isinstance(payload, dict) and payload.get("ok") is False:
            ok = False

    summary["ok"] = ok
    return summary


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
    CATEGORY = "Arena/AutoCache/Basic"
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
    CATEGORY = "Arena/AutoCache/Basic"
    DESCRIPTION = t("node.stats")

    def run(self, category: str):
        result = collect_stats(category)
        return (result["json"],)


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
    CATEGORY = "Arena/AutoCache/Utils"
    DESCRIPTION = t("node.statsex")

    def run(self, category: str):
        result = collect_stats(category)
        return (
            result["json"],
            result["items"],
            result["total_gb"],
            result["cache_root"],
            result["session_hits"],
            result["session_misses"],
            result["session_trims"],
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
            ,
            "optional": {
                "extended_stats": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "description": t("input.extended_stats"),
                        "tooltip": t("input.extended_stats"),
                    },
                ),
                "apply_settings": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "description": t("input.apply_settings"),
                        "tooltip": t("input.apply_settings"),
                    },
                ),
                "do_trim_now": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "description": t("input.do_trim_now"),
                        "tooltip": t("input.do_trim_now"),
                    },
                ),
                "settings_json": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "description": t("input.settings_json"),
                        "tooltip": t("input.settings_json"),
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "INT", "INT", "INT", "STRING")
    RETURN_NAMES = (
        t("output.json"),
        t("output.total"),
        t("output.cached"),
        t("output.missing"),
        t("output.summary_json"),
    )
    RETURN_DESCRIPTIONS = (
        t("output.json"),
        t("output.total"),
        t("output.cached"),
        t("output.missing"),
        t("output.summary_json"),
    )
    OUTPUT_TOOLTIPS = RETURN_DESCRIPTIONS
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache/Advanced"
    OUTPUT_NODE = True
    DESCRIPTION = t("node.audit")

    def run(
        self,
        items: str,
        workflow_json: str,
        default_category: str,
        extended_stats: bool = False,
        apply_settings: bool = False,
        do_trim_now: bool = False,
        settings_json: str = "",
    ):
        effective_workflow = _resolve_workflow_json(workflow_json)
        parsed_items = register_workflow_items(items, effective_workflow, default_category)
        categories = sorted({entry.get("category", "") for entry in parsed_items if isinstance(entry, dict)})
        if not categories:
            categories = [_normalize_category_name(default_category, "checkpoints")]

        config_block: dict[str, object] | None = None
        config_duration = 0.0
        if apply_settings:
            overrides: dict[str, object] = {}
            if settings_json.strip():
                try:
                    decoded = json.loads(settings_json)
                    if isinstance(decoded, dict):
                        overrides = decoded
                except Exception:
                    overrides = {}
            current = get_settings()
            root_override = overrides.get("cache_root", overrides.get("root"))
            max_override = overrides.get("max_size_gb", overrides.get("max_gb"))
            enable_override = overrides.get("enable")
            verbose_override = overrides.get("verbose")

            config_started = _now()
            result = set_cache_settings(
                root=root_override if root_override is not None else current.root,
                max_gb=max_override if max_override is not None else current.max_gb,
                enable=enable_override if enable_override is not None else current.enable,
                verbose=verbose_override if verbose_override is not None else current.verbose,
            )
            config_duration = _duration_since(config_started)
            payload = dict(result)
            if payload.get("ok"):
                payload.setdefault("note", "settings applied")
            else:
                payload.setdefault("note", "settings unchanged")
            payload.setdefault("source", "audit")
            payload.setdefault("timings", {"duration_seconds": config_duration})
            config_block = {"payload": payload, "timings": {"duration_seconds": config_duration}}

        stats_result: dict[str, object] | None = None
        stats_duration = 0.0
        stats_categories: dict[str, dict[str, object]] = {}
        if extended_stats:
            stats_started = _now()
            aggregated_items = 0
            aggregated_total_gb = 0.0
            for category in categories:
                category_stats = collect_stats(category)
                stats_categories[category] = category_stats
                aggregated_items += int(category_stats.get("items", 0) or 0)
                aggregated_total_gb += float(category_stats.get("total_gb", 0.0) or 0.0)
                if stats_result is None:
                    stats_result = dict(category_stats)
            stats_duration = _duration_since(stats_started)
            if stats_result is not None:
                payload = dict(stats_result.get("payload", {}))
                payload.setdefault("category_order", categories)
                payload["categories"] = {
                    name: data.get("payload", {}) for name, data in stats_categories.items()
                }
                payload.setdefault(
                    "aggregated_totals",
                    {"items": aggregated_items, "total_gb": aggregated_total_gb},
                )
                stats_result = dict(stats_result)
                stats_result["payload"] = payload
                stats_result["json"] = json.dumps(payload, ensure_ascii=False, indent=2)
                stats_result["items"] = aggregated_items
                stats_result["total_gb"] = aggregated_total_gb
                if len(categories) > 1:
                    stats_result["cache_root"] = str(get_settings().root)

        audit_result = audit_items(
            items,
            effective_workflow,
            default_category,
            parsed_items=parsed_items,
        )

        trim_result: dict[str, object] | None = None
        trim_duration_total = 0.0
        trimmed_categories: list[str] = []
        if do_trim_now:
            trim_payloads: list[dict[str, object]] = []
            for category in categories:
                trimmed_categories.append(category)
                trim_started = _now()
                raw_trim = trim_category(category)
                duration = _duration_since(trim_started)
                trim_duration_total += duration
                payload = dict(raw_trim.get("payload", {}))
                payload.setdefault("category", category)
                timings = payload.get("timings") if isinstance(payload.get("timings"), dict) else {}
                timings = dict(timings)
                timings.setdefault("duration_seconds", duration)
                payload["timings"] = timings
                trim_payloads.append(
                    {
                        "category": category,
                        "payload": payload,
                        "json": json.dumps(payload, ensure_ascii=False, indent=2),
                        "timings": timings,
                    }
                )
            if trim_payloads:
                if len(trim_payloads) == 1:
                    trim_result = trim_payloads[0]
                else:
                    aggregate_payload = {
                        "ok": all(p["payload"].get("ok", True) for p in trim_payloads),
                        "categories": [p["category"] for p in trim_payloads],
                        "results": [p["payload"] for p in trim_payloads],
                        "note": "multiple categories trimmed",
                    }
                    aggregate_payload["timings"] = {"duration_seconds": trim_duration_total}
                    trim_result = {
                        "payload": aggregate_payload,
                        "json": json.dumps(aggregate_payload, ensure_ascii=False, indent=2),
                        "timings": {"duration_seconds": trim_duration_total},
                    }

        summary = make_ui_summary(
            config=config_block,
            stats=stats_result if extended_stats else None,
            audit=audit_result,
            trim=trim_result,
        )

        timings_block: dict[str, object] = {}
        if isinstance(audit_result.get("timings"), dict):
            timings_block["audit"] = audit_result["timings"]
        if config_block is not None:
            timings_block["config"] = {"seconds": config_duration}
        if extended_stats and stats_result is not None:
            timings_block["stats"] = {"seconds": stats_duration}
        if trim_result is not None:
            timings_block["trim"] = {"seconds": trim_duration_total}
        if timings_block:
            summary["timings"] = timings_block

        actions: list[dict[str, object]] = []
        if config_block is not None:
            payload = config_block.get("payload", {}) if isinstance(config_block, dict) else {}
            actions.append(
                {
                    "type": "settings",
                    "ok": bool(payload.get("ok", False)),
                    "duration_seconds": config_duration,
                    "effective_root": payload.get("effective_root"),
                    "max_size_gb": payload.get("max_size_gb"),
                }
            )
        if extended_stats and stats_result is not None:
            actions.append(
                {
                    "type": "stats",
                    "categories": categories,
                    "duration_seconds": stats_duration,
                    "items": stats_result.get("items"),
                    "total_gb": stats_result.get("total_gb"),
                }
            )
        if trim_result is not None:
            actions.append(
                {
                    "type": "trim",
                    "categories": trimmed_categories,
                    "duration_seconds": trim_duration_total,
                }
            )
        if actions:
            summary["actions"] = actions

        summary["categories"] = categories

        ui_details = [
            f"Audit total: {audit_result.get('total', 0)}",
            f"Audit missing: {audit_result.get('missing', 0)}",
        ]
        if config_block is not None:
            payload = config_block.get("payload", {}) if isinstance(config_block, dict) else {}
            applied = "applied" if payload.get("ok") else "unchanged"
            ui_details.append(f"Settings: {applied}")
        if extended_stats and stats_result is not None:
            ui_details.append(f"Stats categories: {len(categories)}")
        if trim_result is not None:
            if len(trimmed_categories) == 1:
                note = trim_result.get("payload", {}).get("note", "trim executed")
                ui_details.append(f"Trim: {note} ({trimmed_categories[0]})")
            else:
                ui_details.append(f"Trim: {len(trimmed_categories)} categories")
        summary["ui"] = {"headline": "Audit updated", "details": ui_details}

        summary_json = json.dumps(summary, ensure_ascii=False, indent=2)
        return (
            audit_result["json"],
            audit_result["total"],
            audit_result["cached"],
            audit_result["missing"],
            summary_json,
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
            },
            "optional": {
                "log_context": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "description": t("input.log_context"),
                        "tooltip": t("input.log_context"),
                    },
                ),
            },
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
    CATEGORY = "Arena/AutoCache/Advanced"
    DESCRIPTION = t("node.warmup")

    def run(self, items: str, workflow_json: str, default_category: str, log_context: str = ""):
        effective_workflow = _resolve_workflow_json(workflow_json)
        parsed_items = register_workflow_items(items, effective_workflow, default_category)
        context: dict[str, object] = {"node": "ArenaAutoCacheWarmup"}
        parsed_context = _parse_log_context(log_context)
        if parsed_context:
            context.update(parsed_context)
        result = warmup_items(
            items,
            effective_workflow,
            default_category,
            parsed_items=parsed_items,
            copy_context=context,
        )
        return (
            result["json"],
            result["total"],
            result["warmed"],
            result["copied"],
            result["missing"],
            result["errors"],
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
    CATEGORY = "Arena/AutoCache/Advanced"
    DESCRIPTION = t("node.trim")

    def run(self, category: str):
        result = trim_category(category)
        return (result["json"],)


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
    CATEGORY = "Arena/AutoCache/Advanced"
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

        trim_result = trim_category(category) if do_trim else None
        stats_result = collect_stats(category)
        summary = make_ui_summary(
            config={"payload": config_result},
            stats=stats_result,
            trim=trim_result,
        )

        action_payload: dict[str, object] = {
            "config": config_result,
            "category": category,
            "summary": summary,
        }
        if trim_result is not None:
            action_payload["trim"] = trim_result["payload"]

        action_json = json.dumps(action_payload, ensure_ascii=False, indent=2)
        return (stats_result["json"], action_json)


class ArenaAutoCacheDashboard:
    """RU: Сводный дашборд для отображения статистики и аудита."""

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
                ),
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
            },
            "optional": {
                "extended_stats": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "description": t("input.extended_stats"),
                        "tooltip": t("input.extended_stats"),
                    },
                ),
                "apply_settings": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "description": t("input.apply_settings"),
                        "tooltip": t("input.apply_settings"),
                    },
                ),
                "do_trim_now": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "description": t("input.do_trim_now"),
                        "tooltip": t("input.do_trim_now"),
                    },
                ),
                "settings_json": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "description": t("input.settings_json"),
                        "tooltip": t("input.settings_json"),
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = (
        t("output.summary_json"),
        t("output.stats_json"),
        t("output.audit_json"),
    )
    RETURN_DESCRIPTIONS = RETURN_NAMES
    OUTPUT_TOOLTIPS = RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache"
    DESCRIPTION = t("node.dashboard")
    OUTPUT_NODE = True

    def run(
        self,
        category: str,
        items: str,
        workflow_json: str,
        default_category: str,
        extended_stats: bool = False,
        apply_settings: bool = False,
        do_trim_now: bool = False,
        settings_json: str = "",
    ):
        config_block: dict[str, object] | None = None
        config_duration = 0.0
        if apply_settings:
            overrides: dict[str, object] = {}
            if settings_json.strip():
                try:
                    decoded = json.loads(settings_json)
                    if isinstance(decoded, dict):
                        overrides = decoded
                except Exception:
                    overrides = {}
            current = get_settings()
            root_override = overrides.get("cache_root", overrides.get("root"))
            max_override = overrides.get("max_size_gb", overrides.get("max_gb"))
            enable_override = overrides.get("enable")
            verbose_override = overrides.get("verbose")

            config_started = _now()
            result = set_cache_settings(
                root=root_override if root_override is not None else current.root,
                max_gb=max_override if max_override is not None else current.max_gb,
                enable=enable_override if enable_override is not None else current.enable,
                verbose=verbose_override if verbose_override is not None else current.verbose,
            )
            config_duration = _duration_since(config_started)
            if result.get("ok"):
                result.setdefault("note", "settings applied")
            else:
                result.setdefault("note", "settings unchanged")
            result.setdefault("source", "dashboard")
            config_block = {"payload": result}

        stats_started = _now()
        stats_result = collect_stats(category)
        stats_duration = _duration_since(stats_started)

        if extended_stats:
            stats_payload = dict(stats_result.get("payload", {}))
            stats_payload.setdefault("timings", {"duration_seconds": stats_duration})
            stats_payload.setdefault(
                "ui",
                {
                    "headline": f"Stats: {stats_payload.get('items', 0)} entries",
                    "details": [
                        f"Size: {stats_payload.get('total_gb', 0):.4f} GiB",
                        f"Cache root: {stats_payload.get('cache_root', '')}",
                    ],
                },
            )
            stats_result = dict(stats_result)
            stats_result["payload"] = stats_payload
            stats_result["json"] = json.dumps(stats_payload, ensure_ascii=False, indent=2)

        audit_result = audit_items(items, workflow_json, default_category)

        trim_result: dict[str, object] | None = None
        trim_duration = 0.0
        if do_trim_now:
            trim_started = _now()
            raw_trim = trim_category(category)
            trim_duration = _duration_since(trim_started)
            trim_payload = dict(raw_trim.get("payload", {}))
            trim_payload.setdefault("timings", {"duration_seconds": trim_duration})
            trim_result = {
                "payload": trim_payload,
                "json": json.dumps(trim_payload, ensure_ascii=False, indent=2),
                "timings": {"duration_seconds": trim_duration},
            }
        summary = make_ui_summary(
            config=config_block,
            stats=stats_result,
            audit=audit_result,
            trim=trim_result,
        )

        timings_block = dict(summary.get("timings") if isinstance(summary.get("timings"), dict) else {})
        timings_block.setdefault("stats", {"seconds": stats_duration})
        audit_timings = audit_result.get("timings") if isinstance(audit_result.get("timings"), dict) else None
        if audit_timings:
            timings_block.setdefault("audit", audit_timings)
        if trim_result is not None:
            timings_block.setdefault("trim", {"seconds": trim_duration})
        if config_block is not None:
            timings_block.setdefault("config", {"seconds": config_duration})
        summary["timings"] = timings_block

        ui_details = [
            f"Category: {category}",
            f"Audit cached: {audit_result.get('cached', 0)}",
            f"Audit missing: {audit_result.get('missing', 0)}",
        ]
        if config_block is not None:
            config_payload = config_block.get("payload", {})
            applied = "applied" if isinstance(config_payload, dict) and config_payload.get("ok") else "unchanged"
            ui_details.append(f"Settings: {applied}")
        if trim_result is not None:
            trim_note = trim_result.get("payload", {}).get("note", "trim executed")
            ui_details.append(f"Trim: {trim_note}")
        summary["ui"] = {"headline": "Dashboard updated", "details": ui_details}

        summary_json = json.dumps(summary, ensure_ascii=False, indent=2)
        return (summary_json, stats_result["json"], audit_result["json"])


ARENA_OPS_MODES: tuple[str, ...] = (
    "audit_then_warmup",
    "audit",
    "warmup",
    "trim",
)

ARENA_OPS_MODE_SET = set(ARENA_OPS_MODES)


class ArenaAutoCacheOps:
    """RU: Комбинированные операции прогрева и очистки с отчётом."""

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
                ),
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
                "mode": (
                    "STRING",
                    {
                        "default": ARENA_OPS_MODES[0],
                        "choices": ARENA_OPS_MODES,
                        "description": t("input.mode"),
                        "tooltip": t("input.mode.tooltip"),
                    },
                ),
            },
            "optional": {
                "benchmark_samples": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 64,
                        "step": 1,
                        "description": t("input.benchmark_samples"),
                        "tooltip": t("input.benchmark_samples"),
                    },
                ),
                "benchmark_read_mb": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": 0.0,
                        "max": 1024.0,
                        "step": 0.25,
                        "description": t("input.benchmark_read_mb"),
                        "tooltip": t("input.benchmark_read_mb"),
                    },
                ),
                "log_context": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "description": t("input.log_context"),
                        "tooltip": t("input.log_context"),
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = (
        t("output.summary_json"),
        t("output.warmup_json"),
        t("output.trim_json"),
    )
    RETURN_DESCRIPTIONS = RETURN_NAMES
    OUTPUT_TOOLTIPS = RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache"
    DESCRIPTION = t("node.ops")
    OUTPUT_NODE = True

    def run(
        self,
        category: str,
        items: str,
        workflow_json: str,
        default_category: str,
        mode: str,
        benchmark_samples: int = 0,
        benchmark_read_mb: float = 0.0,
        log_context: str = "",
    ):
        normalized_mode = str(mode or ARENA_OPS_MODES[0]).strip().lower()
        if normalized_mode not in ARENA_OPS_MODE_SET:
            normalized_mode = ARENA_OPS_MODES[0]
        run_audit = normalized_mode in {"audit", "audit_then_warmup"}
        run_warmup = normalized_mode in {"warmup", "audit_then_warmup"}
        run_trim = normalized_mode == "trim"

        effective_workflow = _resolve_workflow_json(workflow_json)
        audit_result: dict[str, object] | None = None
        warmup_result: dict[str, object] | None = None
        trim_result: dict[str, object] | None = None
        summary_timings: dict[str, dict[str, object]] = {}
        warmup_context: dict[str, object] | None = None

        parsed_items: list[dict[str, str]] | None = None
        if run_audit or run_warmup:
            parsed_items = register_workflow_items(items, effective_workflow, default_category)

        if run_audit:
            audit_started = _now()
            audit_result = audit_items(
                items,
                effective_workflow,
                default_category,
                parsed_items=parsed_items,
            )
            audit_duration = _duration_since(audit_started)
            audit_timings = audit_result.get("timings") if isinstance(audit_result.get("timings"), dict) else {}
            if not audit_timings:
                audit_timings = {"duration_seconds": audit_duration}
                audit_result = dict(audit_result)
                audit_result["timings"] = audit_timings
            summary_timings["audit"] = audit_timings

        if run_warmup:
            warmup_context = {"node": "ArenaAutoCacheOps", "mode": normalized_mode}
            parsed_context = _parse_log_context(log_context)
            if parsed_context:
                warmup_context.update(parsed_context)
            warmup_started = _now()
            warmup_result = warmup_items(
                items,
                effective_workflow,
                default_category,
                parsed_items=parsed_items,
                copy_context=warmup_context,
            )
            warmup_duration = _duration_since(warmup_started)
            warmup_timings = warmup_result.get("timings") if isinstance(warmup_result.get("timings"), dict) else {}
            if not warmup_timings:
                warmup_timings = {"duration_seconds": warmup_duration}
                warmup_result = dict(warmup_result)
                warmup_result["timings"] = warmup_timings
            summary_timings["warmup"] = warmup_timings

        if run_trim:
            trim_started = _now()
            raw_trim = trim_category(category)
            trim_duration = _duration_since(trim_started)
            trim_payload = dict(raw_trim.get("payload", {}))
            trim_payload.setdefault("timings", {"duration_seconds": trim_duration})
            trim_result = {
                "payload": trim_payload,
                "json": json.dumps(trim_payload, ensure_ascii=False, indent=2),
                "timings": {"duration_seconds": trim_duration},
            }
            summary_timings["trim"] = trim_result["timings"]

        stats_started = _now()
        stats_result = collect_stats(category)
        stats_duration = _duration_since(stats_started)
        summary_timings["stats"] = {"seconds": stats_duration}

        stats_payload = stats_result.get("payload", {}) if isinstance(stats_result, dict) else {}

        if trim_result is None:
            trim_payload = {
                "ok": True,
                "note": "trim skipped",
                "category": category,
                "trimmed": [],
                "items": stats_payload.get("items"),
                "total_bytes": stats_payload.get("total_bytes"),
                "total_gb": stats_payload.get("total_gb"),
                "max_size_gb": stats_payload.get("max_size_gb"),
            }
            trim_result = {
                "payload": trim_payload,
                "json": json.dumps(trim_payload, ensure_ascii=False, indent=2),
                "timings": {"duration_seconds": 0.0},
            }

        if warmup_result is None:
            warmup_counts = {
                "total": 0,
                "warmed": 0,
                "copied": 0,
                "missing": 0,
                "errors": 0,
            }
            warmup_payload = {
                "ok": True,
                "note": "warmup skipped",
                "counts": warmup_counts,
                "items": [],
                "timings": {"duration_seconds": 0.0},
            }
            warmup_result = {
                "payload": warmup_payload,
                "json": json.dumps(warmup_payload, ensure_ascii=False, indent=2),
                "total": 0,
                "warmed": 0,
                "copied": 0,
                "missing": 0,
                "errors": 0,
                "timings": {"duration_seconds": 0.0},
            }
            summary_timings.setdefault("warmup", warmup_result["timings"])
        else:
            warm_timings = warmup_result.get("timings") if isinstance(warmup_result.get("timings"), dict) else None
            if warm_timings:
                summary_timings.setdefault("warmup", warm_timings)

        entries_for_benchmark = _extract_benchmark_candidates(warmup_result, audit_result)
        benchmark_bytes_limit = int(max(0.0, float(benchmark_read_mb)) * 1024 * 1024)
        benchmark_result = _benchmark_cache_entries(
            entries_for_benchmark,
            sample_limit=int(max(0, benchmark_samples)),
            read_limit_bytes=benchmark_bytes_limit,
        )
        if benchmark_result.get("requested_samples", 0) > 0 or benchmark_result.get("read_samples", 0) > 0:
            summary_timings["benchmark"] = benchmark_result

        summary = make_ui_summary(
            stats=stats_result,
            audit=audit_result,
            warmup=warmup_result,
            trim=trim_result,
        )

        existing_timings = summary.get("timings") if isinstance(summary.get("timings"), dict) else {}
        merged_timings = dict(existing_timings)
        merged_timings.update(summary_timings)
        summary["timings"] = merged_timings

        ui_details = [
            f"Mode: {normalized_mode}",
            f"Category: {category}",
        ]
        audit_meta = summary.get("audit_meta") if isinstance(summary.get("audit_meta"), dict) else {}
        if audit_meta:
            ui_details.append(
                f"Audit cached/missing: {audit_meta.get('cached', 0)}/{audit_meta.get('missing', 0)}",
            )
        warm_counts = warmup_result.get("payload", {}).get("counts") if isinstance(warmup_result.get("payload"), dict) else {}
        if isinstance(warm_counts, dict):
            ui_details.append(
                f"Warmup warmed: {warm_counts.get('warmed', 0)}/{warm_counts.get('total', 0)}",
            )
        if summary_timings.get("benchmark"):
            throughput_bytes = summary_timings["benchmark"].get("throughput_bytes_per_s", 0.0)
            ui_details.append(
                f"Benchmark: {throughput_bytes / (1024 * 1024):.2f} MiB/s",
            )
        summary["ui"] = {
            "headline": "Arena Ops report",
            "details": ui_details,
        }

        summary_json = json.dumps(summary, ensure_ascii=False, indent=2)
        return (
            summary_json,
            warmup_result["json"],
            trim_result["json"],
        )


class ArenaAutoCacheAnalyze:
    """RU: Анализ активного воркфлоу и построение плана копирования без ввода.

    По умолчанию использует текущий воркфлоу (PromptServer), категорию
    "checkpoints", small-first стратегию для оценки плана и сразу запускает
    прогрев (auto_start). Выводит человекочитаемый отчет (summary_json) и
    план в JSON (plan_json), пригодный для Show Any.
    """

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        return {
            "required": {},
            "optional": {
                "workflow_json": (
                    "STRING",
                    {"default": "", "multiline": True, "description": t("input.workflow_json"), "tooltip": t("input.workflow_json")},
                ),
                "auto_start": (
                    "BOOLEAN",
                    {"default": True, "description": "Auto start warmup", "tooltip": "Auto start warmup"},
                ),
                "default_category": (
                    "STRING",
                    {"default": "checkpoints", "description": t("input.default_category"), "tooltip": t("input.default_category")},
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = (t("output.summary_json"), t("output.warmup_json"))
    RETURN_DESCRIPTIONS = RETURN_NAMES
    OUTPUT_TOOLTIPS = RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache"
    DESCRIPTION = t("node.analyze")
    OUTPUT_NODE = True

    def run(self, workflow_json: str = "", auto_start: bool = True, default_category: str = "checkpoints"):
        provided = (workflow_json or "").strip()
        effective_workflow = _resolve_workflow_json(provided)
        parsed = register_workflow_items("", effective_workflow, default_category)

        # Сформируем краткий план small-first: оценка размеров, где возможно
        plan_items: list[dict[str, object]] = []
        total_size = 0
        cached = 0
        missing = 0
        for entry in parsed:
            category = entry.get("category", default_category)
            name = entry.get("name", "")
            src_path = None
            size = None
            try:
                from folder_paths import get_full_path  # type: ignore
                src_path = get_full_path(category, name)  # type: ignore[arg-type]
            except Exception:
                src_path = None
            if src_path:
                try:
                    stat = Path(src_path).stat()
                    size = int(stat.st_size)
                except Exception:
                    size = None
            dst_path = _ensure_category_root(category) / name
            is_cached = dst_path.exists()
            if is_cached:
                cached += 1
            else:
                missing += 1
            if size is not None:
                total_size += size
            plan_items.append({
                "category": category,
                "name": name,
                "source": src_path,
                "dest": str(dst_path),
                "cached": is_cached,
                "size": size,
            })

        # Small-first
        plan_items.sort(key=lambda x: (0 if x.get("size") is None else 1, x.get("size") or 0))

        # Прогрев по желанию (auto_start)
        warmup_json = "{}"
        if auto_start:
            warm = warmup_items("", effective_workflow, default_category, parsed_items=parsed)
            warmup_json = warm.get("json", "{}")

        source = "provided" if provided else ("active" if effective_workflow else "none")
        summary = {
            "ok": True,
            "ui": {
                "headline": "Analyze plan",
                "details": [
                    f"Items: {len(parsed)}",
                    f"Cached/Missing: {cached}/{missing}",
                    f"Estimated size: {total_size/ (1024*1024):.2f} MiB",
                    f"Source: {source}",
                ],
            },
            "plan": plan_items,
        }
        summary_json = json.dumps(summary, ensure_ascii=False, indent=2)
        return (summary_json, warmup_json)


class ArenaGetActiveWorkflow:
    """RU: Возвращает текущий активный воркфлоу из PromptServer, если доступен."""

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        return {"required": {}}

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = (t("output.json"), t("output.summary_json"))
    RETURN_DESCRIPTIONS = RETURN_NAMES
    OUTPUT_TOOLTIPS = RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache"
    DESCRIPTION = t("node.get_workflow")
    OUTPUT_NODE = True

    def run(self):
        data = _load_active_workflow()
        ok = data is not None
        text = json.dumps(data if data is not None else {}, ensure_ascii=False, indent=2)
        summary = {
            "ok": ok,
            "ui": {
                "headline": "Active workflow",
                "details": ["Found" if ok else "Not found"],
            },
        }
        return (text, json.dumps(summary, ensure_ascii=False, indent=2))


NODE_CLASS_MAPPINGS.update(
    {
        "ArenaAutoCacheAudit": ArenaAutoCacheAudit,
        "ArenaAutoCacheAnalyze": ArenaAutoCacheAnalyze,
        "ArenaGetActiveWorkflow": ArenaGetActiveWorkflow,
        "ArenaAutoCacheConfig": ArenaAutoCacheConfig,
        "ArenaAutoCacheDashboard": ArenaAutoCacheDashboard,
        "ArenaAutoCacheOps": ArenaAutoCacheOps,
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
        "ArenaAutoCacheAnalyze": t("node.analyze"),
        "ArenaGetActiveWorkflow": t("node.get_workflow"),
        "ArenaAutoCacheConfig": t("node.config"),
        "ArenaAutoCacheDashboard": t("node.dashboard"),
        "ArenaAutoCacheOps": t("node.ops"),
        "ArenaAutoCacheStats": t("node.stats"),
        "ArenaAutoCacheStatsEx": t("node.statsex"),
        "ArenaAutoCacheTrim": t("node.trim"),
        "ArenaAutoCacheWarmup": t("node.warmup"),
        "ArenaAutoCacheManager": t("node.manager"),
    }
)
