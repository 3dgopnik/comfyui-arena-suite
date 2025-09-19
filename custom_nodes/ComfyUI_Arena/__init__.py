"""RU: Единый пакет нод Arena для ComfyUI.
- legacy: перенос существующих нод без изменений логики
- autocache: рантайм-патч путей моделей и LRU SSD-кеш
- updater: обновление моделей с HF/CivitAI по манифесту

Идентификаторы — на английском, комментарии — на русском.
"""

from __future__ import annotations

from types import ModuleType

NODE_CLASS_MAPPINGS: dict[str, type] = {}
NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}

_SUBMODULES: list[ModuleType] = []

from . import legacy as _legacy  # RU: импортирует обязательные ноды

_SUBMODULES.append(_legacy)

# RU: Попробуем подгрузить WIP-модули, но не упадём, если их нет
try:  # RU: автокэш (необязателен)
    from . import autocache as _autocache
except Exception as e:  # noqa: BLE001
    print(f"[Arena] autocache disabled: {e}")
else:
    _SUBMODULES.append(_autocache)

try:  # RU: обновлятор (необязателен)
    from . import updater as _updater
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
]
