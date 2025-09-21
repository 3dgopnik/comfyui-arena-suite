import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace


def _stub_module(name: str) -> ModuleType:
    module = ModuleType(name)
    sys.modules[name] = module
    return module


def _ensure_module(name: str) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    if "." in name:
        parent_name, _, child_name = name.rpartition(".")
        parent = _ensure_module(parent_name)
        module = ModuleType(name)
        setattr(parent, child_name, module)
        sys.modules[name] = module
        return module
    return _stub_module(name)


for module_name in (
    "numpy",
    "torch",
    "nodes",
    "cv2",
    "folder_paths",
):
    _ensure_module(module_name)


segment_anything = _ensure_module("segment_anything")
segment_anything.SamPredictor = SimpleNamespace
latent_preview = _ensure_module("latent_preview")
latent_preview.TAESD = SimpleNamespace
latent_preview.TAESDPreviewerImpl = SimpleNamespace
latent_preview.Latent2RGBPreviewer = SimpleNamespace


comfy_extras = _ensure_module("comfy_extras")


class _NoiseRandomNoise:
    def __init__(self, *args, **kwargs):
        pass

    def generate_noise(self, *args, **kwargs):
        return None


_ensure_module("comfy_extras.nodes_custom_sampler").Noise_RandomNoise = _NoiseRandomNoise
_ensure_module("comfy_extras.nodes_upscale_model")
_ensure_module("comfy_extras.nodes_differential_diffusion")

skimage_measure = _ensure_module("skimage.measure")
skimage_measure.label = lambda *args, **kwargs: None

server_module = _ensure_module("server")
server_module.PromptServer = SimpleNamespace

comfy_module = _ensure_module("comfy")
ksampler = type("KSampler", (), {"SCHEDULERS": []})
comfy_module.samplers = SimpleNamespace(KSampler=ksampler)
model_management_module = _ensure_module("comfy.model_management")
setattr(comfy_module, "model_management", model_management_module)
cli_args_module = _ensure_module("comfy.cli_args")
cli_args_module.args = SimpleNamespace(latent_preview_method=None)


class _LatentPreviewMethod:
    NoPreviews = "NoPreviews"
    Auto = "Auto"
    Latent2RGB = "Latent2RGB"
    TAESD = "TAESD"


cli_args_module.LatentPreviewMethod = _LatentPreviewMethod


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import custom_nodes.ComfyUI_Arena.legacy.core as legacy_core


def test_set_previewbridge_image_reuses_cached_identifier(monkeypatch):
    monkeypatch.setattr(legacy_core, "preview_bridge_image_name_map", {})
    monkeypatch.setattr(legacy_core, "preview_bridge_image_id_map", {})
    monkeypatch.setattr(legacy_core, "pb_id_cnt", 1)

    first_item = object()
    first_id = legacy_core.set_previewbridge_image("node123", "file.png", first_item)

    second_item = object()
    second_id = legacy_core.set_previewbridge_image("node123", "file.png", second_item)

    assert first_id == second_id
    assert legacy_core.preview_bridge_image_name_map == {
        ("node123", "file.png"): (first_id, first_item)
    }
    assert legacy_core.preview_bridge_image_id_map == {first_id: ("file.png", first_item)}
    assert legacy_core.pb_id_cnt == 2
