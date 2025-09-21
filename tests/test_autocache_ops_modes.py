"""Mode selection tests for the Arena AutoCache Ops node."""

from __future__ import annotations

import contextlib
import importlib
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


MODULE_NAME = "custom_nodes.ComfyUI_Arena.autocache.arena_auto_cache"


class ArenaAutoCacheOpsModeSelectionTest(unittest.TestCase):
    """Verify that Ops mode choices execute the expected operations."""

    def setUp(self) -> None:  # noqa: D401 - unittest hook description inherited
        self.addCleanup(sys.modules.pop, MODULE_NAME, None)
        self.addCleanup(sys.modules.pop, "folder_paths", None)
        self.addCleanup(lambda: os.environ.pop("ARENA_CACHE_ROOT", None))
        self.addCleanup(lambda: os.environ.pop("ARENA_CACHE_ENABLE", None))
        self.addCleanup(lambda: os.environ.pop("ARENA_CACHE_VERBOSE", None))

    def _prepare_module(self):
        folder_paths = types.ModuleType("folder_paths")
        folder_paths.get_folder_paths = lambda category: []  # type: ignore[attr-defined]
        folder_paths.get_full_path = lambda category, name: name  # type: ignore[attr-defined]
        sys.modules["folder_paths"] = folder_paths

        cache_dir = tempfile.TemporaryDirectory()
        self.addCleanup(cache_dir.cleanup)
        os.environ["ARENA_CACHE_ROOT"] = cache_dir.name
        os.environ["ARENA_CACHE_ENABLE"] = "1"
        os.environ["ARENA_CACHE_VERBOSE"] = "0"

        sys.modules.pop(MODULE_NAME, None)
        return importlib.import_module(MODULE_NAME)

    def _patch_ops_dependencies(self, module, log):
        stack = contextlib.ExitStack()
        cache_root = module._settings.root.as_posix()

        def audit_stub(items, workflow_json, default_category):
            log.append(("audit", items, workflow_json, default_category))
            payload = {
                "ok": True,
                "items": [],
                "timings": {"duration_seconds": 0.1},
            }
            return {
                "payload": payload,
                "json": json.dumps(payload, ensure_ascii=False, indent=2),
                "items": [],
                "total": 1,
                "cached": 1,
                "missing": 0,
                "timings": {"duration_seconds": 0.1},
            }

        def warmup_stub(items, workflow_json, default_category):
            log.append(("warmup", items, workflow_json, default_category))
            payload = {
                "ok": True,
                "note": "warmup-ok",
                "counts": {
                    "total": 2,
                    "warmed": 2,
                    "copied": 2,
                    "missing": 0,
                    "errors": 0,
                },
                "items": [],
                "timings": {"duration_seconds": 0.2},
            }
            return {
                "payload": payload,
                "json": json.dumps(payload, ensure_ascii=False, indent=2),
                "total": 2,
                "warmed": 2,
                "copied": 2,
                "missing": 0,
                "errors": 0,
                "timings": {"duration_seconds": 0.2},
            }

        def trim_stub(category):
            log.append(("trim", category))
            return {
                "payload": {
                    "ok": True,
                    "note": "trim-ok",
                    "category": category,
                    "timings": {"duration_seconds": 0.3},
                }
            }

        def stats_stub(category):
            log.append(("stats", category))
            payload = {
                "ok": True,
                "items": [],
                "total_bytes": 0,
                "total_gb": 0.0,
                "max_size_gb": 0,
            }
            return {
                "payload": payload,
                "items": 0,
                "total_gb": 0.0,
                "total_bytes": 0,
                "max_size_gb": 0,
                "cache_root": cache_root,
                "session_hits": 0,
                "session_misses": 0,
                "session_trims": 0,
            }

        stack.enter_context(mock.patch.object(module, "audit_items", side_effect=audit_stub))
        stack.enter_context(mock.patch.object(module, "warmup_items", side_effect=warmup_stub))
        stack.enter_context(mock.patch.object(module, "trim_category", side_effect=trim_stub))
        stack.enter_context(mock.patch.object(module, "collect_stats", side_effect=stats_stub))
        stack.enter_context(
            mock.patch.object(module, "_extract_benchmark_candidates", return_value=[])
        )
        stack.enter_context(
            mock.patch.object(
                module,
                "_benchmark_cache_entries",
                return_value={"requested_samples": 0, "read_samples": 0},
            )
        )
        return stack

    def test_default_mode_runs_audit_and_warmup(self) -> None:
        module = self._prepare_module()
        ops = module.ArenaAutoCacheOps()
        log: list[tuple[object, ...]] = []

        with self._patch_ops_dependencies(module, log):
            summary_json, warm_json, trim_json = ops.run(
                "checkpoints", "", "", "checkpoints", ""
            )

        actions = {entry[0] for entry in log}
        self.assertIn("audit", actions)
        self.assertIn("warmup", actions)
        self.assertNotIn("trim", actions)

        warm_payload = json.loads(warm_json)
        self.assertEqual(warm_payload["note"], "warmup-ok")

        trim_payload = json.loads(trim_json)
        self.assertEqual(trim_payload["note"], "trim skipped")

        summary = json.loads(summary_json)
        self.assertIn("Mode: audit_then_warmup", summary["ui"]["details"])

    def test_audit_only_mode_skips_warmup_and_trim(self) -> None:
        module = self._prepare_module()
        ops = module.ArenaAutoCacheOps()
        log: list[tuple[object, ...]] = []

        with self._patch_ops_dependencies(module, log):
            summary_json, warm_json, trim_json = ops.run(
                "checkpoints", "", "", "checkpoints", "audit"
            )

        actions = {entry[0] for entry in log}
        self.assertIn("audit", actions)
        self.assertNotIn("warmup", actions)
        self.assertNotIn("trim", actions)

        warm_payload = json.loads(warm_json)
        self.assertEqual(warm_payload["note"], "warmup skipped")

        trim_payload = json.loads(trim_json)
        self.assertEqual(trim_payload["note"], "trim skipped")

        summary = json.loads(summary_json)
        self.assertIn("Mode: audit", summary["ui"]["details"])

    def test_warmup_only_mode_skips_audit_and_trim(self) -> None:
        module = self._prepare_module()
        ops = module.ArenaAutoCacheOps()
        log: list[tuple[object, ...]] = []

        with self._patch_ops_dependencies(module, log):
            summary_json, warm_json, trim_json = ops.run(
                "checkpoints", "", "", "checkpoints", "warmup"
            )

        actions = {entry[0] for entry in log}
        self.assertIn("warmup", actions)
        self.assertNotIn("audit", actions)
        self.assertNotIn("trim", actions)

        warm_payload = json.loads(warm_json)
        self.assertEqual(warm_payload["note"], "warmup-ok")

        trim_payload = json.loads(trim_json)
        self.assertEqual(trim_payload["note"], "trim skipped")

        summary = json.loads(summary_json)
        self.assertIn("Mode: warmup", summary["ui"]["details"])

    def test_trim_mode_runs_only_trim(self) -> None:
        module = self._prepare_module()
        ops = module.ArenaAutoCacheOps()
        log: list[tuple[object, ...]] = []

        with self._patch_ops_dependencies(module, log):
            summary_json, warm_json, trim_json = ops.run(
                "checkpoints", "", "", "checkpoints", "trim"
            )

        actions = {entry[0] for entry in log}
        self.assertIn("trim", actions)
        self.assertNotIn("audit", actions)
        self.assertNotIn("warmup", actions)

        warm_payload = json.loads(warm_json)
        self.assertEqual(warm_payload["note"], "warmup skipped")

        trim_payload = json.loads(trim_json)
        self.assertEqual(trim_payload["note"], "trim-ok")

        summary = json.loads(summary_json)
        self.assertIn("Mode: trim", summary["ui"]["details"])


if __name__ == "__main__":  # pragma: no cover - unittest main hook
    unittest.main()

