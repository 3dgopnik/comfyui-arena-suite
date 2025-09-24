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
    "node.copy_status": "🅰️ Arena AutoCache: Copy Status",
    "input.cache_root": "Cache root directory",
    "input.max_size_gb": "Maximum cache size (GB)",
    "input.enable": "Enable AutoCache",
    "input.verbose": "Verbose logging",
    "input.min_size_gb": "Minimum size for caching (GB)",
    "input.skip_hardcoded_paths": "Skip hardcoded paths",
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
    min_size_gb: float = 1.0  # RU: Минимальный размер для кеширования (ГБ)
    min_size_mb: float = 1024.0  # RU: Минимальный размер для кеширования (МБ)
    skip_hardcoded_paths: bool = True  # RU: Пропускать модели с жёстко прописанными путями


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


def _extract_models_from_workflow_json(workflow: dict) -> list[dict]:
    """Extract model information from workflow JSON structure."""
    models = []
    
    if not isinstance(workflow, dict) or 'nodes' not in workflow:
        return models
    
    nodes = workflow.get('nodes', [])
    print(f"[ArenaAutoCacheSmart] Processing {len(nodes)} nodes for model extraction")
    
    # Node types that contain model information
    model_node_types = [
        'CheckpointLoaderSimple', 'CheckpointLoader', 'VAELoader', 'CLIPLoader', 
        'LoraLoader', 'LoraLoaderModelOnly', 'ControlNetLoader', 'UpscaleModelLoader',
        'StyleModelLoader', 'CLIPVisionLoader', 'UNETLoader', 'UnetLoaderGGUF',
        'IPAdapterModelLoader', 'InsightFaceLoader', 'DiffControlNetLoader'
    ]
    
    for i, node in enumerate(workflow.get('nodes', [])):
        if not isinstance(node, dict):
            continue
            
        # Проверяем и class_type и type (разные форматы workflow)
        class_type = node.get('class_type', '') or node.get('type', '')
        
        if class_type not in model_node_types:
            continue
            
        # Extract model information from inputs or widgets_values (разные форматы workflow)
        inputs = node.get('inputs', {})
        widgets_values = node.get('widgets_values', [])
        
        # Extract model name from common input keys
        model_name = None
        for key in ['ckpt_name', 'lora_name', 'control_net_name', 'model_name', 'vae_name', 'clip_name']:
            if key in inputs and inputs[key]:
                model_name = inputs[key]
                break
        
        # Если не нашли в inputs, пробуем widgets_values (первый элемент обычно модель)
        if not model_name and widgets_values and len(widgets_values) > 0:
            if isinstance(widgets_values[0], str):
                model_name = widgets_values[0]
                
        if not model_name or not isinstance(model_name, str):
            continue
            
        # Extract additional information from properties
        properties = node.get('properties', {})
        directory = properties.get('directory', '')
        url = properties.get('url', '')
        
        # Determine category based on class_type
        category = _get_model_category(class_type)
        
        model_info = {
            'name': model_name,
            'class_type': class_type,
            'category': category,
            'directory': directory,
            'url': url,
            'node_id': node.get('id', '')
        }
        
        models.append(model_info)
        print(f"[ArenaAutoCacheSmart] Found model: {model_name} ({category})")
    
    print(f"[ArenaAutoCacheSmart] Total unique models found: {len(models)}")
    return models


def _get_model_category(class_type: str) -> str:
    """Map ComfyUI node class types to model categories."""
    category_mapping = {
        'CheckpointLoaderSimple': 'checkpoints',
        'CheckpointLoader': 'checkpoints',
        'UNETLoader': 'checkpoints',
        'UnetLoaderGGUF': 'checkpoints',
        'VAELoader': 'vae',
        'CLIPLoader': 'clip',
        'LoraLoader': 'loras',
        'LoraLoaderModelOnly': 'loras',
        'ControlNetLoader': 'controlnet',
        'UpscaleModelLoader': 'upscale_models',
        'StyleModelLoader': 'style_models',
        'CLIPVisionLoader': 'clip_vision',
        'IPAdapterModelLoader': 'ipadapter',
        'InsightFaceLoader': 'insightface',
        'DiffControlNetLoader': 'controlnet'
    }
    return category_mapping.get(class_type, 'unknown')


def _load_last_executed_workflow() -> object | None:
    """Return the last executed workflow from ComfyUI history API."""
    try:
        import requests
        import json
        
        # Get history from ComfyUI API
        base_url = "http://127.0.0.1:8188"
        history_url = f"{base_url}/history"
        
        print(f"[ArenaAutoCache] Fetching history from {history_url}")
        
        response = requests.get(history_url, timeout=5)
        response.raise_for_status()
        history = response.json()
        
        if not history:
            print("[ArenaAutoCache] No history found")
            return None
        
        # Get the latest executed workflow
        latest_id = max(history.keys(), key=lambda k: history[k]["timestamp"])
        latest_item = history[latest_id]
        
        print(f"[ArenaAutoCache] Latest executed workflow: {latest_id}")
        
        # Get detailed workflow data
        detail_url = f"{base_url}/history/{latest_id}"
        detail_response = requests.get(detail_url, timeout=5)
        detail_response.raise_for_status()
        detail_data = detail_response.json()
        
        # Extract workflow (some builds store under 'prompt', some under 'workflow')
        workflow = detail_data.get("workflow") or detail_data.get("prompt")
        
        if workflow:
            print(f"[ArenaAutoCache] Found last executed workflow: {type(workflow)}")
            return workflow
        else:
            print("[ArenaAutoCache] No workflow found in history detail")
            return None
            
    except Exception as e:
        print(f"[ArenaAutoCache] Error fetching last executed workflow: {e}")
        return None


def _load_active_workflow(force_refresh: bool = False) -> object | None:
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
    print(f"[ArenaAutoCache] _load_active_workflow called with force_refresh={force_refresh}")

    # Принудительное обновление: очищаем кеш если запрошено
    if force_refresh:
        # Очищаем внутренний кеш workflow
        if hasattr(prompt_server, '_arena_workflow_cache'):
            delattr(prompt_server, '_arena_workflow_cache')

    # Метод 1: Попытка получить текущий canvas workflow через WebSocket или API
    try:
        # Проверяем, есть ли метод для получения текущего canvas
        if hasattr(prompt_server, 'get_current_workflow'):
            current_workflow = prompt_server.get_current_workflow()
            if current_workflow:
                candidates.append(current_workflow)
                print(f"[ArenaAutoCache] Found current workflow via get_current_workflow: {type(current_workflow)}")
        
        # Проверяем, есть ли атрибут с текущим workflow
        if hasattr(prompt_server, 'current_workflow'):
            current_workflow = getattr(prompt_server, 'current_workflow')
            if current_workflow:
                candidates.append(current_workflow)
                print(f"[ArenaAutoCache] Found current workflow via current_workflow attribute: {type(current_workflow)}")
        
        # Проверяем, есть ли метод для получения canvas через JavaScript API
        if hasattr(prompt_server, 'get_canvas_workflow'):
            canvas_workflow = prompt_server.get_canvas_workflow()
            if canvas_workflow:
                candidates.append(canvas_workflow)
                print(f"[ArenaAutoCache] Found canvas workflow via get_canvas_workflow: {type(canvas_workflow)}")
        
        # Проверяем, есть ли атрибут с canvas workflow
        if hasattr(prompt_server, 'canvas_workflow'):
            canvas_workflow = getattr(prompt_server, 'canvas_workflow')
            if canvas_workflow:
                candidates.append(canvas_workflow)
                print(f"[ArenaAutoCache] Found canvas workflow via canvas_workflow attribute: {type(canvas_workflow)}")
        
        # Проверяем WebSocket соединения для получения canvas
        if hasattr(prompt_server, 'sockets'):
            sockets = getattr(prompt_server, 'sockets')
            if sockets:
                print(f"[ArenaAutoCache] Found {len(sockets)} WebSocket connections")
                # Можем попробовать получить workflow через WebSocket API
                for i, socket in enumerate(sockets):
                    print(f"[ArenaAutoCache] WebSocket {i}: {type(socket)}")
                    print(f"[ArenaAutoCache] WebSocket {i} attributes: {dir(socket)}")
                    
                    if hasattr(socket, 'current_workflow'):
                        current_workflow = getattr(socket, 'current_workflow')
                        if current_workflow:
                            candidates.append(current_workflow)
                            print(f"[ArenaAutoCache] Found workflow in WebSocket: {type(current_workflow)}")
                    
                    # Проверяем, есть ли в WebSocket данные о canvas
                    if hasattr(socket, 'canvas_data'):
                        canvas_data = getattr(socket, 'canvas_data')
                        if canvas_data:
                            candidates.append(canvas_data)
                            print(f"[ArenaAutoCache] Found canvas data in WebSocket: {type(canvas_data)}")
                    
                    # Проверяем, есть ли в WebSocket данные о текущем состоянии
                    if hasattr(socket, 'current_state'):
                        current_state = getattr(socket, 'current_state')
                        if current_state:
                            candidates.append(current_state)
                            print(f"[ArenaAutoCache] Found current state in WebSocket: {type(current_state)}")
                    
                    # Проверяем, есть ли в WebSocket данные о текущем графе
                    if hasattr(socket, 'current_graph'):
                        current_graph = getattr(socket, 'current_graph')
                        if current_graph:
                            candidates.append(current_graph)
                            print(f"[ArenaAutoCache] Found current graph in WebSocket: {type(current_graph)}")
        
        # Метод 2: Попытка получить через внутренние структуры ComfyUI
        if hasattr(prompt_server, 'client_id'):
            client_id = getattr(prompt_server, 'client_id')
            print(f"[ArenaAutoCache] PromptServer client_id: {client_id}")
        
        # Метод 3: Попытка получить через глобальные переменные ComfyUI
        try:
            import sys
            print(f"[ArenaAutoCache] Searching {len(sys.modules)} modules for ComfyUI data...")
            # Ищем модули ComfyUI в sys.modules
            for module_name, module in sys.modules.items():
                if 'comfy' in module_name.lower():
                    print(f"[ArenaAutoCache] Found ComfyUI module: {module_name}")
                    if hasattr(module, 'current_workflow'):
                        current_workflow = getattr(module, 'current_workflow')
                        if current_workflow:
                            candidates.append(current_workflow)
                            print(f"[ArenaAutoCache] Found workflow in module {module_name}: {type(current_workflow)}")
                    
                    # Проверяем, есть ли в модуле данные о canvas
                    if hasattr(module, 'canvas_data'):
                        canvas_data = getattr(module, 'canvas_data')
                        if canvas_data:
                            candidates.append(canvas_data)
                            print(f"[ArenaAutoCache] Found canvas data in module {module_name}: {type(canvas_data)}")
                    
                    # Проверяем, есть ли в модуле данные о текущем состоянии
                    if hasattr(module, 'current_state'):
                        current_state = getattr(module, 'current_state')
                        if current_state:
                            candidates.append(current_state)
                            print(f"[ArenaAutoCache] Found current state in module {module_name}: {type(current_state)}")
                    
                    # Проверяем, есть ли в модуле данные о текущем графе
                    if hasattr(module, 'current_graph'):
                        current_graph = getattr(module, 'current_graph')
                        if current_graph:
                            candidates.append(current_graph)
                            print(f"[ArenaAutoCache] Found current graph in module {module_name}: {type(current_graph)}")
        except Exception as e:
            print(f"[ArenaAutoCache] Error searching ComfyUI modules: {e}")
        
        # Проверяем, есть ли кэшированный workflow
        if hasattr(prompt_server, '_arena_workflow_cache'):
            cached_workflow = getattr(prompt_server, '_arena_workflow_cache')
            if cached_workflow:
                candidates.append(cached_workflow)
                print(f"[ArenaAutoCache] Found cached workflow: {type(cached_workflow)}")
                
    except Exception as e:
        print(f"[ArenaAutoCache] Error getting current canvas workflow: {e}")

    prompt_queue = getattr(prompt_server, "prompt_queue", None)
    if prompt_queue is not None:
        # Правильный способ получения текущего workflow в ComfyUI Desktop
        if hasattr(prompt_queue, "get_current_queue"):
            try:
                running, queued = prompt_queue.get_current_queue()
                print(f"[ArenaAutoCache] get_current_queue: running={len(running)}, queued={len(queued)}")
                # Проверяем выполняющиеся задачи
                for item in running:
                    if isinstance(item, dict) and "prompt" in item:
                        candidates.append(item["prompt"])
                        print(f"[ArenaAutoCache] Found running prompt: {type(item['prompt'])}")
                # Проверяем очередь
                for item in queued:
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        prompt_data = item[1]
                        if isinstance(prompt_data, dict) and "prompt" in prompt_data:
                            candidates.append(prompt_data["prompt"])
                            print(f"[ArenaAutoCache] Found queued prompt: {type(prompt_data['prompt'])}")
            except Exception as e:
                print(f"[ArenaAutoCache] Error in get_current_queue: {e}")
                pass
        
        # Дополнительные методы (если есть)
        for method_name in ("get_current_prompt", "get_current_workflow", "get_last_prompt", "peek"):
            method = getattr(prompt_queue, method_name, None)
            if callable(method):
                try:
                    result = method()
                    if isinstance(result, dict) and "prompt" in result:
                        candidates.append(result["prompt"])
                    else:
                        candidates.append(result)
                except Exception:
                    pass
        
        # Поиск в очереди напрямую
        queue_data = getattr(prompt_queue, "queue", None)
        if isinstance(queue_data, list):
            for item in reversed(queue_data):
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    prompt_data = item[1]
                    if isinstance(prompt_data, dict) and "prompt" in prompt_data:
                        candidates.append(prompt_data["prompt"])
        
        # Поиск в выполняющихся задачах
        currently_running = getattr(prompt_queue, "currently_running", None)
        if isinstance(currently_running, dict):
            for item in currently_running.values():
                if isinstance(item, dict) and "prompt" in item:
                    candidates.append(item["prompt"])

    # Дополнительный поиск в PromptServer
    for attr in ("workflow", "current_workflow", "current_prompt"):
        if hasattr(prompt_server, attr):
            candidates.append(getattr(prompt_server, attr))
    
    # Попытка получить через методы PromptServer
    for method_name in ("get_current_prompt", "get_current_workflow"):
        method = getattr(prompt_server, method_name, None)
        if callable(method):
            try:
                result = method()
                if isinstance(result, dict) and "prompt" in result:
                    candidates.append(result["prompt"])
                else:
                    candidates.append(result)
            except Exception:
                pass

    print(f"[ArenaAutoCache] Total candidates found: {len(candidates)}")
    for i, candidate in enumerate(candidates):
        print(f"[ArenaAutoCache] Candidate {i}: {type(candidate)}")
        extracted = _extract(candidate)
        if extracted is not None:
            print(f"[ArenaAutoCache] Successfully extracted workflow: {type(extracted)}")
            return extracted
        else:
            print(f"[ArenaAutoCache] Failed to extract from candidate {i}")

    # Fallback: если workflow не найден, возвращаем None
    # Это означает, что нет активного workflow
    print("[ArenaAutoCache] No workflow found, returning None")
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


