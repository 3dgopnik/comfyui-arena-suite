"""ComfyUI Arena Suite - Main entry point for ComfyUI custom nodes.

This package contains Arena nodes for ComfyUI including:
- AutoCache: SSD caching for models
- Legacy: Compatibility nodes
- Updater: Model updating functionality
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path


_LOGGER = logging.getLogger(__name__)

# Initialize mappings
NODE_CLASS_MAPPINGS: dict[str, type] = {}
NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}
WEB_DIRECTORY = "web"

# Add current directory to Python path for imports
_current_dir = Path(__file__).parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

# Import only essential nodes
# Arena AutoCache Base
try:
    from autocache.arena_auto_cache_simple import NODE_CLASS_MAPPINGS as _autocache_mappings
    from autocache.arena_auto_cache_simple import NODE_DISPLAY_NAME_MAPPINGS as _autocache_display
    NODE_CLASS_MAPPINGS.update(_autocache_mappings)
    NODE_DISPLAY_NAME_MAPPINGS.update(_autocache_display)
    print("[Arena Suite] Loaded Arena AutoCache Base")
except Exception as e:
    print(f"[Arena Suite] Failed to load Arena AutoCache: {e}")

# Arena Make Tiles Segments
try:
    from legacy.arena_make_tiles_segs import NODE_CLASS_MAPPINGS as _legacy_mappings
    from legacy.arena_make_tiles_segs import NODE_DISPLAY_NAME_MAPPINGS as _legacy_display
    NODE_CLASS_MAPPINGS.update(_legacy_mappings)
    NODE_DISPLAY_NAME_MAPPINGS.update(_legacy_display)
    print("[Arena Suite] Loaded Arena Make Tiles Segments")
except Exception as e:
    print(f"[Arena Suite] Failed to load Arena Make Tiles Segments: {e}")

print(f"[Arena Suite] Successfully loaded {len(NODE_CLASS_MAPPINGS)} Arena nodes")

# Initialize NAS paths early (hybrid auto-scan + YAML fallback)
def _initialize_arena_paths() -> None:
    try:
        import os
        import shutil
        from autocache.arena_path_manager import (
            get_nas_root,
            scan_nas_structure,
            register_paths_in_folder_paths,
            migrate_from_yaml,
            ensure_yaml_exists,
        )

        # 1) Read Arena config
        nas_root = get_nas_root()
        auto_scan = os.environ.get("ARENA_NAS_AUTO_SCAN", "1") in ("1", "true", "yes")

        # 2) Fallback: migrate from Electron YAML if Arena config is empty
        if not nas_root:
            electron_yaml = Path(
                "C:/Users/acherednikov/AppData/Local/Programs/@comfyorgcomfyui-electron/resources/ComfyUI/extra_model_paths.yaml"
            )
            if electron_yaml.exists():
                print("[Arena Suite] Migrating NAS root from extra_model_paths.yaml...")
                env_data = migrate_from_yaml(electron_yaml)
                if env_data.get("ARENA_NAS_ROOT"):
                    # Persist minimal env via arena node helper if present (best-effort)
                    try:
                        from autocache.arena_auto_cache_simple import _save_env_file  # type: ignore
                        _save_env_file(env_data)
                    except Exception:
                        pass
                    nas_root = env_data.get("ARENA_NAS_ROOT", "")

        # 3) Scan and register into folder_paths
        if nas_root and auto_scan:
            path_map = scan_nas_structure(nas_root)
            if path_map:
                count = sum(len(v) for v in path_map.values())
                registered = register_paths_in_folder_paths(path_map)
                print(f"[Arena Suite] NAS auto-scan: {count} paths discovered, {registered} registered")
            else:
                print("[Arena Suite] NAS auto-scan: no paths discovered")

        # 4) YAML template support (restore if missing)
        template_yaml = Path(__file__).parent / "config" / "extra_model_paths.yaml"
        electron_yaml = Path(
            "C:/Users/acherednikov/AppData/Local/Programs/@comfyorgcomfyui-electron/resources/ComfyUI/extra_model_paths.yaml"
        )

        if not template_yaml.exists() and electron_yaml.exists():
            try:
                template_yaml.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(electron_yaml, template_yaml)
                print(f"[Arena Suite] Saved YAML template to {template_yaml}")
            except Exception:
                pass

        # Restore YAML ONLY if Arena NAS is NOT configured (fallback mode)
        if not nas_root:
            ensure_yaml_exists(electron_yaml, template_yaml)
            print("[Arena Suite] Using YAML fallback mode (ARENA_NAS_ROOT not configured)")
        else:
            print(f"[Arena Suite] Using Arena NAS mode: {nas_root}")

    except Exception as e:
        print(f"[Arena Suite] Failed to initialize Arena NAS paths: {e}")


# Call initializer after node mappings are loaded
try:
    _initialize_arena_paths()
except Exception as e:
    print(f"[Arena Suite] Arena NAS init error: {e}")

# Export the required mappings for ComfyUI
__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
