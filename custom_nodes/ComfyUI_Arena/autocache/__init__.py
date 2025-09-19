# RU: Скелет автокэша — регистрации нод подтянутся из arena_auto_cache.py, если он реализован
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

try:
    from .arena_auto_cache import (
        NODE_CLASS_MAPPINGS as _map,
        NODE_DISPLAY_NAME_MAPPINGS as _names,
    )
    NODE_CLASS_MAPPINGS.update(_map)
    NODE_DISPLAY_NAME_MAPPINGS.update(_names)
except Exception as e:  # noqa: BLE001
    print(f"[ArenaAutoCache] disabled: {e}")
