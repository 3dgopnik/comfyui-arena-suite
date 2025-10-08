"""
Arena Path Manager

Purpose: Register NAS model paths in ComfyUI without relying on extra_model_paths.yaml,
while keeping a clean fallback and restoration workflow.

Notes:
- Code style: explicit, readable, safe. Windows UNC awareness.
- No heavy recursion on startup: shallow scan of known subfolders only.
"""

from __future__ import annotations

import os
import threading
import json
import time
from pathlib import Path
from typing import Dict, List


_register_lock = threading.Lock()
_cached_path_map: Dict[str, List[str]] | None = None
_CACHE_FILE = Path(__file__).parent.parent / "user" / "arena_nas_cache.json"


KNOWN_CATEGORY_FOLDERS: dict[str, list[str]] = {
    # Core categories
    "checkpoints": ["SDXL", "SD3", "SD1.5", "Stable-Cascade", "SD", "Stable-Diffusion"],
    "loras": [
        "Lora",
        "Lora\\Flux",
        "SD1.5\\SD15_LORA",
        "SDXL\\XL_LORA",
        "IPAdapter\\IPA-Lora",
    ],
    "vae": ["vae", "vae_approx"],
    "clip": ["clip"],
    "clip_vision": ["clip_vision"],
    "controlnet": [
        "CN",
        "CN\\Xlabs",
        "IPAdapter\\IPA-sdxl_models",
        "IPAdapter\\IPA-15-models",
    ],
    "diffusion_models": ["unet", "unet\\flux", "unet\\kolors", "style_models"],
    "embeddings": ["embeds"],
    "upscale_models": ["Upscale", "apisr", "stablesr", "SUPIR", "CCSR"],
    "insightface": ["antelopev2", "facerestore_models"],
    "ultralytics": ["ultralytics\\bbox", "ultralytics\\segm"],
    # Optional families (extend as needed)
    "animatediff": ["Animatediff"],
    "pix2pix": ["Pix2Pix"],
    "pulid": ["pulid"],
    "sams": ["sams"],
    "inpaint": ["inpaint", "SDXL\\SDXLInpaint"],
    # Encoders for IPAdapter
    "ipadapter_encoders": [
        "IPAdapter\\image_encoder",
        "IPAdapter\\IPA-sdxl_models\\image_encoder",
        "IPAdapter\\IPA-15-models\\image_encoder",
    ],
}


def get_nas_root() -> str:
    """Read NAS root path from environment (ARENA_NAS_ROOT)."""
    return os.environ.get("ARENA_NAS_ROOT", "").strip()


def _is_path_ok(path: Path) -> bool:
    """Conservative path validation to avoid shallow roots and invalid UNC issues."""
    try:
        p = path.expanduser().resolve(strict=False)
    except Exception:
        return False

    # Windows-specific safety checks
    if os.name == "nt":
        s = str(p)
        if s.startswith("\\\\"):  # UNC
            parts = s.split("\\")
            # Expect at least \\server\share\folder
            if len(parts) <= 4:
                return False
        # Require depth C:\folder\subfolder (>= 3 parts)
        if p.drive and len(p.parts) < 3:
            return False

    # POSIX safety checks
    else:
        forbidden_roots = {"/", "/mnt", "/media", "/Volumes"}
        if str(p) in forbidden_roots:
            return False
        if len(p.parts) < 3:
            return False

    return True


def load_cached_structure() -> dict[str, list[str]]:
    """Load cached NAS structure from disk."""
    try:
        if _CACHE_FILE.exists():
            with open(_CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'paths' in data:
                    return data['paths']
    except Exception:
        pass
    return {}


def save_cached_structure(path_map: dict[str, list[str]], nas_root: str) -> None:
    """Save NAS structure to cache with metadata."""
    try:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        cache_data = {
            'nas_root': nas_root,
            'timestamp': time.time(),
            'paths': path_map
        }
        with open(_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def is_cache_valid(nas_root: str, max_age_hours: int = 24) -> bool:
    """Check if cached structure is still valid."""
    try:
        if not _CACHE_FILE.exists():
            return False
        
        with open(_CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if data.get('nas_root') != nas_root:
            return False
        
        cache_time = data.get('timestamp', 0)
        age_hours = (time.time() - cache_time) / 3600
        return age_hours < max_age_hours
    except Exception:
        return False


def scan_nas_structure(nas_root: str, use_cache: bool = True) -> dict[str, list[str]]:
    """Build a mapping of ComfyUI categories to existing folders under NAS root.

    Uses cache if valid, otherwise scans and caches result.
    """
    global _cached_path_map

    if not nas_root:
        return {}

    # Try cache first
    if use_cache and is_cache_valid(nas_root):
        cached = load_cached_structure()
        if cached:
            _cached_path_map = cached
            return cached

    # Scan NAS
    root = Path(nas_root)
    if not _is_path_ok(root) or not root.exists():
        return {}

    path_map: dict[str, list[str]] = {}
    for category, subfolders in KNOWN_CATEGORY_FOLDERS.items():
        existing: list[str] = []
        for sub in subfolders:
            p = root / sub
            if p.exists() and p.is_dir():
                existing.append(str(p))
        if existing:
            path_map[category] = existing

    # Cache result
    if path_map:
        save_cached_structure(path_map, nas_root)

    _cached_path_map = path_map
    return path_map


def register_paths_in_folder_paths(path_map: dict[str, list[str]]) -> int:
    """Register discovered paths into ComfyUI's folder_paths registry.

    Returns number of paths registered.
    """
    if not path_map:
        return 0

    try:
        import folder_paths  # provided by ComfyUI at runtime
    except Exception:
        return 0

    registered = 0
    with _register_lock:
        for category, paths in path_map.items():
            for p in paths:
                try:
                    folder_paths.add_model_folder_path(category, p)
                    registered += 1
                except Exception:
                    # Best effort: skip invalid entries
                    continue
    return registered


def migrate_from_yaml(yaml_path: Path) -> dict[str, str]:
    """Read extra_model_paths.yaml and infer a minimal Arena configuration.

    Strategy: pick first profile with is_default == true if present; otherwise choose
    the first profile that contains checkpoints/loras/etc. and derive ARENA_NAS_ROOT
    as the common parent directory. This is heuristic on purpose and safe.
    """
    try:
        import yaml  # type: ignore
    except Exception:
        return {}

    if not yaml_path.exists():
        return {}

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}

    # Try choose profile
    chosen = None
    for profile_name, profile in data.items():
        if isinstance(profile, dict) and str(profile.get("is_default", "")).lower() in {"true", "1", "yes"}:
            chosen = profile
            break
    if not chosen:
        # choose any dict profile
        for profile in data.values():
            if isinstance(profile, dict):
                chosen = profile
                break
    if not chosen:
        return {}

    base_path = str(chosen.get("base_path", "")).strip()
    if not base_path:
        return {}

    env: dict[str, str] = {"ARENA_NAS_ROOT": base_path}
    return env


def ensure_yaml_exists(target_path: Path, template_path: Path, *, force: bool = False) -> bool:
    """Ensure extra_model_paths.yaml exists at Electron location.

    Copies from template when target is missing or when force=True and template exists.
    Returns True if file exists/was restored, False otherwise.
    """
    try:
        if force and template_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(str(template_path), str(target_path))
            return True

        if target_path.exists():
            return True

        if template_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(str(template_path), str(target_path))
            return True

        return False
    except Exception:
        return False


