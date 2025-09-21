"""RU: Единый пакет нод Arena для ComfyUI.

- legacy: перенос существующих нод без изменения логики
- autocache: рантайм‑патч путей моделей и LRU SSD‑кэш
- updater: обновление моделей с HF/CivitAI по манифесту

Идентификаторы — на английском, комментарии — на русском.
"""

from __future__ import annotations

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

# UI overlay removed for now. Keep WEB_DIRECTORY unset to avoid loading assets.
WEB_DIRECTORY = None
_LOGGER.info("[Arena] web overlay disabled (removed); see ROADMAP for future plans")

_SUBMODULES: list[ModuleType] = []

try:
    from . import legacy as _legacy  # RU: модуль устаревших узлов (совместимость)
except Exception as e:  # noqa: BLE001
    _LOGGER.warning("[Arena] legacy disabled: %s", e)
else:
    _SUBMODULES.append(_legacy)

try:  # RU: автокэш (в разработке?)
    from . import autocache as _autocache
except Exception as e:  # noqa: BLE001
    print(f"[Arena] autocache disabled: {e}")
else:
    _SUBMODULES.append(_autocache)

try:  # RU: обновление моделей (в разработке?)
    from . import updater as _updater
except Exception as e:  # noqa: BLE001
    print(f"[Arena] updater disabled: {e}")
else:
    _SUBMODULES.append(_updater)

for _module in _SUBMODULES:
    NODE_CLASS_MAPPINGS.update(getattr(_module, "NODE_CLASS_MAPPINGS", {}))
    NODE_DISPLAY_NAME_MAPPINGS.update(getattr(_module, "NODE_DISPLAY_NAME_MAPPINGS", {}))

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
