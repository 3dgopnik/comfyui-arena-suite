# EN identifiers; RU comments for clarity.
import json
import os
import shutil
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType


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

_folder_paths_module: ModuleType | None = None
_orig_get_folder_paths: Callable[[str], list[str] | tuple[str, ...]] | None = None
_orig_get_full_path: Callable[[str, str], str | None] | None = None
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

# RU: Глобальное состояние для отслеживания первого запуска
_session_warmup_completed = False
_session_models_analyzed = set()

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

        def patched_get_full_path(folder_type: str, filename: str) -> str | None:
            """RU: Патчированная версия get_full_path с проверкой кеша."""
            global _session_hits, _session_misses

            if not _settings.enable:
                return _orig_get_full_path(folder_type, filename) if _orig_get_full_path else None

            # Сначала проверяем кеш
            cache_path = _settings.root / folder_type / filename
            if cache_path.exists():
                if _settings.verbose:
                    print(f"[ArenaAutoCache] Cache hit: {filename}")
                _session_hits += 1
                return str(cache_path)

            # Если нет в кеше, используем оригинальную функцию
            original_path = _orig_get_full_path(folder_type, filename) if _orig_get_full_path else None
            if original_path and Path(original_path).exists():
                if _settings.verbose:
                    print(f"[ArenaAutoCache] Cache miss: {filename}")
                _session_misses += 1

                # Кешируем файл в фоне
                _schedule_cache_copy(folder_type, filename, original_path)

            return original_path

        # Применяем патчи
        folder_paths.get_folder_paths = patched_get_folder_paths
        folder_paths.get_full_path = patched_get_full_path

        _folder_paths_patched = True
        print("[ArenaAutoCache] Applied folder_paths patch")

    except Exception as e:
        print(f"[ArenaAutoCache] Failed to apply folder_paths patch: {e}")

def _schedule_cache_copy(folder_type: str, filename: str, source_path: str):
    """RU: Планирует копирование файла в кеш."""
    global _copy_status

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
            _copy_status["completed_jobs"] += 1
            _copy_status["current_file"] = filename
            _copy_status["last_update"] = _now()

    except Exception as e:
        print(f"[ArenaAutoCache] Error caching {filename}: {e}")
        _copy_status["failed_jobs"] += 1