def _load_workflow_from_files() -> object | None:
    """Load the latest workflow from saved files."""
    try:
        import json
        from pathlib import Path
        
        # Поиск в различных местах
        search_paths = [
            Path("C:/ComfyUI/user/default/workflows"),
            Path("C:/ComfyUI/workflows"),
            Path.home() / "Documents" / "ComfyUI" / "workflows",
            Path.home() / "Desktop" / "ComfyUI" / "workflows",
        ]
        
        print(f"[ArenaAutoCacheSmart] Searching for workflow files in multiple locations...")
        json_files = []
        
        for search_path in search_paths:
            print(f"[ArenaAutoCacheSmart] Checking: {search_path}")
            if search_path.exists():
                json_files.extend(search_path.glob("*.json"))
        
        if json_files:
            # Сортируем по времени модификации (новые первыми)
            json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_file = json_files[0]
            print(f"[ArenaAutoCacheSmart] Using latest file: {latest_file}")
            with open(latest_file, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)
            print(f"[ArenaAutoCacheSmart] Loaded workflow from file: {type(workflow_data)}")
            return workflow_data
        else:
            print("[ArenaAutoCacheSmart] No workflow files found")
            return None
            
    except Exception as e:
        print(f"[ArenaAutoCacheSmart] Error loading workflow from files: {e}")
        return None


def _resolve_workflow_json(workflow_json: object, force_refresh: bool = False) -> object:
    """Return the provided workflow JSON or fall back to the active workflow, then to history."""

    if isinstance(workflow_json, str):
        if workflow_json.strip():
            return workflow_json
    elif workflow_json:
        return workflow_json

    # Сначала пробуем активный workflow
    fallback = _load_active_workflow(force_refresh=force_refresh)
    if fallback is not None:
        print("[ArenaAutoCacheSmart] Found active workflow from canvas")
        return fallback
    
    # Если активный workflow не найден, пробуем загрузить из файлов workflow
    print("[ArenaAutoCacheSmart] No active workflow found, trying to load from workflow files")
    file_workflow = _load_workflow_from_files()
    if file_workflow is not None:
        print("[ArenaAutoCacheSmart] Found workflow from files")
        return file_workflow
    
    # В последнюю очередь пробуем последний выполненный из истории
    print("[ArenaAutoCacheSmart] No workflow found in canvas or files, trying last executed workflow from history")
    history_workflow = _load_last_executed_workflow()
    if history_workflow is not None:
        print("[ArenaAutoCacheSmart] Found workflow from history API")
        return history_workflow
    
    print("[ArenaAutoCacheSmart] No workflow found in active canvas, files, or history")
    return workflow_json


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
    
    # Если ничего не найдено, возвращаем пустой список
    # Это означает, что в workflow нет моделей для кеширования
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


def _should_skip_by_size(src_path: Path, settings: ArenaCacheSettings) -> bool:
    """RU: Проверяет, нужно ли пропустить модель по размеру."""
    
    if settings.min_size_gb <= 0 and settings.min_size_mb <= 0:
        return False
    
    try:
        size_bytes = src_path.stat().st_size
        size_gb = size_bytes / (1024 ** 3)
        size_mb = size_bytes / (1024 ** 2)
        
        # Проверяем оба порога (ГБ и МБ)
        if settings.min_size_gb > 0 and size_gb < settings.min_size_gb:
            return True
        if settings.min_size_mb > 0 and size_mb < settings.min_size_mb:
            return True
            
        return False
    except Exception:
        return False


def _should_skip_hardcoded_path(src_path: Path, settings: ArenaCacheSettings) -> bool:
    """RU: Проверяет, нужно ли пропустить модель с жёстко прописанным путём."""
    
    if not settings.skip_hardcoded_paths:
        return False
    
    # RU: Список паттернов путей, которые обычно жёстко привязаны к своим папкам
    hardcoded_patterns = [
        # ControlNet модели часто привязаны к своим папкам
        "controlnet",
        "control_net", 
        # Некоторые специализированные модели
        "insightface",
        "ipadapter",
        "clip_vision",
        # Модели с абсолютными путями в названии
    ]
    
    path_str = str(src_path).lower()
    name_str = src_path.name.lower()
    
    # Проверяем паттерны в пути
    for pattern in hardcoded_patterns:
        if pattern in path_str or pattern in name_str:
            return True
    
    # Проверяем, содержит ли путь специфичные для ComfyUI папки
    comfy_specific = ["custom_nodes", "models", "checkpoints", "loras", "vae"]
    for folder in comfy_specific:
        if f"/{folder}/" in path_str or f"\\{folder}\\" in path_str:
            # Если модель в стандартной папке ComfyUI, не пропускаем
            continue
        if folder in path_str and len(Path(path_str).parts) > 3:
            # Если модель глубоко вложена в нестандартную структуру, пропускаем
            return True
    
    return False


def _update_copy_status(event: str, **kwargs) -> None:
    """RU: Обновляет глобальный статус копирования для визуального индикатора."""
    
    global _copy_status
    with _lock:
        if event == COPY_EVENT_STARTED:
            _copy_status["active_jobs"] += 1
            _copy_status["current_file"] = kwargs.get("filename", "unknown")
            _copy_status["last_update"] = _now()
        elif event == COPY_EVENT_COMPLETED:
            _copy_status["active_jobs"] = max(0, _copy_status["active_jobs"] - 1)
            _copy_status["completed_jobs"] += 1
            _copy_status["current_file"] = None
            _copy_status["last_update"] = _now()
        elif event == COPY_EVENT_FAILED:
            _copy_status["active_jobs"] = max(0, _copy_status["active_jobs"] - 1)
            _copy_status["failed_jobs"] += 1
            _copy_status["current_file"] = None
            _copy_status["last_update"] = _now()


