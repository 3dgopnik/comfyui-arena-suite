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

# Add the custom_nodes directory to Python path
_package_root = Path(__file__).parent
_custom_nodes_path = _package_root / "custom_nodes"
if _custom_nodes_path.exists() and str(_custom_nodes_path) not in sys.path:
    sys.path.insert(0, str(_custom_nodes_path))

# Import from the actual ComfyUI_Arena package
try:
    from ComfyUI_Arena import (
        NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS,
        WEB_DIRECTORY,
    )
    print("[Arena Suite] Successfully loaded Arena nodes")
except Exception as e:
    print(f"[Arena Suite] Failed to load Arena nodes: {e}")
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}
    WEB_DIRECTORY = None

# Export the required mappings for ComfyUI
__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS", 
    "WEB_DIRECTORY",
]
