# RU: Упрощенная версия автокэша — только одна нода для кеширования моделей
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

try:
    from .arena_auto_cache_simple import (
        NODE_CLASS_MAPPINGS as _map,
        NODE_DISPLAY_NAME_MAPPINGS as _names,
    )
    NODE_CLASS_MAPPINGS.update(_map)
    NODE_DISPLAY_NAME_MAPPINGS.update(_names)
    print("[ArenaAutoCache] Loaded simplified version - single node for model caching")
except Exception as e:  # noqa: BLE001
    print(f"[ArenaAutoCache] disabled: {e}")
