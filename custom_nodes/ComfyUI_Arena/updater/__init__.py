# RU: Скелет обновлятора моделей, регистрации добавятся из arena_model_updater.py
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

try:
    from .arena_model_updater import (
        NODE_CLASS_MAPPINGS as _map,
        NODE_DISPLAY_NAME_MAPPINGS as _names,
    )
    NODE_CLASS_MAPPINGS.update(_map)
    NODE_DISPLAY_NAME_MAPPINGS.update(_names)
except Exception as e:  # noqa: BLE001
    print(f"[ArenaUpdater] disabled: {e}")
