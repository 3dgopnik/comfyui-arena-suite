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
            audit_json, audit_total, cached, missing_count, summary_json = audit_node.run(
                "checkpoints:model.safetensors\nloras:style.safetensors",
                "",
                "checkpoints",
            )
            audit_payload = json.loads(audit_json)
            summary_payload = json.loads(summary_json)

            self.assertEqual(audit_total, 2)
            self.assertEqual(cached, 1)
            self.assertEqual(missing_count, 1)
            statuses = {item["name"]: item["status"] for item in audit_payload["items"]}
            self.assertEqual(statuses["model.safetensors"], "cached")
            self.assertEqual(statuses["style.safetensors"], "missing_source")
            self.assertIn("ui", summary_payload)

    def test_warmup_wrapper_emits_ui_and_timings(self) -> None:
        with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as cache_root:
            source_dir = Path(src_dir)
            cache_root_path = Path(cache_root)
            (source_dir / "model.safetensors").write_text("payload", encoding="utf-8")

            module = self._prepare_module(cache_root_path, source_dir)

            warmup_node = module.ArenaAutoCacheWarmup()
            report_json, total, warmed, copied, missing, errors = warmup_node.run(
                "checkpoints:model.safetensors",
                "",
                "checkpoints",
            )
            payload = json.loads(report_json)

            self.assertEqual(total, 1)
            self.assertEqual(warmed, 1)
            self.assertEqual(copied, 1)
            self.assertEqual(missing, 0)
            self.assertEqual(errors, 0)
            self.assertIn("ui", payload)
            self.assertIn("timings", payload)
            self.assertGreaterEqual(payload["timings"]["duration_seconds"], 0.0)

    def test_ops_warmup_mode_with_benchmark_respects_limits(self) -> None:
        with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as cache_root:
            source_dir = Path(src_dir)
            cache_root_path = Path(cache_root)
            data = b"x" * 4096
            (source_dir / "model.safetensors").write_bytes(data)

            module = self._prepare_module(cache_root_path, source_dir)
            ops_node = module.ArenaAutoCacheOps()

            benchmark_limit_mb = 0.001
            summary_json, warmup_json, trim_json = ops_node.run(
                "checkpoints",
                "checkpoints:model.safetensors",
                "",
                "checkpoints",
                "warmup",
                benchmark_samples=1,
                benchmark_read_mb=benchmark_limit_mb,
            )

            summary = json.loads(summary_json)
            warmup_payload = json.loads(warmup_json)
            trim_payload = json.loads(trim_json)

            self.assertEqual(warmup_payload["counts"]["warmed"], 1)
            self.assertEqual(trim_payload["note"], "trim skipped")
            self.assertEqual(summary["ui"]["headline"], "Arena Ops report")
            self.assertIn("Mode: warmup", summary["ui"]["details"])

            benchmark = summary["timings"].get("benchmark")
            self.assertIsInstance(benchmark, dict)
            expected_bytes = int(benchmark_limit_mb * 1024 * 1024)
            self.assertEqual(benchmark["read_samples"], 1)
            self.assertEqual(benchmark["bytes"], expected_bytes)
            self.assertGreaterEqual(benchmark["throughput_bytes_per_s"], 0.0)

    def test_ops_audit_then_warmup_combines_reports(self) -> None:
        with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as cache_root:
            source_dir = Path(src_dir)
            cache_root_path = Path(cache_root)
            (source_dir / "model.safetensors").write_text("payload", encoding="utf-8")

            module = self._prepare_module(cache_root_path, source_dir)
            ops_node = module.ArenaAutoCacheOps()

            items_spec = "\n".join(
                [
                    "checkpoints:model.safetensors",
                    "checkpoints:missing.safetensors",
                ]
            )

            summary_json, warmup_json, trim_json = ops_node.run(
                "checkpoints",
                items_spec,
                "",
                "checkpoints",
                "audit_then_warmup",
            )

            summary = json.loads(summary_json)
            warmup_payload = json.loads(warmup_json)
            trim_payload = json.loads(trim_json)

            self.assertEqual(trim_payload["note"], "trim skipped")
            self.assertEqual(warmup_payload["counts"]["warmed"], 1)
            timings = summary.get("timings", {})
            self.assertIn("audit", timings)
            self.assertIn("warmup", timings)
            self.assertIn("stats", timings)
            self.assertEqual(summary["ui"]["headline"], "Arena Ops report")
            detail_line = "Warmup warmed: 1/2"
            self.assertIn(detail_line, summary["ui"]["details"])

if __name__ == "__main__":  # pragma: no cover
    unittest.main()
