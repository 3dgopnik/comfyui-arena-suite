"""Runtime configuration tests for Arena AutoCache."""

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


def _prepare_module(cache_root: Path, source_dir: Path, enable: bool = True):
    """RU: Собирает заглушку folder_paths и импортирует модуль кеша."""

    folder_paths = types.ModuleType("folder_paths")

    def _get_folder_paths(category: str):
        return [str(source_dir)] if category == "checkpoints" else []

    def _get_full_path(category: str, name: str):
        return str(Path(source_dir) / name)

    folder_paths.get_folder_paths = _get_folder_paths  # type: ignore[attr-defined]
    folder_paths.get_full_path = _get_full_path  # type: ignore[attr-defined]
    sys.modules["folder_paths"] = folder_paths

    os.environ["ARENA_CACHE_ROOT"] = str(cache_root)
    os.environ["ARENA_CACHE_ENABLE"] = "1" if enable else "0"
    os.environ["ARENA_CACHE_VERBOSE"] = "0"

    sys.modules.pop(MODULE_NAME, None)
    module = importlib.import_module(MODULE_NAME)
    module._STALE_LOCK_SECONDS = 0.1

    return module, folder_paths


def _cleanup_module(testcase: unittest.TestCase) -> None:
    """RU: Возвращает окружение и импорты в исходное состояние."""

    testcase.addCleanup(sys.modules.pop, MODULE_NAME, None)
    testcase.addCleanup(sys.modules.pop, "folder_paths", None)
    testcase.addCleanup(lambda: os.environ.pop("ARENA_CACHE_ROOT", None))
    testcase.addCleanup(lambda: os.environ.pop("ARENA_CACHE_ENABLE", None))
    testcase.addCleanup(lambda: os.environ.pop("ARENA_CACHE_VERBOSE", None))


class ArenaAutoCacheConfigRuntimeTest(unittest.TestCase):
    """RU: Проверяет, что рантайм-изменения настроек влияют на патч."""

    def test_runtime_update_refreshes_cache_root(self) -> None:
        with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as initial_root, tempfile.TemporaryDirectory() as new_root:
            module, folder_paths = _prepare_module(Path(initial_root), Path(src_dir))
            _cleanup_module(self)

            source_file = Path(src_dir) / "model.safetensors"
            source_file.write_text("data", encoding="utf-8")

            result = module.set_cache_settings(root=new_root, max_gb=5, enable=True, verbose=False)
            self.assertTrue(result["ok"])
            self.assertEqual(result["effective_root"], str(Path(new_root).resolve(strict=False)))

            resolved = folder_paths.get_full_path("checkpoints", "model.safetensors")  # type: ignore[attr-defined]
            expected_path = Path(new_root) / "checkpoints" / "model.safetensors"
            self.assertEqual(Path(resolved).resolve(strict=False), expected_path.resolve(strict=False))
            self.assertTrue(expected_path.exists())

            paths_list = folder_paths.get_folder_paths("checkpoints")  # type: ignore[attr-defined]
            first_path = Path(paths_list[0]).resolve(strict=False)
            expected_category_root = (Path(new_root) / "checkpoints").resolve(strict=False)
            self.assertEqual(first_path, expected_category_root)


class ArenaAutoCacheEnableToggleTest(unittest.TestCase):
    """RU: Проверяет отключение кеша и возврат оригинальных функций."""

    def test_disable_restores_original_folder_paths(self) -> None:
        with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as cache_root:
            module, folder_paths = _prepare_module(Path(cache_root), Path(src_dir))
            _cleanup_module(self)

            self.assertIsNot(folder_paths.get_folder_paths, module._orig_get_folder_paths)  # type: ignore[attr-defined]
            self.assertIsNot(folder_paths.get_full_path, module._orig_get_full_path)  # type: ignore[attr-defined]

            module.set_cache_settings(enable=False)

            self.assertIs(folder_paths.get_folder_paths, module._orig_get_folder_paths)  # type: ignore[attr-defined]
            self.assertIs(folder_paths.get_full_path, module._orig_get_full_path)  # type: ignore[attr-defined]

            stats_node = module.ArenaAutoCacheStats()
            stats_json, = stats_node.run("checkpoints")
            payload = json.loads(stats_json)
            self.assertFalse(payload["enabled"])


class ArenaAutoCacheStatsExTest(unittest.TestCase):
    """RU: Проверяет расширенную статистику и счётчики сессии."""

    def test_stats_ex_reports_session_counters(self) -> None:
        with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as cache_root:
            module, folder_paths = _prepare_module(Path(cache_root), Path(src_dir))
            _cleanup_module(self)

            source_file = Path(src_dir) / "model.safetensors"
            source_file.write_text("payload", encoding="utf-8")

            folder_paths.get_full_path("checkpoints", "model.safetensors")  # type: ignore[attr-defined]
            folder_paths.get_full_path("checkpoints", "model.safetensors")  # type: ignore[attr-defined]

            stats_node = module.ArenaAutoCacheStatsEx()
            stats_json, items, total_gb, cache_root_str, session_hits, session_misses, session_trims = stats_node.run("checkpoints")
            payload = json.loads(stats_json)

            self.assertEqual(items, payload["items"])
            self.assertEqual(Path(cache_root_str).resolve(strict=False), Path(payload["cache_root"]).resolve(strict=False))
            self.assertAlmostEqual(total_gb, payload["total_gb"])
            self.assertGreaterEqual(session_hits, 1)
            self.assertGreaterEqual(session_misses, 0)
            self.assertGreaterEqual(session_trims, 0)

            trim_node = module.ArenaAutoCacheTrim()
            trim_json, = trim_node.run("checkpoints")
            trim_payload = json.loads(trim_json)
            self.assertTrue(trim_payload["ok"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
