"""Tests for Arena web asset discovery logic."""

from __future__ import annotations

from pathlib import Path

import custom_nodes.ComfyUI_Arena as arena


def test_resolve_web_directory_prefers_repo_root() -> None:
    """The primary lookup should return the repository-level web folder."""

    module_root = Path(arena.__file__).resolve()
    expected = module_root.parents[2] / "web"

    assert Path(arena.WEB_DIRECTORY) == expected


def test_resolve_web_directory_fallback(monkeypatch) -> None:
    """The fallback should point to the package-local web directory when needed."""

    repo_web = Path(arena.WEB_DIRECTORY)
    package_web = Path(arena.__file__).resolve().parent / "web"
    original_exists = Path.exists

    def fake_exists(path: Path) -> bool:
        if path.name == "arena_autocache.js" and repo_web in path.parents:
            return False
        return original_exists(path)

    monkeypatch.setattr(Path, "exists", fake_exists, raising=False)

    resolved = Path(arena._resolve_web_directory())

    assert resolved == package_web
