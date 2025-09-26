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
from types import ModuleType

_LOGGER = logging.getLogger(__name__)

# Initialize mappings
NODE_CLASS_MAPPINGS: dict[str, type] = {}
NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}
WEB_DIRECTORY = None

# Add current directory to Python path for imports
_current_dir = Path(__file__).parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

# Import only essential nodes
# Arena AutoCache v3.3.5
try:
    from autocache.arena_auto_cache_simple import NODE_CLASS_MAPPINGS as _autocache_mappings, NODE_DISPLAY_NAME_MAPPINGS as _autocache_display
    NODE_CLASS_MAPPINGS.update(_autocache_mappings)
    NODE_DISPLAY_NAME_MAPPINGS.update(_autocache_display)
    print("[Arena Suite] Loaded Arena AutoCache v3.3.5")
except Exception as e:
    print(f"[Arena Suite] Failed to load Arena AutoCache: {e}")

# Arena Make Tiles Segments
try:
    from legacy.arena_make_tiles_segs import NODE_CLASS_MAPPINGS as _legacy_mappings, NODE_DISPLAY_NAME_MAPPINGS as _legacy_display
    NODE_CLASS_MAPPINGS.update(_legacy_mappings)
    NODE_DISPLAY_NAME_MAPPINGS.update(_legacy_display)
    print("[Arena Suite] Loaded Arena Make Tiles Segments")
except Exception as e:
    print(f"[Arena Suite] Failed to load Arena Make Tiles Segments: {e}")

print(f"[Arena Suite] Successfully loaded {len(NODE_CLASS_MAPPINGS)} Arena nodes")

# Export the required mappings for ComfyUI
__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS", 
    "WEB_DIRECTORY",
]
