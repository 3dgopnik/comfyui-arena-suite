"""Web overlay is currently disabled; WEB_DIRECTORY should be None."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest import mock

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


MODULE_NAME = "custom_nodes.ComfyUI_Arena"


def _import_fresh_arena_module():
    sys.modules.pop(MODULE_NAME, None)
    return importlib.import_module(MODULE_NAME)


def test_web_directory_is_none() -> None:
    """WEB_DIRECTORY should be None when overlay is disabled/removed."""

    module = _import_fresh_arena_module()
    assert getattr(module, "WEB_DIRECTORY", None) is None


def test_module_exports_without_web_dir() -> None:
    module = _import_fresh_arena_module()
    assert isinstance(module.NODE_CLASS_MAPPINGS, dict)
    assert isinstance(module.NODE_DISPLAY_NAME_MAPPINGS, dict)
