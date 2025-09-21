"""ComfyUI Arena Suite package initializer.

Registers node classes from submodules and exposes WEB_DIRECTORY so the
front‑end can load web extensions (e.g., arena_autocache.js).
"""

from __future__ import annotations

import logging
from pathlib import Path
from types import ModuleType


_LOGGER = logging.getLogger(__name__)


def _resolve_web_directory() -> str | None:
    """Locate the actual web assets directory for the extension.

    Looks upwards from this file for a `web/extensions/arena_autocache.js`.
    Falls back to a module‑local `web/` directory if present.
    """

    module_file = Path(__file__).resolve()
    for parent in module_file.parents:
        candidate = parent / "web"
        if (candidate / "extensions" / "arena_autocache.js").exists():
            return str(candidate)

    # Fallback to module‑local web directory if it exists
    module_web = module_file.parent / "web"
    if (module_web / "extensions" / "arena_autocache.js").exists():
        return str(module_web)

    _LOGGER.warning(
        "[Arena] web assets not found: expected web/extensions/arena_autocache.js"
    )
    return None


NODE_CLASS_MAPPINGS: dict[str, type] = {}
NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}

WEB_DIRECTORY = _resolve_web_directory()

_SUBMODULES: list[ModuleType] = []

# Legacy is optional and may require external packs; do not block package import
try:
    from . import legacy as _legacy  # type: ignore
except Exception as e:  # noqa: BLE001
    _LOGGER.warning("[Arena] legacy disabled: %s", e)
else:
    _SUBMODULES.append(_legacy)

# Autocache subpackage
try:
    from . import autocache as _autocache  # type: ignore
except Exception as e:  # noqa: BLE001
    print(f"[Arena] autocache disabled: {e}")
else:
    _SUBMODULES.append(_autocache)

# Updater subpackage
try:
    from . import updater as _updater  # type: ignore
except Exception as e:  # noqa: BLE001
    print(f"[Arena] updater disabled: {e}")
else:
    _SUBMODULES.append(_updater)

for _module in _SUBMODULES:
    NODE_CLASS_MAPPINGS.update(getattr(_module, "NODE_CLASS_MAPPINGS", {}))
    NODE_DISPLAY_NAME_MAPPINGS.update(
        getattr(_module, "NODE_DISPLAY_NAME_MAPPINGS", {})
    )

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]

