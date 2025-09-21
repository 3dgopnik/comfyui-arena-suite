from __future__ import annotations

import importlib
import json
import sys
import types
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MODULE_NAME = "custom_nodes.ComfyUI_Arena.autocache.arena_auto_cache"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "arena_ui_payload_shape.json"


def _to_shape(value: object) -> object:
    if isinstance(value, dict):
        return {key: _to_shape(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_to_shape(item) for item in value]
    if isinstance(value, bool):
        return "<bool>"
    if isinstance(value, int):
        return "<int>"
    if isinstance(value, float):
        return "<float>"
    if isinstance(value, str):
        return "<str>"
    if value is None:
        return "<null>"
    return f"<{type(value).__name__}>"


@pytest.fixture
def arena_ops_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> types.ModuleType:
    source_dir = tmp_path / "source"
    cache_dir = tmp_path / "cache"
    source_dir.mkdir()
    cache_dir.mkdir()
    (source_dir / "model.safetensors").write_text("payload", encoding="utf-8")

    folder_paths = types.ModuleType("folder_paths")

    def _get_folder_paths(category: str):
        if category in {"checkpoints", "loras"}:
            return [str(source_dir)]
        return []

    def _get_full_path(category: str, name: str):
        candidate = source_dir / name
        return str(candidate) if candidate.exists() else None

    folder_paths.get_folder_paths = _get_folder_paths  # type: ignore[attr-defined]
    folder_paths.get_full_path = _get_full_path  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "folder_paths", folder_paths)
    monkeypatch.setenv("ARENA_CACHE_ROOT", str(cache_dir))
    monkeypatch.setenv("ARENA_CACHE_ENABLE", "1")
    monkeypatch.setenv("ARENA_CACHE_VERBOSE", "0")

    sys.modules.pop(MODULE_NAME, None)
    module = importlib.import_module(MODULE_NAME)
    module._STALE_LOCK_SECONDS = 0.01

    yield module

    sys.modules.pop(MODULE_NAME, None)


def test_arena_ui_payload_matches_shape_snapshot(
    arena_ops_module: types.ModuleType,
) -> None:
    expected_shape = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    ops_node = arena_ops_module.ArenaAutoCacheOps()
    summary_json, warmup_json, trim_json = ops_node.run(
        "checkpoints",
        "checkpoints:model.safetensors",
        "",
        "checkpoints",
        "audit_then_warmup",
    )

    actual_shape = {
        "summary_json": _to_shape(json.loads(summary_json)),
        "warmup_json": _to_shape(json.loads(warmup_json)),
        "trim_json": _to_shape(json.loads(trim_json)),
    }

    assert actual_shape == expected_shape
