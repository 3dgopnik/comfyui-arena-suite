"""Ensure the Arena web assets are resolved from the repository root."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_web_directory_points_to_repo_root() -> None:
    """WEB_DIRECTORY should locate the shared web extension assets."""

    module = importlib.import_module("custom_nodes.ComfyUI_Arena")
    web_dir = Path(module.WEB_DIRECTORY)

    expected = PROJECT_ROOT / "web"
    assert web_dir.resolve() == expected.resolve()
    assert (web_dir / "extensions" / "arena_autocache.js").exists()