def _analyze_workflow_for_models(workflow_data) -> list[dict]:
    """RU: Анализирует workflow для поиска всех используемых моделей."""
    found_models = []

    # RU: Словарь типов нод, которые используют модели
    MODEL_NODE_TYPES = {
        # Checkpoint models
        "CheckpointLoaderSimple": ["ckpt_name"],
        "CheckpointLoader": ["ckpt_name"],
        "UNETLoader": ["unet_name"],

        # VAE models
        "VAELoader": ["vae_name"],
        "VAEDecode": ["vae_name"],
        "VAEEncode": ["vae_name"],

        # LoRA models
        "LoraLoader": ["lora_name"],

        # ControlNet models
        "ControlNetLoader": ["control_net_name"],
        "ControlNetApply": ["control_net"],

        # CLIP models
        "CLIPLoader": ["clip_name"],
        "CLIPTextEncode": ["clip"],

        # Upscale models
        "UpscaleModelLoader": ["model_name"],
        "ImageUpscaleWithModel": ["upscale_model"],

        # Textual Inversion embeddings
        "CLIPTextEncode": ["text"],

        # Hypernetworks
        "HypernetworkLoader": ["hypernetwork_name"],

        # IP-Adapter models
        "IPAdapterLoader": ["ipadapter_file"],
        "IPAdapterApply": ["ipadapter"],

        # GLIGEN models
        "GLIGENLoader": ["gligen_name"],

        # AnimateDiff models
        "AnimateDiffLoader": ["model_name"],

        # InsightFace models
        "InsightFaceLoader": ["provider", "model_name"],

        # Face restoration models
        "FaceRestoreWithModel": ["face_model"],

        # Style models
        "StyleModelLoader": ["style_model_name"],

        # T2I-Adapter models
        "T2IAdapterLoader": ["t2i_adapter_name"],
    }

    try:
        print(f"[ArenaAutoCache] Analyzing workflow data type: {type(workflow_data)}")

        # RU: Проверяем различные форматы данных
        nodes = None

        if isinstance(workflow_data, dict):
            if "nodes" in workflow_data:
                nodes = workflow_data.get("nodes", {})
                if isinstance(nodes, dict):
                    print(f"[ArenaAutoCache] Found nodes in dict: {len(nodes)} nodes")
                elif isinstance(nodes, list):
                    print(f"[ArenaAutoCache] Found nodes in list: {len(nodes)} nodes")
                else:
                    print(f"[ArenaAutoCache] Nodes is not dict/list: {type(nodes)}")
                    # RU: Пробуем обработать модуль как словарь
                    if hasattr(nodes, '__dict__'):
                        print("[ArenaAutoCache] Trying to convert module to dict...")
                        try:
                            # RU: Пробуем получить атрибуты модуля
                            module_dict = {}
                            for attr_name in dir(nodes):
                                if not attr_name.startswith('_'):
                                    attr_value = getattr(nodes, attr_name)
                                    if not callable(attr_value):
                                        module_dict[attr_name] = attr_value

                            if module_dict:
                                print(f"[ArenaAutoCache] Converted module to dict with {len(module_dict)} attributes")
                                # RU: Ищем nodes в атрибутах
                                if 'nodes' in module_dict:
                                    nodes = module_dict['nodes']
                                    if isinstance(nodes, dict) or isinstance(nodes, list):
                                        print(f"[ArenaAutoCache] Found nodes in module dict: {len(nodes)} nodes")
                                    else:
                                        print(f"[ArenaAutoCache] Module dict nodes is not dict/list: {type(nodes)}")
                                        return found_models
                                else:
                                    print("[ArenaAutoCache] No 'nodes' in module dict")
                                    return found_models
                            else:
                                print("[ArenaAutoCache] Module has no accessible attributes")
                                return found_models
                        except Exception as e:
                            print(f"[ArenaAutoCache] Error converting module to dict: {e}")
                            return found_models
                    else:
                        return found_models
            else:
                print(f"[ArenaAutoCache] No 'nodes' key in dict, keys: {list(workflow_data.keys())}")
                return found_models
        elif hasattr(workflow_data, 'nodes'):
            nodes = workflow_data.nodes
            # RU: Проверяем, что nodes не является модулем
            if hasattr(nodes, '__dict__') and not isinstance(nodes, (dict, list)):
                print("[ArenaAutoCache] Nodes is a module/object, trying to extract data...")
                try:
                    # RU: Пробуем получить данные из модуля
                    if hasattr(nodes, 'nodes'):
                        nodes = nodes.nodes
                        if isinstance(nodes, dict) or isinstance(nodes, list):
                            print(f"[ArenaAutoCache] Extracted nodes from module: {len(nodes)} nodes")
                        else:
                            print(f"[ArenaAutoCache] Extracted nodes is not dict/list: {type(nodes)}")
                            return found_models
                    else:
                        print("[ArenaAutoCache] Module has no 'nodes' attribute")
                        return found_models
                except Exception as e:
                    print(f"[ArenaAutoCache] Error extracting from module: {e}")
                    return found_models
            else:
                if isinstance(nodes, dict) or isinstance(nodes, list):
                    print(f"[ArenaAutoCache] Found nodes attribute: {len(nodes)} nodes")
                else:
                    print(f"[ArenaAutoCache] Nodes attribute is not dict/list: {type(nodes)}")
                    return found_models
        elif hasattr(workflow_data, '__dict__'):
            # RU: Пробуем получить данные из атрибутов объекта
            print("[ArenaAutoCache] Converting object to dict...")
            try:
                # RU: Сначала пробуем получить nodes напрямую
                if hasattr(workflow_data, 'nodes'):
                    nodes = workflow_data.nodes
                    # RU: Проверяем, что nodes не является модулем
                    if hasattr(nodes, '__dict__') and not isinstance(nodes, (dict, list)):
                        print("[ArenaAutoCache] Nodes is a module/object, trying to extract data...")
                        try:
                            if hasattr(nodes, 'nodes'):
                                nodes = nodes.nodes
                                print(f"[ArenaAutoCache] Extracted nodes from module: {len(nodes)} nodes")
                            else:
                                print("[ArenaAutoCache] Module has no 'nodes' attribute")
                                return found_models
                        except Exception as e:
                            print(f"[ArenaAutoCache] Error extracting from module: {e}")
                            return found_models
                    else:
                        print(f"[ArenaAutoCache] Found nodes attribute directly: {len(nodes)} nodes")
                else:
                    # RU: Пробуем сериализовать объект
                    import json
                    workflow_dict = json.loads(json.dumps(workflow_data, default=str))
                    if isinstance(workflow_dict, dict) and "nodes" in workflow_dict:
                        nodes = workflow_dict["nodes"]
                        print(f"[ArenaAutoCache] Converted object to dict with {len(nodes)} nodes")
                    else:
                        print("[ArenaAutoCache] No nodes found in converted dict")
                        return found_models
            except Exception as e:
                print(f"[ArenaAutoCache] Error converting object: {e}")
                return found_models
        else:
            print(f"[ArenaAutoCache] Unsupported workflow data type: {type(workflow_data)}")
            return found_models

        if not nodes:
            print("[ArenaAutoCache] No nodes found in workflow data")
            return found_models

        # RU: Обрабатываем как список, так и словарь
        if isinstance(nodes, list):
            print(f"[ArenaAutoCache] Converting list of {len(nodes)} nodes to dict...")
            nodes_dict = {}
            for i, node in enumerate(nodes):
                if isinstance(node, dict) and 'id' in node:
                    nodes_dict[str(node['id'])] = node
                else:
                    nodes_dict[str(i)] = node
            nodes = nodes_dict
            print(f"[ArenaAutoCache] Converted to dict with {len(nodes)} nodes")
        elif not isinstance(nodes, dict):
            print(f"[ArenaAutoCache] Nodes is not a dict or list: {type(nodes)}")
            return found_models

        print(f"[ArenaAutoCache] Processing {len(nodes)} nodes...")

        for node_id, node_data in nodes.items():
            if not isinstance(node_data, dict):
                print(f"[ArenaAutoCache] Node {node_id} is not a dict: {type(node_data)}")
                continue

            class_type = node_data.get("class_type", "")
            inputs = node_data.get("inputs", {})

            print(f"[ArenaAutoCache] Processing node {node_id}: {class_type}")
            print(f"[ArenaAutoCache] Full node data keys: {list(node_data.keys())}")

            # RU: Если class_type пустой, пробуем другие поля
            if not class_type:
                class_type = node_data.get("type", "")
                print(f"[ArenaAutoCache] Using 'type' field: {class_type}")

            if not class_type:
                print(f"[ArenaAutoCache] No class_type found in node {node_id}")
                continue

            # RU: Получаем значения из widgets_values
            widgets_values = node_data.get("widgets_values", [])
            print(f"[ArenaAutoCache] Widgets values: {widgets_values}")

            # RU: Создаем словарь значений для полей
            field_values = {}
            if isinstance(inputs, list):
                print(f"[ArenaAutoCache] Node inputs is a list with {len(inputs)} items")
                # RU: Сопоставляем inputs с widgets_values
                # RU: Сначала находим поля, которые не связаны (link: null)
                unlinked_inputs = []
                for input_item in inputs:
                    if isinstance(input_item, dict) and input_item.get('link') is None:
                        unlinked_inputs.append(input_item)

                print(f"[ArenaAutoCache] Found {len(unlinked_inputs)} unlinked inputs")

                # RU: Сопоставляем unlinked inputs с widgets_values
                for i, input_item in enumerate(unlinked_inputs):
                    if i < len(widgets_values):
                        field_name = input_item['name']
                        try:
                            field_values[field_name] = widgets_values[i]
                            print(f"[ArenaAutoCache] Mapped {field_name} = {widgets_values[i]}")
                        except (KeyError, IndexError, TypeError) as e:
                            print(f"[ArenaAutoCache] Error mapping {field_name}: {e}")
                            # RU: Пробуем получить значение по-другому
                            if isinstance(widgets_values, dict) and field_name in widgets_values:
                                field_values[field_name] = widgets_values[field_name]
                                print(f"[ArenaAutoCache] Mapped {field_name} from dict = {widgets_values[field_name]}")
                            else:
                                print(f"[ArenaAutoCache] Skipping {field_name} - no valid value found")
                    else:
                        break
                print(f"[ArenaAutoCache] Field values: {field_values}")
            elif isinstance(inputs, dict):
                print(f"[ArenaAutoCache] Node inputs: {list(inputs.keys())}")
                field_values = inputs
            else:
                print(f"[ArenaAutoCache] Node inputs type: {type(inputs)}")
                continue

            if class_type in MODEL_NODE_TYPES:
                model_fields = MODEL_NODE_TYPES[class_type]
                print(f"[ArenaAutoCache] Looking for fields: {model_fields}")

                for field in model_fields:
                    if field in field_values:
                        model_name = field_values[field]
                        if isinstance(model_name, str) and model_name.strip():
                            # Определяем категорию модели по типу ноды
                            category = _get_model_category(class_type, field)

                            found_models.append({
                                "name": model_name,
                                "category": category,
                                "node_id": node_id,
                                "node_type": class_type,
                                "field": field,
                                "source": "workflow_analysis"
                            })
                            print(f"[ArenaAutoCache] Found model: {model_name} ({category}) in node {node_id}")
                        else:
                            print(f"[ArenaAutoCache] Field {field} value is not a string: {type(model_name)} = {model_name}")
                    else:
                        print(f"[ArenaAutoCache] Field {field} not found in field_values")
            else:
                print(f"[ArenaAutoCache] Node type {class_type} not in MODEL_NODE_TYPES")

        print(f"[ArenaAutoCache] Workflow analysis completed: {len(found_models)} models found")
        return found_models

    except Exception as e:
        print(f"[ArenaAutoCache] Error analyzing workflow: {e}")
        import traceback
        traceback.print_exc()
        return found_models

