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

# RU: Определяем путь к кеш файлу в глобальном user directory ComfyUI
def _get_cache_file_path() -> Path:
    """Get path to NAS cache file in ComfyUI user directory."""
    # Try to find ComfyUI root (same logic as in arena_auto_cache_simple.py)
    try:
        current = Path(__file__).resolve()
        for parent in [current] + list(current.parents):
            if (parent / "comfy").exists() or (parent / "server.py").exists():
                return parent / "user" / "arena_nas_cache.json"
    except Exception:
        pass
    # Fallback to local user directory
    return Path(__file__).parent.parent / "user" / "arena_nas_cache.json"

_CACHE_FILE = _get_cache_file_path()


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
    "diffusion_models": ["unet", "unet\\flux", "unet\\kolors", "style_models", "Diffusion Model"],
    "embeddings": ["embeds"],
    "upscale_models": ["Upscale", "apisr", "stablesr", "SUPIR", "SDXL", "SD1.5", "CCSR"],
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


def scan_nas_structure(nas_root: str, use_cache: bool = True, min_size_mb: float = None, max_depth: int = None) -> dict[str, list[str]]:
    """Build a mapping of ComfyUI categories to existing folders under NAS root.

    Uses cache if valid, otherwise scans and caches result.
    Recursively discovers ALL subdirectories containing model files (max 3 levels).
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

    # Read settings from environment or use defaults
    if min_size_mb is None:
        min_size_mb = float(os.environ.get("ARENA_CACHE_MIN_SIZE_MB", "1.0"))
    if max_depth is None:
        max_depth = int(os.environ.get("ARENA_NAS_SCAN_MAX_DEPTH", "3"))
    
    min_size_bytes = int(min_size_mb * 1024 * 1024)
    ignore_extensions = {'.txt', '.md', '.json', '.yaml', '.yml', '.log', '.jpg', '.jpeg', '.png', '.gif', '.sha256', '.py', '.pyc', '.ini', '.cfg'}
    
    path_map: dict[str, list[str]] = {}
    
    # UNIVERSAL SCAN: Find ALL folders with model files, regardless of name
    all_found_paths = set()
    
    def universal_scan_dir(path: Path, depth: int):
        """Scan directory for model files and add to global set."""
        if depth > max_depth:
            return
        
        try:
            items = list(path.iterdir())
        except Exception:
            return
        
        # Check files in current directory
        has_models = False
        for item in items:
            if item.is_file():
                ext = item.suffix.lower()
                if ext in ignore_extensions:
                    continue
                try:
                    if item.stat().st_size >= min_size_bytes:
                        all_found_paths.add(str(path))
                        has_models = True
                        break  # Found model, no need to check other files
                except Exception:
                    pass
        
        # Recurse into subdirectories
        for item in items:
            if item.is_dir():
                try:
                    universal_scan_dir(item, depth + 1)
                except Exception:
                    pass
    
    # Start universal scan from NAS root
    universal_scan_dir(root, 0)
    
    # Now categorize found paths based on KNOWN_CATEGORY_FOLDERS
    for category, subfolders in KNOWN_CATEGORY_FOLDERS.items():
        found_paths = set()
        
        # Check predefined paths first
        for sub in subfolders:
            base_path = root / sub
            if base_path.exists() and str(base_path) in all_found_paths:
                found_paths.add(str(base_path))
        
        # Add any other paths that match category patterns
        for path_str in all_found_paths:
            path_name = Path(path_str).name.lower()
            
            # Category-specific pattern matching
            if category == "checkpoints" and any(pattern in path_name for pattern in ["sd", "stable", "cascade"]):
                found_paths.add(path_str)
            elif category == "loras" and "lora" in path_name:
                found_paths.add(path_str)
            elif category == "vae" and "vae" in path_name:
                found_paths.add(path_str)
            elif category == "clip" and "clip" in path_name:
                found_paths.add(path_str)
            elif category == "controlnet" and any(pattern in path_name for pattern in ["controlnet", "cn", "ipadapter"]):
                found_paths.add(path_str)
            elif category == "diffusion_models" and any(pattern in path_name for pattern in ["diffusion", "unet", "style"]):
                found_paths.add(path_str)
            elif category == "upscale_models" and any(pattern in path_name for pattern in ["upscale", "supir", "apisr", "stablesr"]):
                found_paths.add(path_str)
            elif category == "embeddings" and "embed" in path_name:
                found_paths.add(path_str)
        
        if found_paths:
            path_map[category] = sorted(list(found_paths))
    
    # Add any remaining paths to a general "models" category
    categorized_paths = set()
    for category_paths in path_map.values():
        categorized_paths.update(category_paths)
    
    uncategorized_paths = all_found_paths - categorized_paths
    if uncategorized_paths:
        path_map["models"] = sorted(list(uncategorized_paths))

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


