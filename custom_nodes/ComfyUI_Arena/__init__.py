"""RU: Единый пакет нод Arena для ComfyUI.
- legacy: перенос существующих нод без изменений логики
- autocache: рантайм-патч путей моделей и LRU SSD-кеш
- updater: обновление моделей с HF/CivitAI по манифесту

Идентификаторы — на английском, комментарии — на русском.
"""

from .legacy import __init__ as _legacy_init  # noqa: F401  # RU: импортирует NODE_CLASS_MAPPINGS

# RU: Попробуем подгрузить WIP-модули, но не упадём, если их нет
try:  # RU: автокэш (необязателен)
    from .autocache import __init__ as _autocache_init  # noqa: F401
except Exception as e:  # noqa: BLE001
    print(f"[Arena] autocache disabled: {e}")

try:  # RU: обновлятор (необязателен)
    from .updater import __init__ as _updater_init  # noqa: F401
except Exception as e:  # noqa: BLE001
    print(f"[Arena] updater disabled: {e}")
