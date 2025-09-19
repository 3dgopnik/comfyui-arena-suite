"""RU: Адаптер для импорта пакета comfyui-arena-suite в ComfyUI."""

from importlib import import_module as _import_module

_arena_module = _import_module(".custom_nodes.ComfyUI_Arena", __name__)

_export_names = getattr(_arena_module, "__all__", None)
if _export_names is None:
    _export_names = [name for name in dir(_arena_module) if not name.startswith("_")]

globals().update({name: getattr(_arena_module, name) for name in _export_names})
__all__ = tuple(_export_names)

# RU: подчистим временные переменные, чтобы не светились наружу
for _name in ("_import_module", "_arena_module", "_export_names"):
    globals().pop(_name, None)
del _name
