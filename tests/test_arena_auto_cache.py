"""Regression tests for Arena AutoCache utilities."""

from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class ArenaAutoCacheStaleLockTest(unittest.TestCase):
    """Verify stale `.copying` locks are cleaned up and cache refreshes."""

    def test_stale_lock_cleanup_refreshes_cache_entry(self) -> None:
        category = "checkpoints"
        filename = "model.safetensors"

        with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as cache_root:
            src_path = Path(src_dir) / filename
            src_path.parent.mkdir(parents=True, exist_ok=True)
            src_path.write_text("fresh-data", encoding="utf-8")

            # Prepare stubbed ComfyUI folder_paths module for patching.
            folder_paths = types.ModuleType("folder_paths")

            def _get_folder_paths(cat: str):
                return [src_dir] if cat == category else []

            def _get_full_path(cat: str, name: str):
                return str(Path(src_dir) / name)

            folder_paths.get_folder_paths = _get_folder_paths  # type: ignore[attr-defined]
            folder_paths.get_full_path = _get_full_path  # type: ignore[attr-defined]
            sys.modules["folder_paths"] = folder_paths
            self.addCleanup(sys.modules.pop, "folder_paths", None)

            os.environ["ARENA_CACHE_ENABLE"] = "1"
            os.environ["ARENA_CACHE_ROOT"] = cache_root
            os.environ["ARENA_CACHE_VERBOSE"] = "0"
            self.addCleanup(lambda: os.environ.pop("ARENA_CACHE_ENABLE", None))
            self.addCleanup(lambda: os.environ.pop("ARENA_CACHE_ROOT", None))
            self.addCleanup(lambda: os.environ.pop("ARENA_CACHE_VERBOSE", None))

            module_name = "custom_nodes.ComfyUI_Arena.autocache.arena_auto_cache"
            sys.modules.pop(module_name, None)
            self.addCleanup(sys.modules.pop, module_name, None)
            arena_auto_cache = importlib.import_module(module_name)

            # Speed up tests by considering locks stale almost immediately.
            arena_auto_cache._STALE_LOCK_SECONDS = 0.1

            cache_dir = Path(cache_root) / category
            cache_dir.mkdir(parents=True, exist_ok=True)
            dst_path = cache_dir / filename
            dst_path.write_text("stale-data", encoding="utf-8")
            lock_path = dst_path.with_suffix(dst_path.suffix + ".copying")
            lock_path.touch()
            old_timestamp = time.time() - 10
            os.utime(lock_path, (old_timestamp, old_timestamp))

            # First request after crash: stale lock should be removed and cache recopied.
            resolved = folder_paths.get_full_path(category, filename)  # type: ignore[attr-defined]
            self.assertEqual(resolved, str(dst_path))
            self.assertFalse(lock_path.exists())
            self.assertEqual(dst_path.read_text(encoding="utf-8"), "fresh-data")

            # Cache index must track the refreshed entry.
            index_path = cache_dir / ".arena_cache_index.json"
            self.assertTrue(index_path.exists())
            index = json.loads(index_path.read_text("utf-8"))
            self.assertIn(filename, index.get("items", {}))

            # Subsequent requests should keep returning the cache path without recreating locks.
            second_resolved = folder_paths.get_full_path(category, filename)  # type: ignore[attr-defined]
            self.assertEqual(second_resolved, str(dst_path))
            self.assertFalse(dst_path.with_suffix(dst_path.suffix + ".copying").exists())


if __name__ == "__main__":  # pragma: no cover - unittest main hook
    unittest.main()
