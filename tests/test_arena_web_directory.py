"""Ensure the Arena web assets are resolved from the repository root."""

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


def test_web_directory_points_to_repo_root() -> None:
    """WEB_DIRECTORY should locate the shared web extension assets."""

    module = _import_fresh_arena_module()
    web_dir = Path(module.WEB_DIRECTORY)

    expected = PROJECT_ROOT / "web"
    assert web_dir.resolve() == expected.resolve()
    assert (web_dir / "extensions" / "arena_autocache.js").exists()


def test_web_directory_missing_assets_logs_warning_and_returns_none(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """If the overlay assets are missing the module should not expose a fake path."""

    with mock.patch("pathlib.Path.exists", return_value=False):
        with caplog.at_level("WARNING", logger="custom_nodes.ComfyUI_Arena"):
            module = _import_fresh_arena_module()

    assert getattr(module, "WEB_DIRECTORY", None) is None
    assert "web assets missing" in caplog.text
