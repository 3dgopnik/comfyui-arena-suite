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

# Import and register nodes from submodules
_SUBMODULES: list[ModuleType] = []

# Import autocache nodes
try:
    import autocache as _autocache
    _SUBMODULES.append(_autocache)
    print("[Arena Suite] Loaded autocache module")
except Exception as e:
    print(f"[Arena Suite] Failed to load autocache: {e}")

# Import legacy nodes
try:
    import legacy as _legacy
    _SUBMODULES.append(_legacy)
    print("[Arena Suite] Loaded legacy module")
except Exception as e:
    print(f"[Arena Suite] Failed to load legacy: {e}")

# Import updater nodes
try:
    import updater as _updater
    _SUBMODULES.append(_updater)
    print("[Arena Suite] Loaded updater module")
except Exception as e:
    print(f"[Arena Suite] Failed to load updater: {e}")

# Collect all node mappings from submodules
for _module in _SUBMODULES:
    NODE_CLASS_MAPPINGS.update(getattr(_module, "NODE_CLASS_MAPPINGS", {}))
    NODE_DISPLAY_NAME_MAPPINGS.update(getattr(_module, "NODE_DISPLAY_NAME_MAPPINGS", {}))

print(f"[Arena Suite] Successfully loaded {len(NODE_CLASS_MAPPINGS)} Arena nodes")

# Export the required mappings for ComfyUI
__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS", 
    "WEB_DIRECTORY",
]
