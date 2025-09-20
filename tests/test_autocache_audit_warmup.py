from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MODULE_NAME = "custom_nodes.ComfyUI_Arena.autocache.arena_auto_cache"


class ArenaAutoCacheAuditWarmupFlowTest(unittest.TestCase):
    """Validate audit/warmup lifecycle using a temporary cache."""

    def setUp(self) -> None:  # noqa: D401 - unittest hook
        self.addCleanup(sys.modules.pop, MODULE_NAME, None)
        self.addCleanup(sys.modules.pop, "folder_paths", None)
        self.addCleanup(lambda: os.environ.pop("ARENA_CACHE_ROOT", None))
        self.addCleanup(lambda: os.environ.pop("ARENA_CACHE_ENABLE", None))
        self.addCleanup(lambda: os.environ.pop("ARENA_CACHE_VERBOSE", None))

    def _prepare_module(self, cache_root: Path, source_dir: Path):
        folder_paths = types.ModuleType("folder_paths")

        def _get_folder_paths(category: str):
            return [str(source_dir)] if category == "checkpoints" else []

        def _get_full_path(category: str, name: str):
            candidate = Path(source_dir) / name
            return str(candidate)

        folder_paths.get_folder_paths = _get_folder_paths  # type: ignore[attr-defined]
        folder_paths.get_full_path = _get_full_path  # type: ignore[attr-defined]
        sys.modules["folder_paths"] = folder_paths

        os.environ["ARENA_CACHE_ROOT"] = str(cache_root)
        os.environ["ARENA_CACHE_ENABLE"] = "1"
        os.environ["ARENA_CACHE_VERBOSE"] = "0"

        sys.modules.pop(MODULE_NAME, None)
        module = importlib.import_module(MODULE_NAME)
        module._STALE_LOCK_SECONDS = 0.01
        return module

    def test_audit_and_warmup_flow_with_workflow_items(self) -> None:
        with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as cache_dir:
            source_dir = Path(src_dir)
            cache_root = Path(cache_dir)
            model_file = source_dir / "model.safetensors"
            model_file.write_text("payload", encoding="utf-8")

            module = self._prepare_module(cache_root, source_dir)
            warmup_node = module.ArenaAutoCacheWarmup()
            audit_node = module.ArenaAutoCacheAudit()

            workflow_json = json.dumps(
                {
                    "nodes": [
                        {
                            "class_type": "CheckpointLoaderSimple",
                            "inputs": {"ckpt_name": "model.safetensors"},
                        }
                    ]
                }
            )
            items_spec = json.dumps({
                "items": ["checkpoints:missing.safetensors"],
                "skip_existing": True,
            })

            parsed = module.parse_items_spec(items_spec, workflow_json, "checkpoints")
            parsed_names = {(entry["category"], entry["name"]) for entry in parsed}
            self.assertEqual(
                parsed_names,
                {
                    ("checkpoints", "missing.safetensors"),
                    ("checkpoints", "model.safetensors"),
                },
            )

            audit_json, total, cached, missing = audit_node.run(items_spec, workflow_json, "checkpoints")
            audit_payload = json.loads(audit_json)
            statuses_before = {item["name"]: item["status"] for item in audit_payload["items"]}
            self.assertEqual(total, 2)
            self.assertEqual(cached, 0)
            self.assertEqual(missing, 2)
            self.assertEqual(statuses_before["model.safetensors"], "missing_cache")
            self.assertEqual(statuses_before["missing.safetensors"], "missing_source")

            warm_json, total_warm, warmed, copied, missing_warm, errors = warmup_node.run(
                items_spec, workflow_json, "checkpoints"
            )
            warm_payload = json.loads(warm_json)
            statuses_after_warmup = {item["name"]: item["status"] for item in warm_payload["items"]}
            self.assertEqual(total_warm, 2)
            self.assertEqual(warmed, 1)
            self.assertEqual(copied, 1)
            self.assertEqual(missing_warm, 1)
            self.assertEqual(errors, 0)
            self.assertEqual(statuses_after_warmup["model.safetensors"], "copied")
            self.assertEqual(statuses_after_warmup["missing.safetensors"], "missing_source")

            cache_file = cache_root / "checkpoints" / "model.safetensors"
            self.assertTrue(cache_file.exists())

            audit_json_after, total_after, cached_after, missing_after = audit_node.run(
                items_spec, workflow_json, "checkpoints"
            )
            audit_payload_after = json.loads(audit_json_after)
            statuses_after = {item["name"]: item["status"] for item in audit_payload_after["items"]}
            self.assertEqual(total_after, 2)
            self.assertEqual(cached_after, 1)
            self.assertEqual(missing_after, 1)
            self.assertEqual(statuses_after["model.safetensors"], "cached")
            self.assertEqual(statuses_after["missing.safetensors"], "missing_source")

            warm_json_second, total_second, warmed_second, copied_second, missing_second, errors_second = warmup_node.run(
                items_spec, workflow_json, "checkpoints"
            )
            warm_payload_second = json.loads(warm_json_second)
            statuses_second = {item["name"]: item["status"] for item in warm_payload_second["items"]}
            self.assertEqual(total_second, 2)
            self.assertEqual(warmed_second, 1)
            self.assertEqual(copied_second, 0)
            self.assertEqual(missing_second, 1)
            self.assertEqual(errors_second, 0)
            self.assertEqual(statuses_second["model.safetensors"], "cached")
            self.assertEqual(statuses_second["missing.safetensors"], "missing_source")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