def get_copy_status() -> dict[str, object]:
    """RU: Возвращает текущий статус копирования."""
    
    with _lock:
        return _copy_status.copy()


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
    filename = dst.name if dst is not None else (src.name if src is not None else None)
    
    # RU: Обновляем глобальный статус копирования
    _update_copy_status(event, filename=filename)
    
    payload: dict[str, object] = {
        "event": event,
        "category": category,
        "src": str(src) if src is not None else None,
        "dst": str(dst) if dst is not None else None,
        "filename": filename,
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
    min_size_gb: float | None = None,
    skip_hardcoded_paths: bool | None = None,
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
        
        new_min_size_gb = current.min_size_gb if min_size_gb is None else max(0.0, float(min_size_gb))
        new_skip_hardcoded = current.skip_hardcoded_paths if skip_hardcoded_paths is None else bool(skip_hardcoded_paths)

        tentative = ArenaCacheSettings(
            root=new_root,
            max_gb=new_max,
            enable=new_enable,
            verbose=new_verbose,
            min_size_gb=new_min_size_gb,
            skip_hardcoded_paths=new_skip_hardcoded,
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
        "min_size_gb": snapshot.min_size_gb,
        "skip_hardcoded_paths": snapshot.skip_hardcoded_paths,
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
    
    # RU: Применяем фильтры перед копированием
    if _should_skip_by_size(src, settings):
        _notify_copy_event(
            COPY_EVENT_SKIPPED,
            category=category,
            src=src,
            dst=dst,
            context=context,
            note=f"size < {settings.min_size_gb} GB",
        )
        return
    
    if _should_skip_hardcoded_path(src, settings):
        _notify_copy_event(
            COPY_EVENT_SKIPPED,
            category=category,
            src=src,
            dst=dst,
            context=context,
            note="hardcoded path detected",
        )
        return
    
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
                "min_size_gb": (
                    "FLOAT",
                    {
                        "default": settings.min_size_gb,
                        "min": 0.0,
                        "max": 100.0,
                        "step": 0.1,
                        "description": t("input.min_size_gb"),
                        "tooltip": t("input.min_size_gb"),
                    },
                ),
                "skip_hardcoded_paths": (
                    "BOOLEAN",
                    {
                        "default": settings.skip_hardcoded_paths,
                        "description": t("input.skip_hardcoded_paths"),
                        "tooltip": t("input.skip_hardcoded_paths"),
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

    def apply(self, cache_root: str, max_size_gb: int, enable: bool, verbose: bool, min_size_gb: float, skip_hardcoded_paths: bool):
        root_value = cache_root.strip()
        result = set_cache_settings(
            root=root_value or None,
            max_gb=max_size_gb,
            enable=enable,
            verbose=verbose,
            min_size_gb=min_size_gb,
            skip_hardcoded_paths=skip_hardcoded_paths,
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

        # Принудительно обновляем workflow если не предоставлен явно
        provided = (workflow_json or "").strip()
        force_refresh = not provided
        effective_workflow = _resolve_workflow_json(workflow_json, force_refresh=force_refresh)
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
        # Принудительно обновляем workflow если не предоставлен явно
        force_refresh = not provided
        effective_workflow = _resolve_workflow_json(provided, force_refresh=force_refresh)
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


class ArenaAutoCacheCopyStatus:
    """RU: Отображает текущий статус копирования моделей в кеш."""

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        return {
            "required": {},
            "optional": {
                "refresh_interval": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.1,
                        "max": 10.0,
                        "step": 0.1,
                        "description": "Refresh interval (seconds)",
                        "tooltip": "How often to refresh the status display",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = (t("output.json"), t("output.summary_json"))
    RETURN_DESCRIPTIONS = RETURN_NAMES
    OUTPUT_TOOLTIPS = RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache/Basic"
    DESCRIPTION = t("node.copy_status")
    OUTPUT_NODE = True

    def run(self, refresh_interval: float = 1.0):
        status = get_copy_status()
        settings = get_settings()
        
        # RU: Формируем детальный JSON статуса
        detailed_status = {
            "timestamp": _now(),
            "refresh_interval": refresh_interval,
            "copy_status": status,
            "settings": {
                "min_size_gb": settings.min_size_gb,
                "skip_hardcoded_paths": settings.skip_hardcoded_paths,
                "enable": settings.enable,
            },
            "filters": {
                "size_filter_enabled": settings.min_size_gb > 0,
                "size_threshold_gb": settings.min_size_gb,
                "hardcoded_filter_enabled": settings.skip_hardcoded_paths,
            },
        }
        
        # RU: Формируем краткий UI-отчет
        active_jobs = status.get("active_jobs", 0)
        completed_jobs = status.get("completed_jobs", 0)
        failed_jobs = status.get("failed_jobs", 0)
        current_file = status.get("current_file")
        
        if active_jobs > 0:
            headline = f"Copying: {current_file or 'unknown'}"
            details = [
                f"Active jobs: {active_jobs}",
                f"Completed: {completed_jobs}",
                f"Failed: {failed_jobs}",
                f"Size filter: {settings.min_size_gb} GB",
                f"Skip hardcoded: {settings.skip_hardcoded_paths}",
            ]
        else:
            headline = "Copy status: Idle"
            details = [
                f"Completed: {completed_jobs}",
                f"Failed: {failed_jobs}",
                f"Size filter: {settings.min_size_gb} GB",
                f"Skip hardcoded: {settings.skip_hardcoded_paths}",
            ]
        
        summary = {
            "ok": True,
            "ui": {
                "headline": headline,
                "details": details,
            },
        }
        
        detailed_json = json.dumps(detailed_status, ensure_ascii=False, indent=2)
        summary_json = json.dumps(summary, ensure_ascii=False, indent=2)
        
        return (detailed_json, summary_json)


class ArenaAutoCacheRefreshWorkflow:
    """RU: Принудительное обновление активного workflow.

    Очищает кеш workflow и заставляет ноды перечитать текущий активный workflow.
    Полезно когда ноды показывают старую информацию после смены workflow.
    """

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        return {
            "required": {},
            "optional": {},
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = (t("output.json"), t("output.summary_json"))
    RETURN_DESCRIPTIONS = RETURN_NAMES
    OUTPUT_TOOLTIPS = RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache/Utils"
    DESCRIPTION = "Force refresh active workflow"
    OUTPUT_NODE = True

    def run(self):
        """Force refresh and return current workflow."""
        # Очищаем allowlist
        reset_workflow_allowlist()
        
        # Принудительно загружаем новый workflow
        workflow = _load_active_workflow(force_refresh=True)
        
        # Пробуем зарегистрировать элементы для тестирования
        test_parsed = register_workflow_items("", workflow, "checkpoints")
        
        if workflow:
            workflow_str = json.dumps(workflow, indent=2) if isinstance(workflow, dict) else str(workflow)
            workflow_status = "Found"
        else:
            workflow_str = "{}"
            workflow_status = "Not found"
        
        summary = {
            "ok": True,
            "ui": {
                "headline": "Workflow Refresh",
                "details": [
                    "Status: Refreshed",
                    "Allowlist: Cleared",
                    f"Workflow: {workflow_status}",
                    f"Parsed items: {len(test_parsed)}",
                    f"Items: {[item.get('name', 'unknown') for item in test_parsed[:3]]}",
                ],
            },
        }
        
        return (workflow_str, json.dumps(summary, ensure_ascii=False, indent=2))


class ArenaAutoCachePrewarm:
    """RU: Предварительное кеширование моделей из workflow до запуска.

    Анализирует workflow и кеширует все необходимые модели заранее,
    чтобы ускорить выполнение. Работает с любым workflow JSON.
    """

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        return {
            "required": {},
            "optional": {
                "workflow_json": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "description": "Workflow JSON (auto-detected if empty)",
                        "tooltip": "Leave empty to auto-detect current workflow",
                    },
                ),
                "auto_start": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "description": "Auto start prewarming",
                        "tooltip": "Automatically start prewarming models",
                    },
                ),
                "categories": (
                    "STRING",
                    {
                        "default": "checkpoints,loras",
                        "description": "Categories to prewarm (comma-separated)",
                        "tooltip": "List of model categories to include in prewarming",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = (t("output.json"), t("output.summary_json"), "workflow_json")
    RETURN_DESCRIPTIONS = RETURN_NAMES
    OUTPUT_TOOLTIPS = RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache/Utils"
    DESCRIPTION = "Prewarm models from workflow before execution"
    OUTPUT_NODE = True

    def run(self, workflow_json: str = "", auto_start: bool = True, categories: str = "checkpoints,loras,controlnet,upscale_models,clip_vision,ipadapter,insightface,vae,clip"):
        """Analyze workflow and prewarm models."""
        # Если workflow не предоставлен, пытаемся получить текущий
        if not workflow_json.strip():
            workflow_json = _resolve_workflow_json("", force_refresh=True)
            if not workflow_json:
                # Пытаемся найти последний сохраненный workflow
                try:
                    comfyui_path = Path("C:/ComfyUI")
                    if comfyui_path.exists():
                        # Ищем в папке workflows
                        workflows_path = comfyui_path / "workflows"
                        if workflows_path.exists():
                            # Находим самый новый .json файл
                            json_files = list(workflows_path.glob("*.json"))
                            if json_files:
                                latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
                                with open(latest_file, 'r', encoding='utf-8') as f:
                                    workflow_json = json.load(f)
                                
                                summary = {
                                    "ok": True,
                                    "ui": {
                                        "headline": f"Prewarm: Using latest workflow",
                                        "details": [
                                            f"File: {latest_file.name}",
                                            "Found saved workflow file",
                                            "Analyzing models...",
                                        ],
                                    },
                                }
                            else:
                                summary = {
                                    "ok": False,
                                    "ui": {
                                        "headline": "Prewarm: No workflow found",
                                        "details": [
                                            "No active workflow detected",
                                            "No saved workflow files found",
                                            "Create a workflow with models first",
                                        ],
                                    },
                                }
                                return ("{}", json.dumps(summary, ensure_ascii=False, indent=2), "{}")
                        else:
                            summary = {
                                "ok": False,
                                "ui": {
                                    "headline": "Prewarm: No workflow found",
                                    "details": [
                                        "No active workflow detected",
                                        "No workflows folder found",
                                        "Create a workflow with models first",
                                    ],
                                },
                            }
                            return ("{}", json.dumps(summary, ensure_ascii=False, indent=2), "{}")
                    else:
                        summary = {
                            "ok": False,
                            "ui": {
                                "headline": "Prewarm: No workflow found",
                                "details": [
                                    "No active workflow detected",
                                    "ComfyUI path not found",
                                    "Create a workflow with models first",
                                ],
                            },
                        }
                        return ("{}", json.dumps(summary, ensure_ascii=False, indent=2), "{}")
                except Exception as e:
                    summary = {
                        "ok": False,
                        "ui": {
                            "headline": "Prewarm: No workflow found",
                            "details": [
                                "No active workflow detected",
                                f"Error searching files: {str(e)}",
                                "Create a workflow with models first",
                            ],
                        },
                    }
                    return ("{}", json.dumps(summary, ensure_ascii=False, indent=2), "{}")
        
        try:
            # Парсим workflow
            if isinstance(workflow_json, str):
                workflow_data = json.loads(workflow_json)
            else:
                workflow_data = workflow_json
            
            if isinstance(workflow_data, list):
                # Если это список, создаем словарь с nodes
                workflow_data = {"nodes": workflow_data}
            elif not isinstance(workflow_data, dict):
                raise ValueError("Invalid workflow format")
            elif "nodes" not in workflow_data:
                raise ValueError("Invalid workflow format")
            
            # Извлекаем модели из workflow
            category_list = [cat.strip() for cat in categories.split(",")]
            found_models = []
            
            for node in workflow_data.get("nodes", []):
                if not isinstance(node, dict):
                    continue
                
                inputs = node.get("inputs", {})
                class_type = node.get("class_type", "")
                
                # Ищем модели в inputs
                for key, value in inputs.items():
                    if isinstance(value, str) and value.strip():
                        # Проверяем расширение файла
                        if any(value.lower().endswith(ext) for ext in [".safetensors", ".ckpt", ".pt", ".pth", ".bin"]):
                            # Определяем категорию по class_type и key
                            category = self._guess_category(class_type, key, category_list)
                            if category:
                                found_models.append({
                                    "category": category,
                                    "name": value,
                                    "node_type": class_type,
                                    "input_key": key
                                })
            
            # Удаляем дубликаты
            unique_models = []
            seen = set()
            for model in found_models:
                key = (model["category"], model["name"])
                if key not in seen:
                    seen.add(key)
                    unique_models.append(model)
            
            # Кешируем модели если auto_start
            prewarm_results = []
            if auto_start and unique_models:
                for model in unique_models:
                    try:
                        from folder_paths import get_full_path
                        src_path = get_full_path(model["category"], model["name"])
                        if src_path and Path(src_path).exists():
                            # Проверяем фильтры
                            settings = get_settings()
                            if _should_skip_by_size(Path(src_path), settings):
                                prewarm_results.append({
                                    "model": model["name"],
                                    "status": "skipped_size",
                                    "reason": f"Size < {settings.min_size_gb}GB"
                                })
                                continue
                            
                            if _should_skip_hardcoded_path(Path(src_path), settings):
                                prewarm_results.append({
                                    "model": model["name"],
                                    "status": "skipped_hardcoded",
                                    "reason": "Hardcoded path"
                                })
                                continue
                            
                            # Копируем в кеш
                            cache_path = _ensure_category_root(model["category"]) / model["name"]
                            if not cache_path.exists():
                                src_path = get_full_path(model["category"], model["name"])
                                _copy_into_cache_lru(Path(src_path), cache_path, model["category"])
                                prewarm_results.append({
                                    "model": model["name"],
                                    "status": "cached",
                                    "category": model["category"]
                                })
                            else:
                                prewarm_results.append({
                                    "model": model["name"],
                                    "status": "already_cached",
                                    "category": model["category"]
                                })
                        else:
                            prewarm_results.append({
                                "model": model["name"],
                                "status": "not_found",
                                "reason": "File not found"
                            })
                    except Exception as e:
                        prewarm_results.append({
                            "model": model["name"],
                            "status": "error",
                            "reason": str(e)
                        })
            
            # Формируем результат
            result = {
                "ok": True,
                "workflow_analysis": {
                    "total_nodes": len(workflow_data.get("nodes", [])),
                    "models_found": len(unique_models),
                    "categories_checked": category_list,
                },
                "models": unique_models,
                "prewarm_results": prewarm_results if auto_start else [],
            }
            
            # UI отчет
            cached_count = len([r for r in prewarm_results if r["status"] == "cached"])
            skipped_count = len([r for r in prewarm_results if r["status"].startswith("skipped")])
            error_count = len([r for r in prewarm_results if r["status"] in ["error", "not_found"]])
            
            summary = {
                "ok": True,
                "ui": {
                    "headline": f"Prewarm: {len(unique_models)} models analyzed",
                    "details": [
                        f"Models found: {len(unique_models)}",
                        f"Cached: {cached_count}",
                        f"Skipped: {skipped_count}",
                        f"Errors: {error_count}",
                        f"Categories: {', '.join(category_list)}",
                    ],
                },
            }
            
            # Преобразуем workflow в строку для возврата
            workflow_str = json.dumps(workflow_data, ensure_ascii=False, indent=2) if isinstance(workflow_data, dict) else str(workflow_json)
            
            return (
                json.dumps(result, ensure_ascii=False, indent=2),
                json.dumps(summary, ensure_ascii=False, indent=2),
                workflow_str
            )
            
        except Exception as e:
            summary = {
                "ok": False,
                "ui": {
                    "headline": "Prewarm: Error",
                    "details": [
                        f"Error: {str(e)}",
                        "Check workflow JSON format",
                    ],
                },
            }
            workflow_str = str(workflow_json) if workflow_json else "{}"
            return ("{}", json.dumps(summary, ensure_ascii=False, indent=2), workflow_str)
    
    def _guess_category(self, class_type: str, input_key: str, categories: list) -> str | None:
        """Guess model category from node class and input key."""
        class_type_lower = class_type.lower()
        input_key_lower = input_key.lower()
        
        # Checkpoint models
        if any(keyword in class_type_lower for keyword in ["checkpoint", "model"]):
            if any(keyword in input_key_lower for keyword in ["ckpt", "model", "checkpoint"]):
                return "checkpoints" if "checkpoints" in categories else None
        
        # LoRA models
        if "lora" in class_type_lower or "lora" in input_key_lower:
            return "loras" if "loras" in categories else None
        
        # ControlNet models
        if "controlnet" in class_type_lower or "controlnet" in input_key_lower:
            return "controlnet" if "controlnet" in categories else None
        
        # Upscale models
        if any(keyword in class_type_lower for keyword in ["upscale", "upscaler"]):
            return "upscale_models" if "upscale_models" in categories else None
        
        # CLIP Vision models
        if "clip" in class_type_lower and "vision" in class_type_lower:
            return "clip_vision" if "clip_vision" in categories else None
        
        # IP-Adapter models
        if "ipadapter" in class_type_lower:
            return "ipadapter" if "ipadapter" in categories else None
        
        # InsightFace models
        if "insightface" in class_type_lower:
            return "insightface" if "insightface" in categories else None
        
        # Generic fallback
        if any(keyword in input_key_lower for keyword in ["model", "ckpt", "lora", "controlnet"]):
            for category in categories:
                if category in input_key_lower:
                    return category
        
        return None


class ArenaAutoCachePrewarmFromFile:
    """RU: Предварительное кеширование моделей из сохраненного workflow файла.

    Загружает workflow из файла и кеширует все необходимые модели.
    Полезно для работы с пресетами и сохраненными workflow.
    """

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        return {
            "required": {
                "workflow_file": (
                    "STRING",
                    {
                        "default": "",
                        "description": "Path to workflow file (.json)",
                        "tooltip": "Path to saved workflow file, e.g., 'workflows/my_workflow.json'",
                    },
                ),
            },
            "optional": {
                "auto_start": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "description": "Auto start prewarming",
                        "tooltip": "Automatically start prewarming models",
                    },
                ),
                "categories": (
                    "STRING",
                    {
                        "default": "checkpoints,loras",
                        "description": "Categories to prewarm (comma-separated)",
                        "tooltip": "List of model categories to include in prewarming",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = (t("output.json"), t("output.summary_json"), "workflow_json")
    RETURN_DESCRIPTIONS = RETURN_NAMES
    OUTPUT_TOOLTIPS = RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache/Utils"
    DESCRIPTION = "Prewarm models from saved workflow file"
    OUTPUT_NODE = True

    def run(self, workflow_file: str = "", auto_start: bool = True, categories: str = "checkpoints,loras,controlnet,upscale_models,clip_vision,ipadapter,insightface,vae,clip"):
        """Load workflow from file and prewarm models."""
        if not workflow_file.strip():
            summary = {
                "ok": False,
                "ui": {
                    "headline": "Prewarm From File: No file specified",
                    "details": [
                        "Please specify workflow file path",
                        "Example: 'workflows/my_workflow.json'",
                    ],
                },
            }
            return ("{}", json.dumps(summary, ensure_ascii=False, indent=2), "{}")
        
        try:
            # Определяем путь к файлу
            if not Path(workflow_file).is_absolute():
                # Относительный путь - ищем в папке ComfyUI
                comfyui_path = Path("C:/ComfyUI")  # Можно сделать более умный поиск
                full_path = comfyui_path / workflow_file
            else:
                full_path = Path(workflow_file)
            
            # Проверяем существование файла
            if not full_path.exists():
                summary = {
                    "ok": False,
                    "ui": {
                        "headline": "Prewarm From File: File not found",
                        "details": [
                            f"File not found: {full_path}",
                            "Check the file path",
                        ],
                    },
                }
                return ("{}", json.dumps(summary, ensure_ascii=False, indent=2), "{}")
            
            # Читаем файл
            with open(full_path, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)
            
            if isinstance(workflow_data, list):
                # Если это список, создаем словарь с nodes
                workflow_data = {"nodes": workflow_data}
            elif not isinstance(workflow_data, dict):
                raise ValueError("Invalid workflow file format")
            elif "nodes" not in workflow_data:
                raise ValueError("Invalid workflow file format")
            
            # Используем ту же логику анализа что и в ArenaAutoCachePrewarm
            category_list = [cat.strip() for cat in categories.split(",")]
            found_models = []
            
            for node in workflow_data.get("nodes", []):
                if not isinstance(node, dict):
                    continue
                
                inputs = node.get("inputs", {})
                class_type = node.get("class_type", "")
                
                # Ищем модели в inputs
                for key, value in inputs.items():
                    if isinstance(value, str) and value.strip():
                        # Проверяем расширение файла
                        if any(value.lower().endswith(ext) for ext in [".safetensors", ".ckpt", ".pt", ".pth", ".bin"]):
                            # Определяем категорию по class_type и key
                            category = self._guess_category(class_type, key, category_list)
                            if category:
                                found_models.append({
                                    "category": category,
                                    "name": value,
                                    "node_type": class_type,
                                    "input_key": key
                                })
            
            # Удаляем дубликаты
            unique_models = []
            seen = set()
            for model in found_models:
                key = (model["category"], model["name"])
                if key not in seen:
                    seen.add(key)
                    unique_models.append(model)
            
            # Кешируем модели если auto_start
            prewarm_results = []
            if auto_start and unique_models:
                for model in unique_models:
                    try:
                        from folder_paths import get_full_path
                        src_path = get_full_path(model["category"], model["name"])
                        if src_path and Path(src_path).exists():
                            # Проверяем фильтры
                            settings = get_settings()
                            if _should_skip_by_size(Path(src_path), settings):
                                prewarm_results.append({
                                    "model": model["name"],
                                    "status": "skipped_size",
                                    "reason": f"Size < {settings.min_size_gb}GB"
                                })
                                continue
                            
                            if _should_skip_hardcoded_path(Path(src_path), settings):
                                prewarm_results.append({
                                    "model": model["name"],
                                    "status": "skipped_hardcoded",
                                    "reason": "Hardcoded path"
                                })
                                continue
                            
                            # Копируем в кеш
                            cache_path = _ensure_category_root(model["category"]) / model["name"]
                            if not cache_path.exists():
                                src_path = get_full_path(model["category"], model["name"])
                                _copy_into_cache_lru(Path(src_path), cache_path, model["category"])
                                prewarm_results.append({
                                    "model": model["name"],
                                    "status": "cached",
                                    "category": model["category"]
                                })
                            else:
                                prewarm_results.append({
                                    "model": model["name"],
                                    "status": "already_cached",
                                    "category": model["category"]
                                })
                        else:
                            prewarm_results.append({
                                "model": model["name"],
                                "status": "not_found",
                                "reason": "File not found"
                            })
                    except Exception as e:
                        prewarm_results.append({
                            "model": model["name"],
                            "status": "error",
                            "reason": str(e)
                        })
            
            # Формируем результат
            result = {
                "ok": True,
                "file_info": {
                    "file_path": str(full_path),
                    "file_size": full_path.stat().st_size,
                },
                "workflow_analysis": {
                    "total_nodes": len(workflow_data.get("nodes", [])),
                    "models_found": len(unique_models),
                    "categories_checked": category_list,
                },
                "models": unique_models,
                "prewarm_results": prewarm_results if auto_start else [],
            }
            
            # UI отчет
            cached_count = len([r for r in prewarm_results if r["status"] == "cached"])
            skipped_count = len([r for r in prewarm_results if r["status"].startswith("skipped")])
            error_count = len([r for r in prewarm_results if r["status"] in ["error", "not_found"]])
            
            summary = {
                "ok": True,
                "ui": {
                    "headline": f"Prewarm From File: {len(unique_models)} models analyzed",
                    "details": [
                        f"File: {full_path.name}",
                        f"Models found: {len(unique_models)}",
                        f"Cached: {cached_count}",
                        f"Skipped: {skipped_count}",
                        f"Errors: {error_count}",
                    ],
                },
            }
            
            return (
                json.dumps(result, ensure_ascii=False, indent=2),
                json.dumps(summary, ensure_ascii=False, indent=2),
                json.dumps(workflow_data, ensure_ascii=False, indent=2)
            )
            
        except Exception as e:
            summary = {
                "ok": False,
                "ui": {
                    "headline": "Prewarm From File: Error",
                    "details": [
                        f"Error: {str(e)}",
                        "Check file path and format",
                    ],
                },
            }
            return ("{}", json.dumps(summary, ensure_ascii=False, indent=2), "{}")
    
    def _guess_category(self, class_type: str, input_key: str, categories: list) -> str | None:
        """Guess model category from node class and input key."""
        class_type_lower = class_type.lower()
        input_key_lower = input_key.lower()
        
        # Checkpoint models
        if any(keyword in class_type_lower for keyword in ["checkpoint", "model"]):
            if any(keyword in input_key_lower for keyword in ["ckpt", "model", "checkpoint"]):
                return "checkpoints" if "checkpoints" in categories else None
        
        # LoRA models
        if "lora" in class_type_lower or "lora" in input_key_lower:
            return "loras" if "loras" in categories else None
        
        # ControlNet models
        if "controlnet" in class_type_lower or "controlnet" in input_key_lower:
            return "controlnet" if "controlnet" in categories else None
        
        # Upscale models
        if any(keyword in class_type_lower for keyword in ["upscale", "upscaler"]):
            return "upscale_models" if "upscale_models" in categories else None
        
        # CLIP Vision models
        if "clip" in class_type_lower and "vision" in class_type_lower:
            return "clip_vision" if "clip_vision" in categories else None
        
        # IP-Adapter models
        if "ipadapter" in class_type_lower:
            return "ipadapter" if "ipadapter" in categories else None
        
        # InsightFace models
        if "insightface" in class_type_lower:
            return "insightface" if "insightface" in categories else None
        
        # Generic fallback
        if any(keyword in input_key_lower for keyword in ["model", "ckpt", "lora", "controlnet"]):
            for category in categories:
                if category in input_key_lower:
                    return category
        
        return None


class ArenaAutoCacheSmart:
    """RU: Умная нода для кеширования моделей.

    Автоматически определяет workflow (активный или из файла),
    анализирует модели, применяет фильтры и кеширует.
    Одна нода для всех задач кеширования.
    """

    @classmethod
    def INPUT_TYPES(cls):  # noqa: N802
        return {
            "required": {},
            "optional": {
                "workflow_source": (
                    ["auto", "file", "json"],
                    {
                        "default": "auto",
                        "description": "Workflow source",
                        "tooltip": "auto = find active/file, file = load from file, json = paste JSON",
                    },
                ),
                "workflow_file": (
                    "STRING",
                    {
                        "default": "",
                        "description": "Workflow file path (if source=file)",
                        "tooltip": "Path to workflow file, e.g., 'workflows/default.json'",
                    },
                ),
                "workflow_json": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "description": "Workflow JSON (if source=json)",
                        "tooltip": "Paste workflow JSON here",
                    },
                ),
                "auto_cache": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "description": "Auto cache models",
                        "tooltip": "Automatically cache found models",
                    },
                ),
                "show_analysis": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "description": "Show analysis",
                        "tooltip": "Show detailed analysis of found models",
                    },
                ),
                "categories": (
                    "STRING",
                    {
                        "default": "checkpoints,loras",
                        "description": "Categories to process",
                        "tooltip": "Comma-separated list of model categories",
                    },
                ),
                "workflow_path_display": (
                    "STRING",
                    {
                        "default": "No workflow loaded",
                        "description": "Current workflow path",
                        "tooltip": "Shows the path to the currently loaded workflow",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = (t("output.json"), t("output.summary_json"), "workflow_json")
    RETURN_DESCRIPTIONS = RETURN_NAMES
    OUTPUT_TOOLTIPS = RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = "Arena/AutoCache"
    DESCRIPTION = "Smart model caching - one node for all tasks"
    OUTPUT_NODE = True

    def run(
        self,
        workflow_source: str = "auto",
        workflow_file: str = "",
        workflow_json: str = "",
        auto_cache: bool = True,
        show_analysis: bool = True,
        categories: str = "checkpoints,loras",
        workflow_path_display: str = "No workflow loaded"
    ):
        """Smart workflow analysis and caching."""
        # print(f"[ArenaAutoCacheSmart] Starting with source={workflow_source}, auto_cache={auto_cache}")
        
        # Проверяем, не получили ли мы данные от ArenaAutoCacheAnalyze
        if workflow_json and workflow_json.strip():
            try:
                # Пытаемся парсить как JSON
                parsed_json = json.loads(workflow_json)
                if isinstance(parsed_json, list) and len(parsed_json) > 0 and isinstance(parsed_json[0], dict):
                    # Это список моделей от ArenaAutoCacheAnalyze
                    # print(f"[ArenaAutoCacheSmart] Detected models list from ArenaAutoCacheAnalyze: {len(parsed_json)} models")
                    
                    # Конвертируем в формат ArenaAutoCacheSmart
                    found_models = []
                    for model_data in parsed_json:
                        if isinstance(model_data, dict) and "name" in model_data and "category" in model_data:
                            found_models.append({
                                "name": model_data["name"],
                                "category": model_data["category"],
                                "path": model_data.get("path", "N/A")
                            })
                    
                    if found_models:
                        # print(f"[ArenaAutoCacheSmart] Converted {len(found_models)} models from ArenaAutoCacheAnalyze")
                        
                        # Кешируем модели если нужно
                        cache_results = []
                        if auto_cache:
                            # print(f"[ArenaAutoCacheSmart] Starting cache process for {len(found_models)} models")
                            cache_results = self._cache_models_with_progress(found_models)
                            # print(f"[ArenaAutoCacheSmart] Cache process completed. Results: {len(cache_results)}")
                        
                        # Формируем результат
                        cached_count = len([r for r in cache_results if r["status"] == "cached"])
                        skipped_count = len([r for r in cache_results if r["status"].startswith("skipped")])
                        error_count = len([r for r in cache_results if r["status"] in ["error", "not_found"]])
                        
                        details = [
                            f"Source: ArenaAutoCacheAnalyze",
                            f"Models found: {len(found_models)}",
                            f"Cached: {cached_count}",
                            f"Skipped: {skipped_count}",
                            f"Errors: {error_count}",
                        ]
                        
                        summary = {
                            "ok": True,
                            "ui": {
                                "headline": f"Smart Cache: {len(found_models)} models processed",
                                "details": details,
                            },
                            "workflow_path": "From ArenaAutoCacheAnalyze"
                        }
                        
                        # Обновляем workflow_path_display
                        current_workflow_path = "From ArenaAutoCacheAnalyze"
                        
                        return (json.dumps(summary, ensure_ascii=False, indent=2), summary, workflow_json)
            except json.JSONDecodeError:
                # Не JSON, продолжаем обычную обработку
                pass
        
        workflow_data = None
        source_info = ""
        current_workflow_path = "No workflow loaded"
        
        try:
            # Получаем workflow в зависимости от источника
            if workflow_source == "auto":
                print("[ArenaAutoCacheSmart] Auto mode: analyzing current canvas for model nodes")
                
                # Сначала пробуем получить активный canvas workflow
                workflow_data = _load_active_workflow(force_refresh=True)
                if workflow_data:
                    print(f"[ArenaAutoCacheSmart] Found active canvas workflow: {type(workflow_data)}")
                    current_workflow_path = "Active canvas workflow"
                    
                    # Регистрируем элементы workflow для заполнения allowlist
                    default_category = "checkpoints"  # Основная категория по умолчанию
                    registered_items = register_workflow_items("", workflow_data, default_category)
                    print(f"[ArenaAutoCacheSmart] Registered {len(registered_items)} items from workflow")
                    
                    # Пробуем новый метод анализа JSON workflow
                    if isinstance(workflow_data, dict):
                        json_models = _extract_models_from_workflow_json(workflow_data)
                        if json_models:
                            print(f"[ArenaAutoCacheSmart] Extracted {len(json_models)} models from JSON workflow")
                            # Конвертируем в формат, ожидаемый ArenaAutoCacheSmart
                            found_models = self._convert_json_models_to_arena_format(json_models)
                        else:
                            # Fallback на старый метод
                            found_models = self._extract_models_from_workflow(workflow_data)
                    else:
                        # Fallback на старый метод
                        found_models = self._extract_models_from_workflow(workflow_data)
                    
                    print(f"[ArenaAutoCacheSmart] Final extracted {len(found_models)} models from active canvas workflow")
                else:
                    # Если активный canvas недоступен, пробуем анализ текущего canvas
                    print("[ArenaAutoCacheSmart] Active canvas workflow not available, analyzing current canvas")
                    found_models = self._analyze_current_canvas()
                    workflow_data = {"nodes": []}  # Создаем пустой workflow для совместимости
                
                if found_models:
                    source_info = "Current canvas workflow"
                    # print(f"[ArenaAutoCacheSmart] Found {len(found_models)} models in current canvas workflow")
                    
                    # Если workflow_data не был получен из _load_active_workflow, создаем фиктивный
                    if not workflow_data:
                        workflow_data = {"nodes": []}
                    
                    # Кешируем найденные модели
                    if auto_cache and found_models:
                        # Убеждаемся, что патч путей активен
                        _apply_folder_paths_patch_locked()
                        print(f"[ArenaAutoCacheSmart] Starting cache process for {len(found_models)} models")
                        cache_results = self._cache_models_with_progress(found_models)
                        print(f"[ArenaAutoCacheSmart] Cache process completed. Results: {len(cache_results)}")
                        
                        # Формируем результат
                        result = {
                            "ok": True,
                            "source": source_info,
                            "canvas_analysis": {
                                "models_found": len(found_models),
                                "categories_checked": [cat.strip() for cat in categories.split(",")],
                            },
                            "models": found_models,
                            "cache_results": cache_results,
                        }
                        
                        # UI отчет
                        cached_count = len([r for r in cache_results if r["status"] == "cached"])
                        skipped_count = len([r for r in cache_results if r["status"].startswith("skipped")])
                        error_count = len([r for r in cache_results if r["status"] in ["error", "not_found"]])
                        
                        details = [
                            f"Source: {source_info}",
                            f"Models found: {len(found_models)}",
                            f"Cached: {cached_count}",
                            f"Skipped: {skipped_count}",
                            f"Errors: {error_count}",
                        ]
                        
                        summary = {
                            "ok": True,
                            "ui": {
                                "headline": f"Smart Cache: {len(found_models)} models processed",
                                "details": details,
                            },
                        }
                        
                        return (
                            json.dumps(result, ensure_ascii=False, indent=2),
                            json.dumps(summary, ensure_ascii=False, indent=2),
                            json.dumps(workflow_data, ensure_ascii=False, indent=2)
                        )
                else:
                    print("[ArenaAutoCacheSmart] No models found in current canvas, searching for saved files")
                    # Ищем последний сохраненный файл в разных местах
                    search_paths = [
                        # ComfyUI Desktop user data (основные места)
                        Path.home() / "AppData" / "Roaming" / "ComfyUI" / "workflows",
                        Path.home() / "AppData" / "Local" / "ComfyUI" / "workflows",
                        Path.home() / "AppData" / "Roaming" / "ComfyUI" / "user" / "workflows",
                        Path.home() / "AppData" / "Local" / "ComfyUI" / "user" / "workflows",
                        # ComfyUI Desktop installation paths
                        Path("C:/Users") / Path.home().name / "AppData" / "Local" / "Programs" / "@comfyorgcomfyui-electron" / "resources" / "ComfyUI" / "workflows",
                        Path("C:/Users") / Path.home().name / "AppData" / "Roaming" / "ComfyUI" / "workflows",
                        Path("C:/Users") / Path.home().name / "AppData" / "Local" / "ComfyUI" / "workflows",
                        # ComfyUI installation
                        Path("C:/ComfyUI/workflows"),
                        Path("C:/ComfyUI/user/workflows"),
                        Path("C:/ComfyUI/user/default/workflows"),
                        # Fallback locations
                        Path("C:/ComfyUI"),
                        Path(".") / "workflows",
                        # Дополнительные места для ComfyUI Desktop
                        Path.home() / "Documents" / "ComfyUI" / "workflows",
                        Path.home() / "Desktop" / "ComfyUI" / "workflows",
                    ]
                    
                    print(f"[ArenaAutoCacheSmart] Searching for workflow files in multiple locations...")
                    json_files = []
                    
                    for search_path in search_paths:
                        print(f"[ArenaAutoCacheSmart] Checking: {search_path}")
                        if search_path.exists():
                            if search_path.is_dir():
                                # Ищем JSON файлы в папке
                                found_files = list(search_path.glob("*.json"))
                                print(f"[ArenaAutoCacheSmart] Found {len(found_files)} JSON files in {search_path}")
                                json_files.extend(found_files)
                            else:
                                # Это файл, проверяем расширение
                                if search_path.suffix.lower() == '.json':
                                    print(f"[ArenaAutoCacheSmart] Found JSON file: {search_path}")
                                    json_files.append(search_path)
                    
                    if json_files:
                        # Сортируем по времени изменения и берем самый новый
                        json_files = sorted(json_files, key=lambda f: f.stat().st_mtime, reverse=True)
                        latest_file = json_files[0]
                        print(f"[ArenaAutoCacheSmart] Using latest file: {latest_file}")
                        with open(latest_file, 'r', encoding='utf-8') as f:
                            workflow_data = json.load(f)
                        source_info = f"Latest file: {latest_file.name}"
                        print(f"[ArenaAutoCacheSmart] Loaded workflow from file: {type(workflow_data)}")
                    else:
                        return self._error_result("No workflow found", [
                            "No active workflow detected",
                            "No saved workflow files found in any location",
                            "Create a workflow with models first"
                        ])
            
            elif workflow_source == "file":
                print(f"[ArenaAutoCacheSmart] File mode: loading from {workflow_file}")
                current_workflow_path = f"File: {workflow_file}"
                if not workflow_file.strip():
                    return self._error_result("No file specified", [
                        "Please specify workflow file path",
                        "Example: 'workflows/default.json'"
                    ])
                
                # Определяем путь к файлу
                if not Path(workflow_file).is_absolute():
                    comfyui_path = Path("C:/ComfyUI")
                    full_path = comfyui_path / workflow_file
                else:
                    full_path = Path(workflow_file)
                
                print(f"[ArenaAutoCacheSmart] Full path: {full_path}")
                if not full_path.exists():
                    return self._error_result("File not found", [
                        f"File not found: {full_path}",
                        "Check the file path"
                    ])
                
                with open(full_path, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                source_info = f"File: {full_path.name}"
                print(f"[ArenaAutoCacheSmart] Loaded workflow from file: {type(workflow_data)}")
            
            elif workflow_source == "json":
                print(f"[ArenaAutoCacheSmart] JSON mode: parsing provided JSON")
                current_workflow_path = "JSON: Pasted workflow data"
                if not workflow_json.strip():
                    return self._error_result("No JSON provided", [
                        "Please provide workflow JSON",
                        "Paste workflow from ComfyUI interface"
                    ])
                
                # Пытаемся парсить JSON
                try:
                    workflow_data = json.loads(workflow_json)
                    source_info = "Provided JSON"
                    print(f"[ArenaAutoCacheSmart] Parsed JSON workflow: {type(workflow_data)}")
                except json.JSONDecodeError as e:
                    return self._error_result("Invalid JSON format", [
                        f"JSON parsing error: {str(e)}",
                        "Check JSON syntax"
                    ])
            
            # Проверяем формат workflow
            print(f"[ArenaAutoCacheSmart] Validating workflow format: {type(workflow_data)}")
            if isinstance(workflow_data, list):
                # Если это список, проверяем, что это за список
                if len(workflow_data) > 0 and isinstance(workflow_data[0], dict):
                    # Если это список словарей (возможно, от ArenaAutoCacheAnalyze), 
                    # создаем фиктивный workflow
                    print("[ArenaAutoCacheSmart] Detected list of dictionaries, creating dummy workflow")
                    workflow_data = {"nodes": []}
                else:
                    # Если это список узлов, создаем словарь с nodes
                    print("[ArenaAutoCacheSmart] Converting list to dict with 'nodes' key")
                    workflow_data = {"nodes": workflow_data}
            elif not isinstance(workflow_data, dict):
                return self._error_result("Invalid workflow format", [
                    "Workflow must be a valid JSON object or array",
                    "Check workflow format"
                ])
            elif "nodes" not in workflow_data:
                return self._error_result("Invalid workflow format", [
                    "Workflow must contain 'nodes' array",
                    "Check workflow format"
                ])
            
            # Исправляем проблему с links (Alert ошибка)
            if "links" in workflow_data:
                links = workflow_data["links"]
                if isinstance(links, list):
                    # Проверяем и исправляем неправильные links
                    corrected_links = []
                    for link in links:
                        if isinstance(link, list) and len(link) >= 6:
                            corrected_links.append(link)
                        elif isinstance(link, dict):
                            # Конвертируем dict в list если нужно
                            if all(key in link for key in ["from", "to", "from_slot", "to_slot", "type", "weight"]):
                                corrected_links.append([
                                    link["from"], link["to"], link["from_slot"], 
                                    link["to_slot"], link["type"], link["weight"]
                                ])
                    workflow_data["links"] = corrected_links
                    print(f"[ArenaAutoCacheSmart] Corrected {len(corrected_links)} links in workflow")
            
            print(f"[ArenaAutoCacheSmart] Workflow validated. Nodes count: {len(workflow_data.get('nodes', []))}")
            
            # Анализируем workflow
            category_list = [cat.strip() for cat in categories.split(",")]
            print(f"[ArenaAutoCacheSmart] Analyzing workflow with categories: {category_list}")
            
            # Используем новый метод анализа JSON workflow
            json_models = _extract_models_from_workflow_json(workflow_data)
            if json_models:
                print(f"[ArenaAutoCacheSmart] Extracted {len(json_models)} models from JSON workflow")
                found_models = self._convert_json_models_to_arena_format(json_models)
            else:
                # Fallback на старый метод
                found_models = self._extract_models_from_workflow(workflow_data)
            
            print(f"[ArenaAutoCacheSmart] Found {len(found_models)} models before deduplication")
            
            # Удаляем дубликаты
            unique_models = []
            seen = set()
            for model in found_models:
                key = (model["category"], model["name"])
                if key not in seen:
                    seen.add(key)
                    unique_models.append(model)
            
            print(f"[ArenaAutoCacheSmart] Unique models after deduplication: {len(unique_models)}")
            for model in unique_models:
                print(f"[ArenaAutoCacheSmart] - {model['category']}: {model['name']}")
            
            # Кешируем модели если нужно
            cache_results = []
            if auto_cache and unique_models:
                print(f"[ArenaAutoCacheSmart] Starting cache process for {len(unique_models)} models")
                cache_results = self._cache_models_with_progress(unique_models)
                print(f"[ArenaAutoCacheSmart] Cache process completed. Results: {len(cache_results)}")
            else:
                print("[ArenaAutoCacheSmart] Skipping cache process (auto_cache=False or no models)")
            
            # Формируем результат
            result = {
                "ok": True,
                "source": source_info,
                "workflow_analysis": {
                    "total_nodes": len(workflow_data.get("nodes", [])),
                    "models_found": len(unique_models),
                    "categories_checked": category_list,
                },
                "models": unique_models,
                "cache_results": cache_results if auto_cache else [],
            }
            
            # UI отчет
            cached_count = len([r for r in cache_results if r["status"] == "cached"])
            skipped_count = len([r for r in cache_results if r["status"].startswith("skipped")])
            error_count = len([r for r in cache_results if r["status"] in ["error", "not_found"]])
            
            if show_analysis:
                details = [
                    f"Source: {source_info}",
                    f"Models found: {len(unique_models)}",
                ]
                if auto_cache:
                    details.extend([
                        f"Cached: {cached_count}",
                        f"Skipped: {skipped_count}",
                        f"Errors: {error_count}",
                    ])
                else:
                    details.append("Analysis only (caching disabled)")
            else:
                details = [
                    f"Source: {source_info}",
                    f"Models: {len(unique_models)}",
                    f"Cached: {cached_count}" if auto_cache else "Analysis only",
                ]
            
            summary = {
                "ok": True,
                "ui": {
                    "headline": f"Smart Cache: {len(unique_models)} models processed",
                    "details": details,
                },
                "workflow_path": current_workflow_path,
            }
            
            return (
                json.dumps(result, ensure_ascii=False, indent=2),
                json.dumps(summary, ensure_ascii=False, indent=2),
                json.dumps(workflow_data, ensure_ascii=False, indent=2)
            )
            
        except Exception as e:
            # Добавляем диагностику для отладки
            debug_info = []
            if workflow_data is not None:
                debug_info.append(f"Workflow type: {type(workflow_data)}")
                if isinstance(workflow_data, dict):
                    debug_info.append(f"Keys: {list(workflow_data.keys())}")
                elif isinstance(workflow_data, list):
                    debug_info.append(f"List length: {len(workflow_data)}")
            
            return self._error_result("Error", [
                f"Error: {str(e)}",
                "Check workflow format and settings"
            ] + debug_info, current_workflow_path)
    
    def _error_result(self, headline: str, details: list, workflow_path: str = "No workflow loaded") -> tuple:
        """Создает результат с ошибкой."""
        summary = {
            "ok": False,
            "ui": {
                "headline": f"Smart Cache: {headline}",
                "details": details,
            },
            "workflow_path": workflow_path,
        }
        return ("{}", json.dumps(summary, ensure_ascii=False, indent=2), "{}")
    
    def _analyze_workflow(self, workflow_data: dict, categories: list) -> list:
        """Анализирует workflow и находит модели."""
        found_models = []
        nodes = workflow_data.get("nodes", [])
        print(f"[ArenaAutoCacheSmart] Analyzing {len(nodes)} nodes")
        
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                print(f"[ArenaAutoCacheSmart] Node {i}: skipping (not dict)")
                continue
            
            inputs = node.get("inputs", {})
            class_type = node.get("class_type", "") or node.get("type", "")
            print(f"[ArenaAutoCacheSmart] Node {i}: {class_type or 'Unknown'} with {len(inputs)} inputs")
            
            # Детальная диагностика ноды
            if not class_type:
                print(f"[ArenaAutoCacheSmart] Node {i} missing class_type/type. Available keys: {list(node.keys())}")
                # Пытаемся найти class_type в других полях
                for key, value in node.items():
                    if isinstance(value, str) and any(keyword in value.lower() for keyword in ['checkpoint', 'lora', 'controlnet', 'upscale', 'clip', 'ipadapter', 'insightface']):
                        print(f"[ArenaAutoCacheSmart] Found potential class_type in {key}: {value}")
                        class_type = value
                        break
            
            # Ищем модели в inputs и widgets_values
            print(f"[ArenaAutoCacheSmart] Node {i} inputs: {list(inputs.keys())}")
            
            # Проверяем widgets_values (ComfyUI Desktop формат)
            widgets_values = node.get("widgets_values", [])
            if widgets_values:
                print(f"[ArenaAutoCacheSmart] Node {i} widgets_values: {len(widgets_values)} items")
                for j, widget_value in enumerate(widgets_values):
                    # Обрабатываем строки
                    if isinstance(widget_value, str) and widget_value.strip():
                        print(f"[ArenaAutoCacheSmart] Node {i} widget {j}: {widget_value}")
                        # Нормализуем путь (заменяем обратные слеши)
                        normalized_value = widget_value.replace("\\", "/")
                        # Проверяем расширение файла
                        if any(normalized_value.lower().endswith(ext) for ext in [".safetensors", ".ckpt", ".pt", ".pth", ".bin"]):
                            print(f"[ArenaAutoCacheSmart] Found model file in widget: {normalized_value}")
                            # Определяем категорию
                            category = self._guess_category(class_type, f"widget_{j}", categories)
                            if category:
                                print(f"[ArenaAutoCacheSmart] Categorized as: {category}")
                                found_models.append({
                                    "category": category,
                                    "name": normalized_value,
                                    "node_type": class_type,
                                    "input_key": f"widget_{j}"
                                })
                            else:
                                print(f"[ArenaAutoCacheSmart] No category found for: {normalized_value} (class_type: {class_type})")
                        else:
                            print(f"[ArenaAutoCacheSmart] Not a model file: {widget_value}")
                    # Обрабатываем объекты (например, Power Lora Loader) - упрощенно
                    elif isinstance(widget_value, dict):
                        print(f"[ArenaAutoCacheSmart] Node {i} widget {j} (object): {type(widget_value)}")
                        # Ищем lora в объекте
                        if "lora" in widget_value and isinstance(widget_value["lora"], str):
                            lora_name = widget_value["lora"]
                            print(f"[ArenaAutoCacheSmart] Found lora in object: {lora_name}")
                            # Нормализуем путь
                            normalized_lora = lora_name.replace("\\", "/")
                            if any(normalized_lora.lower().endswith(ext) for ext in [".safetensors", ".ckpt", ".pt", ".pth", ".bin"]):
                                print(f"[ArenaAutoCacheSmart] Found lora model: {normalized_lora}")
                                category = self._guess_category(class_type, f"widget_{j}_lora", categories)
                                if category:
                                    print(f"[ArenaAutoCacheSmart] Categorized as: {category}")
                                    found_models.append({
                                        "category": category,
                                        "name": normalized_lora,
                                        "node_type": class_type,
                                        "input_key": f"widget_{j}_lora"
                                    })
                                else:
                                    print(f"[ArenaAutoCacheSmart] No category found for lora: {normalized_lora}")
                    else:
                        print(f"[ArenaAutoCacheSmart] Node {i} widget {j}: {type(widget_value)}")
            
            # Проверяем обычные inputs
            for key, value in inputs.items():
                if isinstance(value, str) and value.strip():
                    print(f"[ArenaAutoCacheSmart] Node {i} input '{key}': {value}")
                    # Проверяем расширение файла
                    if any(value.lower().endswith(ext) for ext in [".safetensors", ".ckpt", ".pt", ".pth", ".bin"]):
                        print(f"[ArenaAutoCacheSmart] Found model file: {value}")
                        # Определяем категорию
                        category = self._guess_category(class_type, key, categories)
                        if category:
                            print(f"[ArenaAutoCacheSmart] Categorized as: {category}")
                            found_models.append({
                                "category": category,
                                "name": value,
                                "node_type": class_type,
                                "input_key": key
                            })
                        else:
                            print(f"[ArenaAutoCacheSmart] No category found for: {value} (class_type: {class_type}, key: {key})")
                    else:
                        print(f"[ArenaAutoCacheSmart] Not a model file: {value}")
                else:
                    print(f"[ArenaAutoCacheSmart] Node {i} input '{key}': {type(value)} = {value}")
        
        return found_models
    
    def _cache_models(self, models: list) -> list:
        """Кеширует модели с применением фильтров."""
        results = []
        
        for i, model in enumerate(models):
            print(f"[ArenaAutoCacheSmart] Processing model {i+1}/{len(models)}: {model['name']}")
            try:
                from folder_paths import get_full_path
                src_path = get_full_path(model["category"], model["name"])
                print(f"[ArenaAutoCacheSmart] Source path: {src_path}")
                
                if src_path and Path(src_path).exists():
                    print(f"[ArenaAutoCacheSmart] File exists, checking filters")
                    # Проверяем фильтры
                    settings = get_settings()
                    if _should_skip_by_size(Path(src_path), settings):
                        print(f"[ArenaAutoCacheSmart] Skipping due to size filter")
                        results.append({
                            "model": model["name"],
                            "status": "skipped_size",
                            "reason": f"Size < {settings.min_size_gb}GB"
                        })
                        continue
                    
                    if _should_skip_hardcoded_path(Path(src_path), settings):
                        print(f"[ArenaAutoCacheSmart] Skipping due to hardcoded path filter")
                        results.append({
                            "model": model["name"],
                            "status": "skipped_hardcoded",
                            "reason": "Hardcoded path"
                        })
                        continue
                    
                    # Копируем в кеш
                    cache_path = _ensure_category_root(model["category"]) / model["name"]
                    print(f"[ArenaAutoCacheSmart] Cache path: {cache_path}")
                    
                    if not cache_path.exists():
                        print(f"[ArenaAutoCacheSmart] Starting copy process")
                        src_path = get_full_path(model["category"], model["name"])
                        _copy_into_cache_lru(Path(src_path), cache_path, model["category"])
                        print(f"[ArenaAutoCacheSmart] Copy completed")
                        results.append({
                            "model": model["name"],
                            "status": "cached",
                            "category": model["category"]
                        })
                    else:
                        print(f"[ArenaAutoCacheSmart] Already cached")
                        results.append({
                            "model": model["name"],
                            "status": "already_cached",
                            "category": model["category"]
                        })
                else:
                    print(f"[ArenaAutoCacheSmart] File not found")
                    results.append({
                        "model": model["name"],
                        "status": "not_found",
                        "reason": "File not found"
                    })
            except Exception as e:
                print(f"[ArenaAutoCacheSmart] Error processing model: {str(e)}")
                results.append({
                    "model": model["name"],
                    "status": "error",
                    "reason": str(e)
                })
        
        return results
    
    def _cache_models_with_progress(self, models: list) -> list:
        """Кеширует модели с индикатором прогресса."""
        results = []
        total = len(models)
        
        print(f"🔄 Кеширование {total} моделей...")
        
        for i, model in enumerate(models, 1):
            try:
                print(f"📁 [{i}/{total}] Кеширую {model['name']} ({model['category']})...")
                
                from folder_paths import get_full_path, folder_names_and_paths
                src_path = get_full_path(model["category"], model["name"])
                print(f"🔍 [{i}/{total}] Ищу модель: {model['name']} в категории: {model['category']}")
                print(f"🔍 [{i}/{total}] Полный путь: {src_path}")
                
                # Показываем доступные пути для категории
                if model["category"] in folder_names_and_paths:
                    paths = folder_names_and_paths[model["category"]]
                    print(f"🔍 [{i}/{total}] Доступные пути для {model['category']}: {paths}")
                
                # Получаем размер файла для отображения
                file_size_mb = 0
                if src_path and Path(src_path).exists():
                    try:
                        file_size_bytes = Path(src_path).stat().st_size
                        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
                        print(f"📏 [{i}/{total}] Размер файла: {file_size_mb} MB")
                    except Exception as e:
                        print(f"⚠️ [{i}/{total}] Не удалось получить размер файла: {e}")
                
                if src_path and Path(src_path).exists():
                    # Проверяем фильтры
                    settings = get_settings()
                    if _should_skip_by_size(Path(src_path), settings):
                        result = {
                            "model": model["name"],
                            "status": "skipped_size",
                            "reason": f"Size < {settings.min_size_gb}GB",
                            "size_mb": file_size_mb
                        }
                        results.append(result)
                        print(f"⏭️  [{i}/{total}] Пропущено по размеру: {model['name']}")
                        continue
                    
                    if _should_skip_hardcoded_path(Path(src_path), settings):
                        result = {
                            "model": model["name"],
                            "status": "skipped_hardcoded",
                            "reason": "Hardcoded path",
                            "size_mb": file_size_mb
                        }
                        results.append(result)
                        print(f"⏭️  [{i}/{total}] Пропущено по пути: {model['name']}")
                        continue
                    
                    # Копируем в кеш
                    cache_path = _ensure_category_root(model["category"]) / model["name"]
                    
                    if not cache_path.exists():
                        print(f"📋 [{i}/{total}] Копирую {model['name']}...")
                        print(f"🔄 [{i}/{total}] Прогресс: 0% - Начинаю копирование...")
                        _copy_into_cache_lru(Path(src_path), cache_path, model["category"])
                        print(f"✅ [{i}/{total}] Прогресс: 100% - Копирование завершено!")
                        result = {
                            "model": model["name"],
                            "status": "cached",
                            "category": model["category"],
                            "size_mb": file_size_mb
                        }
                        results.append(result)
                        print(f"✅ [{i}/{total}] Скопировано: {model['name']}")
                    else:
                        result = {
                            "model": model["name"],
                            "status": "skipped_exists",
                            "reason": "Already cached",
                            "size_mb": file_size_mb
                        }
                        results.append(result)
                        print(f"⏭️  [{i}/{total}] Уже в кеше: {model['name']}")
                else:
                    result = {
                        "model": model["name"],
                        "status": "not_found",
                        "reason": "File not found"
                    }
                    results.append(result)
                    print(f"❌ [{i}/{total}] Файл не найден: {model['name']}")
                    
            except Exception as e:
                result = {
                    "model": model["name"],
                    "status": "error",
                    "reason": str(e)
                }
                results.append(result)
                print(f"❌ [{i}/{total}] Ошибка: {model['name']} - {str(e)}")
        
        cached_count = len([r for r in results if r["status"] == "cached"])
        print(f"🎯 Кеширование завершено: {cached_count}/{total} моделей скопировано")
        
        return results
    
    def _guess_category(self, class_type: str, input_key: str, categories: list) -> str | None:
        """Определяет категорию модели по типу ноды и ключу."""
        class_type_lower = class_type.lower()
        input_key_lower = input_key.lower()
        
        # Checkpoint models
        if any(keyword in class_type_lower for keyword in ["checkpoint", "model"]):
            if any(keyword in input_key_lower for keyword in ["ckpt", "model", "checkpoint"]):
                return "checkpoints" if "checkpoints" in categories else None
        
        # LoRA models
        if "lora" in class_type_lower or "lora" in input_key_lower:
            return "loras" if "loras" in categories else None
        
        # ControlNet models
        if "controlnet" in class_type_lower or "controlnet" in input_key_lower:
            return "controlnet" if "controlnet" in categories else None
        
        # Upscale models
        if any(keyword in class_type_lower for keyword in ["upscale", "upscaler"]):
            return "upscale_models" if "upscale_models" in categories else None
        
        # CLIP Vision models
        if "clip" in class_type_lower and "vision" in class_type_lower:
            return "clip_vision" if "clip_vision" in categories else None
        
        # IP-Adapter models
        if "ipadapter" in class_type_lower:
            return "ipadapter" if "ipadapter" in categories else None
        
        # InsightFace models
        if "insightface" in class_type_lower:
            return "insightface" if "insightface" in categories else None
        
        # Generic fallback
        if any(keyword in input_key_lower for keyword in ["model", "ckpt", "lora", "controlnet"]):
            for category in categories:
                if category in input_key_lower:
                    return category
        
        return None
    
    def _analyze_current_canvas(self) -> list:
        """Анализирует текущий холст ComfyUI и находит ноды с моделями."""
        found_models = []
        
        try:
            print("[ArenaAutoCacheSmart] Analyzing current canvas...")
            
            # Метод 1: Через PromptServer и очередь
            try:
                from server import PromptServer
                if hasattr(PromptServer, 'instance') and PromptServer.instance:
                    prompt_server = PromptServer.instance
                    print("[ArenaAutoCacheSmart] Accessing PromptServer...")
                    
                    # Получаем текущую очередь
                    if hasattr(prompt_server, 'prompt_queue'):
                        queue = prompt_server.prompt_queue
                        print("[ArenaAutoCacheSmart] Accessing prompt queue...")
                        
                        # Получаем текущую очередь
                        if hasattr(queue, 'get_current_queue'):
                            current_queue = queue.get_current_queue()
                            print(f"[ArenaAutoCacheSmart] Current queue length: {len(current_queue) if current_queue else 0}")
                            
                            if current_queue:
                                for i, item in enumerate(current_queue):
                                    if isinstance(item, dict) and 'prompt' in item:
                                        prompt = item['prompt']
                                        print(f"[ArenaAutoCacheSmart] Analyzing queue item {i}: {type(prompt)}")
                                        
                                        if isinstance(prompt, dict) and 'nodes' in prompt:
                                            models = self._extract_models_from_workflow(prompt)
                                            found_models.extend(models)
                                            print(f"[ArenaAutoCacheSmart] Found {len(models)} models in queue item {i}")
                        
                        # Получаем текущий выполняемый prompt
                        if hasattr(queue, 'currently_running') and queue.currently_running:
                            running = queue.currently_running
                            print(f"[ArenaAutoCacheSmart] Currently running: {type(running)}")
                            
                            if isinstance(running, dict) and 'prompt' in running:
                                prompt = running['prompt']
                                if isinstance(prompt, dict) and 'nodes' in prompt:
                                    models = self._extract_models_from_workflow(prompt)
                                    found_models.extend(models)
                                    print(f"[ArenaAutoCacheSmart] Found {len(models)} models in currently running")
            except Exception as e:
                print(f"[ArenaAutoCacheSmart] Error accessing PromptServer: {e}")
            
            # Метод 2: Через NODE_CLASS_MAPPINGS - ищем зарегистрированные ноды
            try:
                print("[ArenaAutoCacheSmart] Searching registered node classes...")
                import sys
                
                # Ищем модули с NODE_CLASS_MAPPINGS
                for module_name, module in sys.modules.items():
                    if module and hasattr(module, 'NODE_CLASS_MAPPINGS'):
                        mappings = getattr(module, 'NODE_CLASS_MAPPINGS', {})
                        try:
                            mappings_len = len(mappings) if hasattr(mappings, '__len__') else 'unknown'
                            print(f"[ArenaAutoCacheSmart] Found NODE_CLASS_MAPPINGS in {module_name}: {mappings_len} nodes")
                        except:
                            print(f"[ArenaAutoCacheSmart] Found NODE_CLASS_MAPPINGS in {module_name}: type {type(mappings)}")
                        
                        # Проверяем, что mappings поддерживает итерацию
                        if hasattr(mappings, 'items'):
                            for node_name, node_class in mappings.items():
                                if hasattr(node_class, 'class_type'):
                                    class_type = getattr(node_class, 'class_type', '')
                                    if isinstance(class_type, str) and class_type.strip():
                                        if any(keyword in class_type.lower() for keyword in ['checkpoint', 'lora', 'controlnet', 'upscale', 'clip', 'ipadapter', 'insightface']):
                                            print(f"[ArenaAutoCacheSmart] Found model node class: {class_type} ({node_name})")
                                            
                                            # Пытаемся создать экземпляр и получить inputs
                                            try:
                                                if hasattr(node_class, 'INPUT_TYPES'):
                                                    input_types = node_class.INPUT_TYPES()
                                                    if isinstance(input_types, dict) and 'required' in input_types:
                                                        required_inputs = input_types['required']
                                                        for input_name, input_config in required_inputs.items():
                                                            if isinstance(input_config, tuple) and len(input_config) > 0:
                                                                input_type = input_config[0]
                                                                if isinstance(input_type, str) and any(keyword in input_type.lower() for keyword in ['model', 'ckpt', 'lora', 'controlnet']):
                                                                    print(f"[ArenaAutoCacheSmart] Found model input: {input_name} in {class_type}")
                                            except Exception as e:
                                                print(f"[ArenaAutoCacheSmart] Error analyzing {class_type}: {e}")
            except Exception as e:
                print(f"[ArenaAutoCacheSmart] Error searching node classes: {e}")
            
            # Метод 3: Через folder_paths - ищем недавно использованные модели
            try:
                print("[ArenaAutoCacheSmart] Checking recently used models...")
                
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
                        print("[ArenaAutoCacheSmart] Cannot import folder_paths, skipping recent models check")
                        model_folders = {}
                
                if model_folders:
                    print(f"[ArenaAutoCacheSmart] Model folders: {list(model_folders.keys())}")
                else:
                    print("[ArenaAutoCacheSmart] No model folders found")
                
                # Ищем недавно модифицированные файлы в папках моделей
                for category, folder_path in model_folders.items():
                    if folder_path and Path(folder_path).exists():
                        try:
                            # Ищем файлы моделей, модифицированные в последние 5 минут
                            import time
                            current_time = time.time()
                            recent_files = []
                            
                            for file_path in Path(folder_path).glob("*"):
                                if file_path.is_file() and any(file_path.suffix.lower() in [".safetensors", ".ckpt", ".pt", ".pth", ".bin"]):
                                    if current_time - file_path.stat().st_mtime < 300:  # 5 минут
                                        recent_files.append(file_path)
                            
                            if recent_files:
                                print(f"[ArenaAutoCacheSmart] Found {len(recent_files)} recently used models in {category}")
                                for file_path in recent_files:
                                    found_models.append({
                                        "category": category,
                                        "name": file_path.name,
                                        "node_type": "recent_file",
                                        "input_key": "file",
                                        "source": "recent_usage"
                                    })
                        except Exception as e:
                            print(f"[ArenaAutoCacheSmart] Error checking {category}: {e}")
            except Exception as e:
                print(f"[ArenaAutoCacheSmart] Error checking recent models: {e}")
            
            # Удаляем дубликаты
            unique_models = []
            seen = set()
            for model in found_models:
                key = (model["category"], model["name"])
                if key not in seen:
                    seen.add(key)
                    unique_models.append(model)
            
            print(f"[ArenaAutoCacheSmart] Total unique models found: {len(unique_models)}")
            return unique_models
            
        except Exception as e:
            print(f"[ArenaAutoCacheSmart] Error analyzing canvas: {e}")
            return []
    
    def _convert_json_models_to_arena_format(self, json_models: list[dict]) -> list[object]:
        """Convert JSON model format to Arena format."""
        arena_models = []
        
        for model in json_models:
            arena_model = {
                'name': model['name'],
                'class_type': model['class_type'],
                'category': model['category'],
                'directory': model['directory'],
                'url': model['url'],
                'node_id': model['node_id']
            }
            arena_models.append(arena_model)
        
        print(f"[ArenaAutoCacheSmart] Converted {len(arena_models)} JSON models to Arena format")
        return arena_models

    def _extract_models_from_workflow(self, workflow: dict) -> list:
        """Извлекает модели из workflow."""
        models = []
        
        print(f"[ArenaAutoCacheSmart] _extract_models_from_workflow called with workflow type: {type(workflow)}")
        
        if not isinstance(workflow, dict):
            print(f"[ArenaAutoCacheSmart] Workflow is not a dict: {type(workflow)}")
            return models
            
        if 'nodes' not in workflow:
            print(f"[ArenaAutoCacheSmart] No 'nodes' key in workflow. Keys: {list(workflow.keys())}")
            return models
        
        nodes = workflow.get('nodes', [])
        print(f"[ArenaAutoCacheSmart] Processing {len(nodes)} nodes from workflow")
        
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                print(f"[ArenaAutoCacheSmart] Node {i} is not a dict: {type(node)}")
                continue
            
            inputs = node.get('inputs', {})
            class_type = node.get('class_type', '')
            print(f"[ArenaAutoCacheSmart] Node {i}: {class_type} with {len(inputs)} inputs")
            
            for key, value in inputs.items():
                if isinstance(value, str) and value.strip():
                    if any(value.lower().endswith(ext) for ext in [".safetensors", ".ckpt", ".pt", ".pth", ".bin"]):
                        category = self._guess_category(class_type, key, ["checkpoints", "loras", "controlnet", "upscale_models", "clip_vision", "ipadapter", "insightface"])
                        if category:
                            print(f"[ArenaAutoCacheSmart] Found model: {value} in category {category} (node: {class_type})")
                            models.append({
                                "category": category,
                                "name": value,
                                "node_type": class_type,
                                "input_key": key,
                                "source": "workflow"
                            })
        
        print(f"[ArenaAutoCacheSmart] Extracted {len(models)} models from workflow")
        return models


# Версия узлов для тестирования
# v2.11 - Исправлена поддержка разных форматов workflow (class_type vs type)
#         Добавлена поддержка widgets_values для извлечения моделей
#         Теперь работает с реальными workflow ComfyUI
# v2.10 - Добавлена отладка class_type и inputs для диагностики узлов
#         Теперь показываются все inputs каждого узла для понимания структуры
#         Поможет найти правильные ключи для извлечения моделей
# v2.9 - Добавлен индикатор прогресса кеширования с эмодзи и подробными логами
#        Добавлена функция _cache_models_with_progress для визуального отслеживания процесса
#        Расширен список поддерживаемых узлов загрузки моделей
#        Теперь пользователь видит процесс кеширования в реальном времени
# v2.8 - Исправлена функция _extract_models_from_workflow_json для работы с ComfyUI форматом
#        Теперь ищет модели в inputs вместо widgets_values
#        Добавлена подробная отладочная информация для диагностики извлечения моделей
#        Функция теперь должна корректно находить модели в workflow
# v2.7 - Исправлена проблема с кешированием моделей - теперь используется правильный метод анализа
#        ArenaAutoCacheSmart теперь использует _extract_models_from_workflow_json для извлечения моделей
#        Добавлен fallback на старый метод при отсутствии моделей в JSON анализе
#        Модели теперь должны корректно кешироваться
# v2.6 - Исправлена проблема с "No workflow loaded" - теперь показывается реальный путь
#        Исправлена Alert ошибка "Invalid workflow against zod schema" - добавлена коррекция links
#        ArenaAutoCacheSmart теперь корректно обрабатывает неправильные links в workflow
#        Добавлена автоматическая коррекция формата links для совместимости с ComfyUI
# v2.5 - Исправлена ошибка 'list' object has no attribute 'keys' при работе с ArenaAutoCacheAnalyze
#        Добавлена специальная обработка данных от ArenaAutoCacheAnalyze в ArenaAutoCacheSmart
#        ArenaAutoCacheSmart теперь корректно обрабатывает список моделей от ArenaAutoCacheAnalyze
#        Добавлена конвертация форматов между ArenaAutoCacheAnalyze и ArenaAutoCacheSmart
# v2.4 - Добавлено отображение пути к workflow в интерфейсе ноды
#        Добавлено поле workflow_path_display для показа источника workflow
#        Обновлен summary с информацией о workflow_path
#        Пользователь теперь видит откуда читается workflow (history API, файл, JSON)
# v2.4 - Исправлена проблема с определением активного workflow в ArenaAutoCacheSmart
#        Убрана зависимость от истории ComfyUI как fallback для определения моделей
#        ArenaAutoCacheSmart теперь анализирует текущий canvas вместо последнего выполненного workflow
#        Добавлены дополнительные методы получения canvas workflow через JavaScript API
# v2.3 - Добавлен анализ JSON workflow для извлечения моделей из нод загрузки
#        Добавлена функция _extract_models_from_workflow_json для парсинга JSON структуры
#        Добавлена функция _get_model_category для определения категорий моделей
#        ArenaAutoCacheSmart теперь использует новый метод анализа JSON workflow
# v2.2 - Реализована правильная стратегия кеширования: работа с последним выполненным workflow
#        Добавлена функция _load_last_executed_workflow через ComfyUI history API
#        ArenaAutoCacheSmart теперь работает с выполняющимися workflow, а не с canvas
#        Единственный рабочий путь: Запуск workflow → кеширование в процессе → следующий запуск из кеша
# v2.1 - Добавлена улучшенная функция _load_active_workflow с новыми методами получения canvas workflow
#        Добавлена подробная отладочная информация для WebSocket и модулей ComfyUI
#        Основные узлы теперь имеют версии в названиях для удобства тестирования
#        Обратная совместимость: старые названия узлов остаются для существующих workflow
ARENA_NODES_VERSION = "v2.19"

NODE_CLASS_MAPPINGS.update(
    {
        # Основные узлы с версиями для тестирования (новые)
        f"ArenaAutoCacheSmart {ARENA_NODES_VERSION}": ArenaAutoCacheSmart,
        f"ArenaAutoCacheAnalyze {ARENA_NODES_VERSION}": ArenaAutoCacheAnalyze,
        f"ArenaGetActiveWorkflow {ARENA_NODES_VERSION}": ArenaGetActiveWorkflow,
        f"ArenaAutoCacheRefreshWorkflow {ARENA_NODES_VERSION}": ArenaAutoCacheRefreshWorkflow,
        
        # Обратная совместимость - старые названия для существующих workflow
        "ArenaAutoCacheSmart": ArenaAutoCacheSmart,
        "ArenaAutoCacheAnalyze": ArenaAutoCacheAnalyze,
        "ArenaGetActiveWorkflow": ArenaGetActiveWorkflow,
        "ArenaAutoCacheRefreshWorkflow": ArenaAutoCacheRefreshWorkflow,
        
        # Остальные узлы без версий (стабильные)
        "ArenaAutoCacheAudit": ArenaAutoCacheAudit,
        "ArenaAutoCacheConfig": ArenaAutoCacheConfig,
        "ArenaAutoCacheCopyStatus": ArenaAutoCacheCopyStatus,
        "ArenaAutoCacheDashboard": ArenaAutoCacheDashboard,
        "ArenaAutoCacheOps": ArenaAutoCacheOps,
        "ArenaAutoCachePrewarm": ArenaAutoCachePrewarm,
        "ArenaAutoCachePrewarmFromFile": ArenaAutoCachePrewarmFromFile,
        "ArenaAutoCacheStats": ArenaAutoCacheStats,
        "ArenaAutoCacheStatsEx": ArenaAutoCacheStatsEx,
        "ArenaAutoCacheTrim": ArenaAutoCacheTrim,
        "ArenaAutoCacheWarmup": ArenaAutoCacheWarmup,
        "ArenaAutoCacheManager": ArenaAutoCacheManager,
    }
)

NODE_DISPLAY_NAME_MAPPINGS.update(
    {
        # Основные узлы с версиями для тестирования (новые)
        f"ArenaAutoCacheSmart {ARENA_NODES_VERSION}": f"🅰️ Arena AutoCache: Smart {ARENA_NODES_VERSION}",
        f"ArenaAutoCacheAnalyze {ARENA_NODES_VERSION}": f"{t('node.analyze')} {ARENA_NODES_VERSION}",
        f"ArenaGetActiveWorkflow {ARENA_NODES_VERSION}": f"{t('node.get_workflow')} {ARENA_NODES_VERSION}",
        f"ArenaAutoCacheRefreshWorkflow {ARENA_NODES_VERSION}": f"🅰️ Arena AutoCache: Refresh Workflow {ARENA_NODES_VERSION}",
        
        # Обратная совместимость - старые названия для существующих workflow
        "ArenaAutoCacheSmart": "🅰️ Arena AutoCache: Smart",
        "ArenaAutoCacheAnalyze": t("node.analyze"),
        "ArenaGetActiveWorkflow": t("node.get_workflow"),
        "ArenaAutoCacheRefreshWorkflow": "🅰️ Arena AutoCache: Refresh Workflow",
        
        # Остальные узлы без версий (стабильные)
        "ArenaAutoCacheAudit": t("node.audit"),
        "ArenaAutoCacheConfig": t("node.config"),
        "ArenaAutoCacheCopyStatus": t("node.copy_status"),
        "ArenaAutoCacheDashboard": t("node.dashboard"),
        "ArenaAutoCacheOps": t("node.ops"),
        "ArenaAutoCachePrewarm": "🅰️ Arena AutoCache: Prewarm",
        "ArenaAutoCachePrewarmFromFile": "🅰️ Arena AutoCache: Prewarm From File",
        "ArenaAutoCacheStats": t("node.stats"),
        "ArenaAutoCacheStatsEx": t("node.statsex"),
        "ArenaAutoCacheTrim": t("node.trim"),
        "ArenaAutoCacheWarmup": t("node.warmup"),
        "ArenaAutoCacheManager": t("node.manager"),
    }
)
