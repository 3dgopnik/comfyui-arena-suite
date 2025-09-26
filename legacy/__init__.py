"""Legacy Arena node exports.

This module optionally registers legacy nodes that depend on the
`ComfyUI-Impact-Pack` package. When the dependency is missing we keep ComfyUI
bootable and emit a warning so users know how to install the missing pack.
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Iterable

LOGGER = logging.getLogger(__name__)
IMPACT_REPO_URL = "https://github.com/ltdrdata/ComfyUI-Impact-Pack"
IMPACT_MISSING_MESSAGE = (
    "Impact Pack dependency missing: install it from "
    f"{IMPACT_REPO_URL} and ensure the `ComfyUI-Impact-Pack/modules` "
    "directory is available on PYTHONPATH. Legacy Arena nodes are disabled."
)

_IMPACT_CHECKED = False
_IMPACT_AVAILABLE = False


def _impact_module_dirs() -> Iterable[Path]:
    """Yield likely locations for the Impact Pack ``modules`` directory."""

    resolved = Path(__file__).resolve()
    parents = resolved.parents
    for depth in (2, 3, 4):
        if len(parents) > depth:
            candidate = parents[depth] / "ComfyUI-Impact-Pack" / "modules"
            yield candidate


def ensure_impact() -> bool:
    """Ensure the Impact Pack can be imported, logging guidance if missing."""

    global _IMPACT_CHECKED, _IMPACT_AVAILABLE
    if _IMPACT_CHECKED:
        return _IMPACT_AVAILABLE

    _IMPACT_CHECKED = True

    if importlib.util.find_spec("impact") is not None:
        _IMPACT_AVAILABLE = True
        return True

    for modules_dir in _impact_module_dirs():
        if not modules_dir.is_dir():
            continue
        modules_path = str(modules_dir)
        if modules_path not in sys.path:
            sys.path.append(modules_path)
        if importlib.util.find_spec("impact") is not None:
            _IMPACT_AVAILABLE = True
            return True

    LOGGER.warning(IMPACT_MISSING_MESSAGE)
    return False


IMPACT_AVAILABLE = ensure_impact()

if IMPACT_AVAILABLE:
    from .arena_make_tiles_segs import Arena_MakeTilesSegs

    NODE_CLASS_MAPPINGS = {
        "Arena_MakeTilesSegs": Arena_MakeTilesSegs
    }
    NODE_DISPLAY_NAME_MAPPINGS = {
        "Arena_MakeTilesSegs": "🅰️ Arena Make Tiles Segments"
    }
else:
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}


__all__ = [
    "IMPACT_AVAILABLE",
    "IMPACT_MISSING_MESSAGE",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "ensure_impact",
]
