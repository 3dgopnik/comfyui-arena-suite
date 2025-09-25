from __future__ import annotations

VERSION = "3.0.0a0"

__all__ = [
    "VERSION",
]
"""RU: Единый пакет нод Arena для ComfyUI.

- legacy: перенос существующих нод без изменения логики
- autocache: рантайм‑патч путей моделей и LRU SSD‑кэш
- updater: обновление моделей с HF/CivitAI по манифесту

Идентификаторы — на английском, комментарии — на русском.
"""

import logging
from pathlib import Path
from types import ModuleType


_LOGGER = logging.getLogger(__name__)


def _resolve_web_directory() -> str | None:
    """Locate the actual web assets directory for the extension."""

    arena_root = Path(__file__).resolve()
    for parent in arena_root.parents:
        candidate = parent / "web"
        if (candidate / "extensions" / "arena_autocache.js").exists():
            return str(candidate)

    _LOGGER.warning("[Arena] web assets missing: expected web/extensions/arena_autocache.js")
    return None


NODE_CLASS_MAPPINGS: dict[str, type] = {}
NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}

# Enable web assets for ComfyUI integration
WEB_DIRECTORY = _resolve_web_directory()
if WEB_DIRECTORY:
    _LOGGER.info("[Arena] web assets loaded from: %s", WEB_DIRECTORY)
else:
    _LOGGER.warning("[Arena] web assets not found")

_SUBMODULES: list[ModuleType] = []

# Import legacy module
try:
    from . import legacy as _legacy  # RU: модуль устаревших узлов (совместимость)
    _SUBMODULES.append(_legacy)
    _LOGGER.info("[Arena] legacy module loaded successfully")
except Exception as e:  # noqa: BLE001
    _LOGGER.warning("[Arena] legacy disabled: %s", e)

# Import autocache module
try:
    from . import autocache as _autocache
    _SUBMODULES.append(_autocache)
    _LOGGER.info("[Arena] autocache module loaded successfully")
except Exception as e:  # noqa: BLE001
    _LOGGER.warning("[Arena] autocache disabled: %s", e)

# Import updater module
try:
    from . import updater as _updater
    _SUBMODULES.append(_updater)
    _LOGGER.info("[Arena] updater module loaded successfully")
except Exception as e:  # noqa: BLE001
    _LOGGER.warning("[Arena] updater disabled: %s", e)

for _module in _SUBMODULES:
    NODE_CLASS_MAPPINGS.update(getattr(_module, "NODE_CLASS_MAPPINGS", {}))
    NODE_DISPLAY_NAME_MAPPINGS.update(getattr(_module, "NODE_DISPLAY_NAME_MAPPINGS", {}))

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]