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


class ArenaAutoCacheParseItemsSpecTest(unittest.TestCase):
    """Validate unified item specification parsing."""

    def tearDown(self) -> None:  # noqa: D401 - unittest hook
        sys.modules.pop(MODULE_NAME, None)

    def test_parse_items_spec_merges_sources_and_deduplicates(self) -> None:
        module = importlib.import_module(MODULE_NAME)
        items = "\n".join([
            "loras:style.safetensors",
            "checkpoints:model.safetensors",
        ])
        workflow = json.dumps(
            {
                "nodes": [
                    {
                        "class_type": "CheckpointLoaderSimple",
                        "inputs": {"ckpt_name": "model.safetensors"},
                    },
                    {"class_type": "VAELoader", "inputs": {"vae_name": "vae.pt"}},
                    {"class_type": "LoraLoader", "inputs": {"lora_name": "style.safetensors"}},
                ]
            }
        )

        parsed = module.parse_items_spec(items, workflow, "checkpoints")

        self.assertEqual(
            parsed,
            [
                {"category": "loras", "name": "style.safetensors"},
                {"category": "checkpoints", "name": "model.safetensors"},
                {"category": "vae", "name": "vae.pt"},
            ],
        )


class ArenaAutoCacheWarmupAuditIntegrationTest(unittest.TestCase):
    """Integration tests for warmup/audit helpers operating on real files."""

    def setUp(self) -> None:
        self.addCleanup(sys.modules.pop, MODULE_NAME, None)
        self.addCleanup(sys.modules.pop, "folder_paths", None)
        self.addCleanup(lambda: os.environ.pop("ARENA_CACHE_ROOT", None))
        self.addCleanup(lambda: os.environ.pop("ARENA_CACHE_ENABLE", None))
        self.addCleanup(lambda: os.environ.pop("ARENA_CACHE_VERBOSE", None))

    def _prepare_module(self, cache_root: Path, source_dir: Path):
        folder_paths = types.ModuleType("folder_paths")

        def _get_folder_paths(category: str):
            if category in {"checkpoints", "loras"}:
                return [str(source_dir)]
            return []

        def _get_full_path(category: str, name: str):
            candidate = Path(source_dir) / name
            return str(candidate) if candidate.exists() else None

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

    def test_warmup_populates_cache_and_audit_reports_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as cache_root:
            source_dir = Path(src_dir)
            cache_root_path = Path(cache_root)
            (source_dir / "model.safetensors").write_text("payload", encoding="utf-8")

            module = self._prepare_module(cache_root_path, source_dir)

            warmup_node = module.ArenaAutoCacheWarmup()
            report_json, total, warmed, copied, missing, errors = warmup_node.run(
                "checkpoints:model.safetensors\nloras:style.safetensors",
                "",
                "checkpoints",
            )
            payload = json.loads(report_json)

            self.assertEqual(total, 2)
            self.assertEqual(warmed, 1)
            self.assertEqual(copied, 1)
            self.assertEqual(missing, 1)
            self.assertEqual(errors, 0)
            self.assertTrue(payload["ok"])

            cache_file = cache_root_path / "checkpoints" / "model.safetensors"
            self.assertTrue(cache_file.exists())

            audit_node = module.ArenaAutoCacheAudit()
            audit_json, audit_total, cached, missing_count = audit_node.run(
                "checkpoints:model.safetensors\nloras:style.safetensors",
                "",
                "checkpoints",
            )
            audit_payload = json.loads(audit_json)

            self.assertEqual(audit_total, 2)
            self.assertEqual(cached, 1)
            self.assertEqual(missing_count, 1)
            statuses = {item["name"]: item["status"] for item in audit_payload["items"]}
            self.assertEqual(statuses["model.safetensors"], "cached")
            self.assertEqual(statuses["style.safetensors"], "missing_source")

if __name__ == "__main__":  # pragma: no cover
    unittest.main()