def _get_model_category(node_type: str, field: str) -> str:
    """RU: Определяет категорию модели по типу ноды и полю."""
    # RU: Маппинг типов нод на категории моделей
    CATEGORY_MAPPING = {
        "CheckpointLoaderSimple": "checkpoints",
        "CheckpointLoader": "checkpoints",
        "UNETLoader": "unet",
        "VAELoader": "vaes",
        "VAEDecode": "vaes",
        "VAEEncode": "vaes",
        "LoraLoader": "loras",
        "ControlNetLoader": "controlnet",
        "ControlNetApply": "controlnet",
        "CLIPLoader": "clip",
        "UpscaleModelLoader": "upscale_models",
        "ImageUpscaleWithModel": "upscale_models",
        "HypernetworkLoader": "hypernetworks",
        "IPAdapterLoader": "ipadapter",
        "GLIGENLoader": "gligen",
        "AnimateDiffLoader": "animatediff_models",
        "InsightFaceLoader": "insightface",
        "FaceRestoreWithModel": "face_restore_models",
        "StyleModelLoader": "style_models",
        "T2IAdapterLoader": "t2i_adapter",
    }

    return CATEGORY_MAPPING.get(node_type, "unknown")

def _get_current_workflow() -> dict:
    """RU: Получает текущий workflow из ComfyUI."""
    try:
        # RU: Пробуем получить workflow через различные способы
        import sys

        print("[ArenaAutoCache] Attempting to get current workflow...")

        # Способ 1: Через server.PromptServer
        try:
            from server import PromptServer
            prompt_server = getattr(PromptServer, "instance", None)
            if prompt_server:
                print(f"[ArenaAutoCache] Found PromptServer instance: {type(prompt_server)}")

                # Проверяем различные атрибуты
                for attr in ['current_workflow', 'workflow', 'prompt', 'graph']:
                    if hasattr(prompt_server, attr):
                        workflow = getattr(prompt_server, attr)
                        if workflow:
                            print(f"[ArenaAutoCache] Found workflow via PromptServer.{attr}")
                            return workflow
        except Exception as e:
            print(f"[ArenaAutoCache] PromptServer method failed: {e}")

        # Способ 2: Через sys.modules
        print("[ArenaAutoCache] Searching sys.modules for workflow data...")
        for module_name, module in sys.modules.items():
            if any(keyword in module_name.lower() for keyword in ['comfy', 'server', 'web', 'app']):
                for attr in ['current_workflow', 'workflow', 'prompt', 'graph', 'canvas']:
                    if hasattr(module, attr):
                        workflow = getattr(module, attr)
                        if workflow:
                            print(f"[ArenaAutoCache] Found workflow in {module_name}.{attr}")
                            # RU: Проверяем, что это словарь, а не модуль
                            if isinstance(workflow, dict):
                                return workflow
                            elif hasattr(workflow, '__dict__'):
                                # RU: Если это объект, пробуем получить данные из его атрибутов
                                print("[ArenaAutoCache] Converting module/object to dict...")
                                try:
                                    # RU: Сначала пробуем получить nodes напрямую
                                    if hasattr(workflow, 'nodes'):
                                        nodes = workflow.nodes
                                        # RU: Проверяем, что nodes не является модулем
                                        if hasattr(nodes, '__dict__') and not isinstance(nodes, (dict, list)):
                                            print("[ArenaAutoCache] Nodes is a module/object, trying to extract data...")
                                            try:
                                                if hasattr(nodes, 'nodes'):
                                                    nodes = nodes.nodes
                                                    if nodes:
                                                        return {"nodes": nodes}
                                                else:
                                                    print("[ArenaAutoCache] Module has no 'nodes' attribute")
                                                    continue
                                            except Exception as e:
                                                print(f"[ArenaAutoCache] Error extracting from module: {e}")
                                                continue
                                        elif nodes:
                                            return {"nodes": nodes}
                                    # RU: Пробуем другие атрибуты
                                    elif hasattr(workflow, 'workflow'):
                                        return workflow.workflow
                                    elif hasattr(workflow, 'prompt'):
                                        return workflow.prompt
                                    else:
                                        # RU: Пробуем сериализовать объект
                                        import json
                                        workflow_dict = json.loads(json.dumps(workflow, default=str))
                                        if isinstance(workflow_dict, dict):
                                            return workflow_dict
                                except Exception as e:
                                    print(f"[ArenaAutoCache] Error converting workflow object: {e}")
                                    continue

        # Способ 3: Через глобальные переменные
        try:
            import __main__
            for attr in ['current_workflow', 'workflow', 'prompt', 'graph']:
                if hasattr(__main__, attr):
                    workflow = getattr(__main__, attr)
                    if workflow:
                        print(f"[ArenaAutoCache] Found workflow in __main__.{attr}")
                        return workflow
        except Exception as e:
            print(f"[ArenaAutoCache] __main__ method failed: {e}")

        # Способ 4: Через WebSocket или API (если доступно)
        try:
            # RU: Пробуем получить через WebSocket соединение
            import json
            import os

            # Проверяем, есть ли временные файлы с workflow
            temp_dirs = [
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "temp"),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "temp"),
                "/tmp",
                os.path.expanduser("~/tmp")
            ]

            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for file in os.listdir(temp_dir):
                        if file.endswith(('.json', '.workflow')) and 'workflow' in file.lower():
                            file_path = os.path.join(temp_dir, file)
                            try:
                                with open(file_path, encoding='utf-8') as f:
                                    workflow_data = json.load(f)
                                    if workflow_data and 'nodes' in workflow_data:
                                        print(f"[ArenaAutoCache] Found workflow in temp file: {file_path}")
                                        return workflow_data
                            except Exception:
                                continue
        except Exception as e:
            print(f"[ArenaAutoCache] Temp file method failed: {e}")

        print("[ArenaAutoCache] No workflow data found through any method")
        return {}

    except Exception as e:
        print(f"[ArenaAutoCache] Error getting current workflow: {e}")
        return {}

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
                        "tooltip": "Comma-separated list of model categories to automatically cache. Leave empty to cache all found models.",
                    },
                ),
                "force_warmup": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "description": "Force cache warmup",
                        "tooltip": "Force cache warmup even if already completed in this session",
                    },
                ),
                "comfyui_port": (
                    "INT",
                    {
                        "default": 8188,
                        "min": 1000,
                        "max": 65535,
                        "step": 1,
                        "description": "ComfyUI API port",
                        "tooltip": "Port where ComfyUI API is running. Leave 8188 for auto-detection. Check ComfyUI console for 'Starting server on port XXXX'",
                    },
                ),
                "comfyui_host": (
                    "STRING",
                    {
                        "default": "127.0.0.1",
                        "description": "ComfyUI API host",
                        "tooltip": "Host where ComfyUI API is running (default: 127.0.0.1)",
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
    DESCRIPTION = "Automatically analyze workflow via ComfyUI API and cache all models on first run. Prevents delays by pre-copying models from NAS to local SSD cache."
    OUTPUT_NODE = True

    def run(
        self,
        categories: str = "checkpoints,loras,vaes,upscale_models,controlnet",
        force_warmup: bool = False,
        comfyui_port: int = 8188,
        comfyui_host: str = "127.0.0.1"
    ):
        """Automatically detect and cache models from current workflow."""
        global _session_warmup_completed, _session_models_analyzed

        print("[ArenaAutoCache] Starting automatic model detection and caching")

        # RU: Проверяем, не был ли уже выполнен прогрев в этой сессии
        if _session_warmup_completed and not force_warmup:
            print("[ArenaAutoCache] Cache warmup already completed in this session")
            return json.dumps({
                "ok": True,
                "message": "Cache warmup already completed in this session",
                "warmup_completed": True,
                "models_analyzed": len(_session_models_analyzed),
                "force_warmup_available": True
            }, ensure_ascii=False, indent=2)

        if force_warmup:
            print("[ArenaAutoCache] Force warmup requested, resetting session state")
            _session_warmup_completed = False
            _session_models_analyzed.clear()

        # Убеждаемся, что патч путей активен
        _apply_folder_paths_patch_locked()

        # RU: Анализ workflow с канваса через HTTP API
        print("[ArenaAutoCache] Analyzing canvas workflow via HTTP API...")
        workflow_data = self._get_canvas_workflow_via_api()

        found_models = []
        if workflow_data:
            print("[ArenaAutoCache] Found canvas workflow, analyzing for models...")
            found_models = _analyze_workflow_for_models(workflow_data)
            print(f"[ArenaAutoCache] Found {len(found_models)} models in canvas workflow")
        else:
            print("[ArenaAutoCache] No canvas workflow found, trying direct methods...")
            workflow_data = self._get_workflow_direct()

            if workflow_data:
                print("[ArenaAutoCache] Found workflow via direct methods, analyzing for models...")
                found_models = _analyze_workflow_for_models(workflow_data)
                print(f"[ArenaAutoCache] Found {len(found_models)} models in workflow")
            else:
                return json.dumps({
                    "ok": False,
                    "message": "No workflow found on canvas or in execution",
                    "suggestion": "Load a workflow on canvas or run a workflow first"
                }, ensure_ascii=False, indent=2)

        if not found_models:
            print("[ArenaAutoCache] No models found in workflow")
            return json.dumps({
                "ok": False,
                "message": "No models found in current workflow",
                "details": [
                    "Add model loading nodes to your workflow",
                    "Use Load Checkpoint, Load VAE, or other model nodes",
                    "Make sure your workflow contains model loading nodes"
                ]
            }, ensure_ascii=False, indent=2)

        print(f"[ArenaAutoCache] Found {len(found_models)} models in workflow")

        # RU: Фильтруем модели по категориям если указано
        if categories and categories.strip():
            categories_list = [cat.strip() for cat in categories.split(",")]
            filtered_models = [
                model for model in found_models
                if model.get("category", "unknown") in categories_list
            ]
            print(f"[ArenaAutoCache] Filtered to {len(filtered_models)} models in specified categories")
            found_models = filtered_models

        # RU: Кешируем найденные модели асинхронно
        print(f"[ArenaAutoCache] Starting cache warmup for {len(found_models)} models")
        cache_results = self._cache_models_with_progress(found_models)
        print(f"[ArenaAutoCache] Cache warmup completed. Results: {len(cache_results)}")

        # RU: Обновляем состояние сессии
        _session_warmup_completed = True
        _session_models_analyzed.update([model["name"] for model in found_models])

        # Формируем результат
        cached_count = len([r for r in cache_results if r["status"] == "cached"])
        skipped_count = len([r for r in cache_results if r["status"].startswith("skipped")])
        error_count = len([r for r in cache_results if r["status"] in ["error", "not_found"]])

        result = {
            "ok": True,
            "message": f"Successfully processed {len(found_models)} models",
            "warmup_completed": True,
            "models_found": len(found_models),
            "cached": cached_count,
            "skipped": skipped_count,
            "errors": error_count,
            "categories_checked": [cat.strip() for cat in categories.split(",")] if categories else [],
            "models": found_models,
            "cache_results": cache_results,
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    def _find_comfyui_port(self, host: str = "127.0.0.1") -> int:
        """RU: Автоматически находит порт ComfyUI."""
        try:
            import requests

            # RU: Стандартные порты ComfyUI
            common_ports = [8188, 8189, 8190, 8080, 8081, 3000, 5000]

            for port in common_ports:
                try:
                    api_url = f"http://{host}:{port}"
                    response = requests.get(f"{api_url}/system_stats", timeout=2)
                    if response.status_code == 200:
                        print(f"[ArenaAutoCache] Auto-detected ComfyUI at {api_url}")
                        return port
                except Exception:
                    continue

            print("[ArenaAutoCache] Could not auto-detect ComfyUI port")
            return None

        except Exception as e:
            print(f"[ArenaAutoCache] Error auto-detecting port: {e}")
            return None

    def _get_workflow_via_api(self, host: str = "127.0.0.1", port: int = 8188) -> dict:
        """RU: Получает workflow через ComfyUI API."""
        try:
            import json
            import os

            import requests

            # RU: Если порт не найден, пробуем автоопределение
            if port == 8188:  # Значение по умолчанию
                detected_port = self._find_comfyui_port(host)
                if detected_port:
                    port = detected_port
                    print(f"[ArenaAutoCache] Using auto-detected port: {port}")

            # RU: Используем переданные параметры или переменные окружения
            api_url = f"http://{host}:{port}"

            # RU: Проверяем доступность API
            try:
                response = requests.get(f"{api_url}/system_stats", timeout=5)
                if response.status_code == 200:
                    print(f"[ArenaAutoCache] Found ComfyUI at {api_url}")
                else:
                    print(f"[ArenaAutoCache] ComfyUI API not accessible at {api_url} (status: {response.status_code})")
                    return {}
            except Exception as e:
                print(f"[ArenaAutoCache] ComfyUI API not accessible at {api_url}: {e}")
                return {}

            # Способ 1: Через history API
            try:
                response = requests.get(f"{api_url}/history", timeout=5)
                if response.status_code == 200:
                    history = response.json()
                    if history:
                        # RU: Берем последний выполненный workflow
                        latest = max(history.keys(), key=lambda x: history[x].get('timestamp', 0))
                        workflow_data = history[latest].get('prompt', {})
                        if workflow_data and workflow_data.get('nodes'):
                            print(f"[ArenaAutoCache] Found workflow via history API: {len(workflow_data.get('nodes', {}))} nodes")
                            return workflow_data
            except Exception as e:
                print(f"[ArenaAutoCache] History API failed: {e}")

            # Способ 2: Через queue API
            try:
                response = requests.get(f"{api_url}/queue", timeout=5)
                if response.status_code == 200:
                    queue_data = response.json()
                    if queue_data.get('queue_running') or queue_data.get('queue_pending'):
                        # RU: Берем первый элемент из очереди
                        queue_item = (queue_data.get('queue_running', []) + queue_data.get('queue_pending', []))[0]
                        if len(queue_item) > 1:
                            workflow_data = queue_item[1].get('prompt', {})
                            if workflow_data and workflow_data.get('nodes'):
                                print(f"[ArenaAutoCache] Found workflow via queue API: {len(workflow_data.get('nodes', {}))} nodes")
                                return workflow_data
            except Exception as e:
                print(f"[ArenaAutoCache] Queue API failed: {e}")

            print("[ArenaAutoCache] No workflow found via ComfyUI API")
            return {}

        except ImportError:
            print("[ArenaAutoCache] requests module not available for API calls")
            return {}
        except Exception as e:
            print(f"[ArenaAutoCache] API method failed: {e}")
            return {}

    def _get_canvas_workflow_via_api(self) -> dict:
        """RU: Получает данные канваса через HTTP API."""
        try:
            import requests

            # RU: Получаем данные канваса через API
            api_url = "http://127.0.0.1:8188"

            print("[ArenaAutoCache] Trying to get canvas workflow via HTTP API...")

            # RU: Способ 1: Через history API (последний выполненный workflow)
            try:
                response = requests.get(f"{api_url}/history", timeout=5)
                if response.status_code == 200:
                    history = response.json()
                    if history:
                        # RU: Берем последний выполненный workflow
                        latest = max(history.keys(), key=lambda x: history[x].get('timestamp', 0))
                        workflow_data = history[latest].get('prompt', {})
                        if workflow_data and workflow_data.get('nodes'):
                            print(f"[ArenaAutoCache] Found canvas workflow via history API: {len(workflow_data.get('nodes', {}))} nodes")
                            return workflow_data
            except Exception as e:
                print(f"[ArenaAutoCache] History API failed: {e}")

            # RU: Способ 2: Через queue API (текущий workflow в очереди)
            try:
                response = requests.get(f"{api_url}/queue", timeout=5)
                if response.status_code == 200:
                    queue_data = response.json()
                    if queue_data.get('queue_pending'):
                        # RU: Берем первый элемент из очереди
                        queue_item = queue_data['queue_pending'][0]
                        if len(queue_item) > 1:
                            workflow_data = queue_item[1].get('prompt', {})
                            if workflow_data and workflow_data.get('nodes'):
                                print(f"[ArenaAutoCache] Found canvas workflow via queue API: {len(workflow_data.get('nodes', {}))} nodes")
                                return workflow_data
            except Exception as e:
                print(f"[ArenaAutoCache] Queue API failed: {e}")

            print("[ArenaAutoCache] No canvas workflow found via API")
            return {}

        except ImportError:
            print("[ArenaAutoCache] requests module not available for API calls")
            return {}
        except Exception as e:
            print(f"[ArenaAutoCache] Canvas API method failed: {e}")
            return {}

    def _get_workflow_direct(self) -> dict:
        """RU: Прямое подключение к ComfyUI через внутренние модули."""
        try:
            import sys

            # RU: Способ 1: Через server.PromptServer (лучший способ)
            try:
                from server import PromptServer
                prompt_server = getattr(PromptServer, "instance", None)
                if prompt_server:
                    print("[ArenaAutoCache] Found PromptServer instance")

                    # RU: Пробуем получить workflow из различных атрибутов
                    for attr in ['current_workflow', 'workflow', 'prompt', 'graph', 'canvas']:
                        if hasattr(prompt_server, attr):
                            workflow = getattr(prompt_server, attr)
                            if workflow:
                                print(f"[ArenaAutoCache] Found workflow via PromptServer.{attr}")
                                # RU: Проверяем, что это словарь с nodes
                                if isinstance(workflow, dict) and workflow.get('nodes'):
                                    return workflow
                                elif hasattr(workflow, 'nodes'):
                                    nodes = workflow.nodes
                                    if nodes:
                                        return {"nodes": nodes}
            except Exception as e:
                print(f"[ArenaAutoCache] PromptServer method failed: {e}")

            # RU: Способ 2: Через sys.modules (поиск в загруженных модулях)
            print("[ArenaAutoCache] Searching sys.modules for workflow data...")
            for module_name, module in sys.modules.items():
                if any(keyword in module_name.lower() for keyword in ['comfy', 'server', 'web', 'app']):
                    for attr in ['current_workflow', 'workflow', 'prompt', 'graph', 'canvas']:
                        if hasattr(module, attr):
                            workflow = getattr(module, attr)
                            if workflow:
                                print(f"[ArenaAutoCache] Found workflow in {module_name}.{attr}")
                                if isinstance(workflow, dict) and workflow.get('nodes'):
                                    return workflow
                                elif hasattr(workflow, 'nodes'):
                                    nodes = workflow.nodes
                                    if nodes:
                                        # RU: Проверяем, что nodes не является модулем
                                        if hasattr(nodes, '__dict__') and not isinstance(nodes, (dict, list)):
                                            print("[ArenaAutoCache] Nodes is a module, trying to extract data...")
                                            # RU: Пробуем получить данные из модуля
                                            if hasattr(nodes, 'nodes'):
                                                nodes = nodes.nodes
                                                if isinstance(nodes, dict) and nodes or isinstance(nodes, list) and nodes:
                                                    return {"nodes": nodes}
                                        elif isinstance(nodes, dict) and nodes or isinstance(nodes, list) and nodes:
                                            return {"nodes": nodes}

            # RU: Способ 3: Простой поиск в sys.modules
            print("[ArenaAutoCache] Searching sys.modules for workflow data...")
            for module_name, module in sys.modules.items():
                if any(keyword in module_name.lower() for keyword in ['comfy', 'server', 'web', 'app']):
                    for attr in ['current_workflow', 'workflow', 'prompt', 'graph', 'canvas']:
                        if hasattr(module, attr):
                            workflow = getattr(module, attr)
                            if workflow:
                                print(f"[ArenaAutoCache] Found workflow in {module_name}.{attr}")
                                if isinstance(workflow, dict) and workflow.get('nodes'):
                                    return workflow
                                elif hasattr(workflow, 'nodes'):
                                    nodes = workflow.nodes
                                    if isinstance(nodes, dict) and nodes or isinstance(nodes, list) and nodes:
                                        return {"nodes": nodes}

            # RU: Способ 3: Через глобальные переменные
            try:
                import __main__
                for attr in ['current_workflow', 'workflow', 'prompt', 'graph']:
                    if hasattr(__main__, attr):
                        workflow = getattr(__main__, attr)
                        if workflow:
                            print(f"[ArenaAutoCache] Found workflow via __main__.{attr}")
                            if isinstance(workflow, dict) and workflow.get('nodes'):
                                return workflow
            except Exception as e:
                print(f"[ArenaAutoCache] __main__ method failed: {e}")

            print("[ArenaAutoCache] No workflow found via direct methods")
            return {}

        except Exception as e:
            print(f"[ArenaAutoCache] Error in direct workflow detection: {e}")
            return {}

    def _get_workflow_alternative(self) -> dict:
        """RU: Альтернативные способы получения workflow."""
        try:
            import glob
            import json
            import os

            # RU: Способ 1: Поиск в папке ComfyUI
            comfyui_paths = [
                os.path.join(os.path.dirname(__file__), "..", "..", ".."),  # ComfyUI root
                os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."),  # One level up
                "C:\\ComfyUI",  # Standard Windows path
                os.path.expanduser("~/ComfyUI"),  # User home
            ]

            for comfyui_path in comfyui_paths:
                if os.path.exists(comfyui_path):
                    # RU: Ищем workflow файлы
                    workflow_patterns = [
                        os.path.join(comfyui_path, "workflows", "*.json"),
                        os.path.join(comfyui_path, "user", "default", "workflows", "*.json"),
                        os.path.join(comfyui_path, "*.json"),
                        os.path.join(comfyui_path, "temp", "*.json"),
                    ]

                    for pattern in workflow_patterns:
                        for workflow_file in glob.glob(pattern):
                            try:
                                with open(workflow_file, encoding='utf-8') as f:
                                    workflow_data = json.load(f)
                                    if workflow_data and workflow_data.get('nodes'):
                                        print(f"[ArenaAutoCache] Found workflow file: {workflow_file}")
                                        return workflow_data
                            except Exception:
                                continue

            # RU: Способ 2: Поиск в системных папках
            temp_dirs = [
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "temp"),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "temp"),
                "/tmp",
                os.path.expanduser("~/tmp"),
                os.path.expanduser("~/AppData/Local/Temp"),
            ]

            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for file in os.listdir(temp_dir):
                        if file.endswith(('.json', '.workflow')) and 'workflow' in file.lower():
                            file_path = os.path.join(temp_dir, file)
                            try:
                                with open(file_path, encoding='utf-8') as f:
                                    workflow_data = json.load(f)
                                    if workflow_data and workflow_data.get('nodes'):
                                        print(f"[ArenaAutoCache] Found workflow in temp: {file_path}")
                                        return workflow_data
                            except Exception:
                                continue

            print("[ArenaAutoCache] No workflow files found")
            return {}

        except Exception as e:
            print(f"[ArenaAutoCache] Error in alternative workflow detection: {e}")
            return {}

    def _analyze_current_canvas(self, categories: str) -> list[dict]:
        """RU: Анализирует текущий canvas для поиска моделей."""
        categories_list = [cat.strip() for cat in categories.split(",")]
        found_models = []

        try:
            # RU: Пробуем различные способы получения папок с моделями
            model_folders = {}

            # Способ 1: Через get_folder_paths
            try:
                from folder_paths import get_folder_paths
                model_folders = get_folder_paths()
                print(f"[ArenaAutoCache] Got folder_paths via get_folder_paths: {len(model_folders)} folders")
            except Exception as e:
                print(f"[ArenaAutoCache] get_folder_paths failed: {e}")

                # Способ 2: Через folder_paths напрямую
                try:
                    from folder_paths import folder_paths
                    model_folders = folder_paths
                    print(f"[ArenaAutoCache] Got folder_paths directly: {len(model_folders)} folders")
                except Exception as e:
                    print(f"[ArenaAutoCache] Direct folder_paths failed: {e}")

                    # Способ 3: Через стандартные пути ComfyUI
                    print("[ArenaAutoCache] Using standard ComfyUI paths")
                    model_folders = self._get_standard_model_paths()

            if not model_folders:
                print("[ArenaAutoCache] No model folders found, trying alternative approach")
                return self._analyze_models_alternative()

            # Ищем модели в папках
            for category in categories_list:
                if category in model_folders:
                    category_path = Path(model_folders[category])
                    if category_path.exists():
                        print(f"[ArenaAutoCache] Scanning {category} folder: {category_path}")
                        for model_file in category_path.iterdir():
                            if model_file.is_file() and model_file.suffix.lower() in ['.ckpt', '.safetensors', '.pt', '.pth', '.bin']:
                                found_models.append({
                                    "name": model_file.name,
                                    "category": category,
                                    "path": str(model_file),
                                    "size_mb": model_file.stat().st_size / (1024 * 1024),
                                    "source": "canvas_analysis"
                                })
                                print(f"[ArenaAutoCache] Found model: {model_file.name} in {category}")

            print(f"[ArenaAutoCache] Canvas analysis found {len(found_models)} models")
            return found_models

        except Exception as e:
            print(f"[ArenaAutoCache] Error analyzing canvas: {e}")
            return []

    def _get_standard_model_paths(self) -> dict:
        """RU: Получает стандартные пути к моделям ComfyUI."""
        try:
            # RU: Стандартные пути ComfyUI
            import os
            # RU: Ищем корень ComfyUI, поднимаясь по директориям
            current_path = os.path.dirname(__file__)
            base_path = current_path

            # RU: Поднимаемся до корня ComfyUI (ищем папку с models)
            for _ in range(5):  # Максимум 5 уровней вверх
                if os.path.exists(os.path.join(base_path, "models")):
                    break
                parent = os.path.dirname(base_path)
                if parent == base_path:  # Достигли корня файловой системы
                    break
                base_path = parent

            print(f"[ArenaAutoCache] Detected ComfyUI root: {base_path}")

            standard_paths = {
                "checkpoints": os.path.join(base_path, "models", "checkpoints"),
                "loras": os.path.join(base_path, "models", "loras"),
                "vaes": os.path.join(base_path, "models", "vae"),
                "upscale_models": os.path.join(base_path, "models", "upscale_models"),
                "controlnet": os.path.join(base_path, "models", "controlnet"),
                "clip": os.path.join(base_path, "models", "clip"),
                "hypernetworks": os.path.join(base_path, "models", "hypernetworks"),
                "ipadapter": os.path.join(base_path, "models", "ipadapter"),
                "gligen": os.path.join(base_path, "models", "gligen"),
                "animatediff_models": os.path.join(base_path, "models", "animatediff"),
                "insightface": os.path.join(base_path, "models", "insightface"),
                "face_restore_models": os.path.join(base_path, "models", "face_restore"),
                "style_models": os.path.join(base_path, "models", "style_models"),
                "t2i_adapter": os.path.join(base_path, "models", "t2i_adapter"),
            }

            # RU: Фильтруем только существующие папки
            existing_paths = {}
            for category, path in standard_paths.items():
                if os.path.exists(path):
                    existing_paths[category] = path
                    print(f"[ArenaAutoCache] Found standard path: {category} -> {path}")

            return existing_paths

        except Exception as e:
            print(f"[ArenaAutoCache] Error getting standard paths: {e}")
            return {}

    def _analyze_models_alternative(self) -> list[dict]:
        """RU: Альтернативный способ поиска моделей."""
        try:
            print("[ArenaAutoCache] Trying alternative model detection...")

            # RU: Ищем модели в известных местах
            import os
            # RU: Ищем корень ComfyUI, поднимаясь по директориям
            current_path = os.path.dirname(__file__)
            base_path = current_path

            # RU: Поднимаемся до корня ComfyUI (ищем папку с models)
            for _ in range(5):  # Максимум 5 уровней вверх
                if os.path.exists(os.path.join(base_path, "models")):
                    break
                parent = os.path.dirname(base_path)
                if parent == base_path:  # Достигли корня файловой системы
                    break
                base_path = parent

            models_path = os.path.join(base_path, "models")
            print(f"[ArenaAutoCache] Looking for models in: {models_path}")

            if not os.path.exists(models_path):
                print(f"[ArenaAutoCache] Models directory not found: {models_path}")
                return []

            found_models = []

            # RU: Рекурсивно ищем файлы моделей
            for root, dirs, files in os.walk(models_path):
                for file in files:
                    if file.lower().endswith(('.ckpt', '.safetensors', '.pt', '.pth', '.bin')):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(root, models_path)

                        # RU: Определяем категорию по пути
                        category = "unknown"
                        if "checkpoints" in relative_path.lower():
                            category = "checkpoints"
                        elif "lora" in relative_path.lower():
                            category = "loras"
                        elif "vae" in relative_path.lower():
                            category = "vaes"
                        elif "upscale" in relative_path.lower():
                            category = "upscale_models"
                        elif "controlnet" in relative_path.lower():
                            category = "controlnet"
                        elif "clip" in relative_path.lower():
                            category = "clip"
                        elif "hypernetwork" in relative_path.lower():
                            category = "hypernetworks"
                        elif "ipadapter" in relative_path.lower():
                            category = "ipadapter"
                        elif "gligen" in relative_path.lower():
                            category = "gligen"
                        elif "animatediff" in relative_path.lower():
                            category = "animatediff_models"
                        elif "insightface" in relative_path.lower():
                            category = "insightface"
                        elif "face_restore" in relative_path.lower():
                            category = "face_restore_models"
                        elif "style" in relative_path.lower():
                            category = "style_models"
                        elif "t2i_adapter" in relative_path.lower():
                            category = "t2i_adapter"

                        found_models.append({
                            "name": file,
                            "category": category,
                            "path": file_path,
                            "size_mb": os.path.getsize(file_path) / (1024 * 1024),
                            "source": "alternative_analysis"
                        })
                        print(f"[ArenaAutoCache] Found model: {file} in {category} ({relative_path})")

            print(f"[ArenaAutoCache] Alternative analysis found {len(found_models)} models")
            return found_models

        except Exception as e:
            print(f"[ArenaAutoCache] Error in alternative analysis: {e}")
            return []

    def _cache_models_with_progress(self, models: list[dict]) -> list[dict]:
        """RU: Кеширует модели с отображением прогресса и асинхронным копированием."""
        results = []

        for i, model in enumerate(models, 1):
            try:
                print(f"[ArenaAutoCache] Processing model {i}/{len(models)}: {model['name']}")

                # RU: Получаем путь к исходному файлу модели
                source_path = self._get_model_source_path(model)
                if not source_path or not source_path.exists():
                    results.append({
                        "name": model["name"],
                        "category": model.get("category", "unknown"),
                        "status": "not_found",
                        "message": f"Source file not found: {source_path}"
                    })
                    print(f"[ArenaAutoCache] ❌ Model not found: {model['name']}")
                    continue

                # Проверяем размер файла
                file_size_mb = source_path.stat().st_size / (1024 * 1024)
                if file_size_mb < _settings.min_size_mb:
                    results.append({
                        "name": model["name"],
                        "category": model.get("category", "unknown"),
                        "status": "skipped_small",
                        "message": f"File too small: {file_size_mb:.1f} MB < {_settings.min_size_mb} MB"
                    })
                    print(f"[ArenaAutoCache] ⏭️ Skipping small file: {model['name']} ({file_size_mb:.1f} MB)")
                    continue

                # Создаем папку кеша
                cache_dir = _settings.root / model.get("category", "unknown")
                cache_dir.mkdir(parents=True, exist_ok=True)

                # Проверяем, не кеширован ли уже файл
                cache_file = cache_dir / model["name"]
                if cache_file.exists():
                    results.append({
                        "name": model["name"],
                        "category": model.get("category", "unknown"),
                        "status": "skipped_exists",
                        "message": "Already cached"
                    })
                    print(f"[ArenaAutoCache] ✅ Already cached: {model['name']}")
                    continue

                # RU: Копируем файл асинхронно
                print(f"[ArenaAutoCache] 🔄 Caching: {model['name']} ({file_size_mb:.1f} MB)")
                self._copy_model_async(source_path, cache_file, model["name"])

                results.append({
                    "name": model["name"],
                    "category": model.get("category", "unknown"),
                    "status": "cached",
                    "message": f"Cached successfully ({file_size_mb:.1f} MB)"
                })
                print(f"[ArenaAutoCache] ✅ Cached: {model['name']}")

            except Exception as e:
                results.append({
                    "name": model["name"],
                    "category": model.get("category", "unknown"),
                    "status": "error",
                    "message": f"Error: {str(e)}"
                })
                print(f"[ArenaAutoCache] ❌ Error caching {model['name']}: {e}")

        return results

    def _get_model_source_path(self, model: dict) -> Path:
        """RU: Получает путь к исходному файлу модели."""
        try:
            # RU: Пробуем найти файл в стандартных папках ComfyUI
            from folder_paths import get_folder_paths

            category = model.get("category", "unknown")
            model_name = model["name"]

            # Получаем папки для данной категории
            try:
                folder_paths = get_folder_paths(category)
                if folder_paths:
                    for folder_path in folder_paths:
                        folder_path_obj = Path(folder_path)
                        if folder_path_obj.exists():
                            model_path = folder_path_obj / model_name
                            if model_path.exists():
                                return model_path
            except Exception as e:
                print(f"[ArenaAutoCache] Error getting folder paths for {category}: {e}")
                # RU: Пробуем стандартные пути
                try:
                    from folder_paths import folder_paths
                    if category in folder_paths:
                        for folder_path in folder_paths[category]:
                            folder_path_obj = Path(folder_path)
                            if folder_path_obj.exists():
                                model_path = folder_path_obj / model_name
                                if model_path.exists():
                                    return model_path
                except Exception as e2:
                    print(f"[ArenaAutoCache] Error with standard paths: {e2}")

            # RU: Пробуем найти в других папках
            for other_category in ['checkpoints', 'loras', 'vaes', 'embeddings']:
                if other_category != category:
                    try:
                        other_folder_paths = get_folder_paths(other_category)
                        if other_folder_paths:
                            for folder_path in other_folder_paths:
                                folder_path_obj = Path(folder_path)
                                if folder_path_obj.exists():
                                    model_path = folder_path_obj / model_name
                                    if model_path.exists():
                                        return model_path
                    except Exception:
                        continue

            return None

        except Exception as e:
            print(f"[ArenaAutoCache] Error getting source path for {model['name']}: {e}")
            return None

    def _copy_model_async(self, source_path: Path, cache_file: Path, model_name: str):
        """RU: Асинхронно копирует модель в кэш."""
        try:
            # RU: Используем threading для неблокирующего копирования
            def copy_worker():
                try:
                    shutil.copy2(source_path, cache_file)
                    print(f"[ArenaAutoCache] ✅ Async copy completed: {model_name}")
                except Exception as e:
                    print(f"[ArenaAutoCache] ❌ Async copy failed: {model_name}: {e}")

            # Запускаем копирование в отдельном потоке
            copy_thread = threading.Thread(target=copy_worker, daemon=True)
            copy_thread.start()

            # RU: Ждем завершения копирования (можно убрать для полностью асинхронного режима)
            copy_thread.join(timeout=30)  # Таймаут 30 секунд

        except Exception as e:
            print(f"[ArenaAutoCache] Error in async copy for {model_name}: {e}")
            # RU: Fallback к синхронному копированию
            shutil.copy2(source_path, cache_file)

# Версия нод
ARENA_NODES_VERSION = "v3.2.0"

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
