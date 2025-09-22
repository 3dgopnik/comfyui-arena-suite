"""Regression tests for Arena AutoCache utilities."""

from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path
from typing import Mapping


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
            arena_auto_cache.register_workflow_items(
                f"{category}:{filename}",
                "",
                category,
            )

            cache_dir = Path(cache_root) / category
            cache_dir.mkdir(parents=True, exist_ok=True)
            dst_path = cache_dir / filename
            dst_path.write_text("stale-data", encoding="utf-8")
            lock_path = dst_path.with_suffix(dst_path.suffix + ".copying")
            lock_path.touch()
            old_timestamp = time.time() - 10
            os.utime(lock_path, (old_timestamp, old_timestamp))

            # First request after crash: returns source while copy job runs in background.
            resolved = folder_paths.get_full_path(category, filename)  # type: ignore[attr-defined]
            self.assertEqual(resolved, str(src_path))
            self.assertTrue(arena_auto_cache.wait_for_copy_queue(timeout=5.0))
            self.assertFalse(lock_path.exists())
            self.assertEqual(dst_path.read_text(encoding="utf-8"), "fresh-data")

            # Cache index must track the refreshed entry.
            index_path = cache_dir / ".arena_cache_index.json"
            self.assertTrue(index_path.exists())
            index = json.loads(index_path.read_text("utf-8"))
            self.assertIn(filename, index.get("items", {}))

            # Subsequent requests should return the cache path without recreating locks.
            second_resolved = folder_paths.get_full_path(category, filename)  # type: ignore[attr-defined]
            self.assertEqual(Path(second_resolved).resolve(strict=False), dst_path.resolve(strict=False))
            self.assertFalse(dst_path.with_suffix(dst_path.suffix + ".copying").exists())


class ArenaAutoCacheMissingFileTest(unittest.TestCase):
    """Verify cache falls back to the source when locks disappear without files."""

    def test_lock_removed_without_cache_file_prefers_source(self) -> None:
        category = "loras"
        filename = "style.safetensors"

        with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as cache_root:
            src_path = Path(src_dir) / filename
            src_path.parent.mkdir(parents=True, exist_ok=True)
            src_path.write_text("authoritative-data", encoding="utf-8")

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

            arena_auto_cache._STALE_LOCK_SECONDS = 30

            cache_dir = Path(cache_root) / category
            cache_dir.mkdir(parents=True, exist_ok=True)
            dst_path = cache_dir / filename
            dst_path.write_text("old-cache", encoding="utf-8")
            lock_path = dst_path.with_suffix(dst_path.suffix + ".copying")
            lock_path.touch()

            def drop_lock_and_file() -> None:
                time.sleep(0.1)
                if dst_path.exists():
                    dst_path.unlink()
                if lock_path.exists():
                    lock_path.unlink()

            dropper = threading.Thread(target=drop_lock_and_file)
            dropper.start()
            try:
                resolved = folder_paths.get_full_path(category, filename)  # type: ignore[attr-defined]
            finally:
                dropper.join()

            self.assertEqual(resolved, str(src_path))
            self.assertFalse(dst_path.exists())
            self.assertFalse(lock_path.exists())

            index_path = cache_dir / ".arena_cache_index.json"
            self.assertTrue(index_path.exists())
            index = json.loads(index_path.read_text("utf-8"))
            self.assertEqual(index.get("last_op"), "MISS")
            self.assertNotIn(filename, index.get("items", {}))


class ArenaAutoCacheLocalizationFallbackTest(unittest.TestCase):
    """Ensure localization environment variables are ignored and English labels are used."""

    def test_localization_env_vars_are_ignored(self) -> None:
        module_name = "custom_nodes.ComfyUI_Arena.autocache.arena_auto_cache"

        old_arena_lang = os.environ.get("ARENA_LANG")
        if old_arena_lang is not None:
            self.addCleanup(lambda value=old_arena_lang: os.environ.__setitem__("ARENA_LANG", value))
        else:
            self.addCleanup(lambda: os.environ.pop("ARENA_LANG", None))
        os.environ["ARENA_LANG"] = "ru"

        old_comfyui_lang = os.environ.get("COMFYUI_LANG")
        if old_comfyui_lang is not None:
            self.addCleanup(lambda value=old_comfyui_lang: os.environ.__setitem__("COMFYUI_LANG", value))
        else:
            self.addCleanup(lambda: os.environ.pop("COMFYUI_LANG", None))
        os.environ["COMFYUI_LANG"] = "de"

        sys.modules.pop(module_name, None)
        self.addCleanup(sys.modules.pop, module_name, None)
        arena_auto_cache = importlib.import_module(module_name)

        self.assertFalse(hasattr(arena_auto_cache, "ARENA_LANG"))
        self.assertEqual(
            arena_auto_cache.t("node.dashboard"),
            "🅰️ Arena AutoCache: Dashboard",
        )
        self.assertEqual(
            arena_auto_cache.t("input.cache_root"),
            "Cache root directory",
        )


class ArenaAutoCacheAsyncCopyTest(unittest.TestCase):
    """Verify that copy requests return immediately while the worker performs the sync."""

    def test_background_worker_copies_without_blocking(self) -> None:
        category = "checkpoints"
        filename = "model.safetensors"

        with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as cache_root:
            src_path = Path(src_dir) / filename
            src_path.write_text("async-data", encoding="utf-8")

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

            arena_auto_cache.register_workflow_items(
                f"{category}:{filename}",
                "",
                category,
            )

            original_copy = arena_auto_cache._copy_into_cache_lru
            worker_started = threading.Event()

            def _slow_copy(
                src: Path,
                dst: Path,
                cat: str,
                *,
                context: Mapping[str, object] | None = None,
            ) -> None:
                worker_started.set()
                time.sleep(0.2)
                original_copy(src, dst, cat, context=context)

            arena_auto_cache._copy_into_cache_lru = _slow_copy
            self.addCleanup(lambda: setattr(arena_auto_cache, "_copy_into_cache_lru", original_copy))

            folder_paths = sys.modules["folder_paths"]
            start = time.perf_counter()
            resolved = folder_paths.get_full_path(category, filename)  # type: ignore[attr-defined]
            duration = time.perf_counter() - start

            self.assertEqual(resolved, str(src_path))
            self.assertLess(duration, 0.15)
            self.assertTrue(worker_started.wait(timeout=1.0))
            self.assertTrue(arena_auto_cache.wait_for_copy_queue(timeout=5.0))

            cache_path = Path(cache_root) / category / filename
            self.assertTrue(cache_path.exists())
            self.assertEqual(cache_path.read_text(encoding="utf-8"), "async-data")

            cached_resolved = folder_paths.get_full_path(category, filename)  # type: ignore[attr-defined]
            self.assertEqual(Path(cached_resolved).resolve(strict=False), cache_path.resolve(strict=False))


class ArenaAutoCacheCopyNotificationTest(unittest.TestCase):
    """Ensure copy lifecycle notifications fire even when verbose logging is disabled."""

    def test_copy_events_emitted_without_verbose(self) -> None:
        module_name = "custom_nodes.ComfyUI_Arena.autocache.arena_auto_cache"
        category = "checkpoints"
        filename = "model.safetensors"

        with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as cache_dir:
            src_path = Path(src_dir) / filename
            src_path.write_text("payload", encoding="utf-8")

            os.environ["ARENA_CACHE_ENABLE"] = "1"
            os.environ["ARENA_CACHE_ROOT"] = cache_dir
            os.environ["ARENA_CACHE_VERBOSE"] = "0"
            self.addCleanup(lambda: os.environ.pop("ARENA_CACHE_ENABLE", None))
            self.addCleanup(lambda: os.environ.pop("ARENA_CACHE_ROOT", None))
            self.addCleanup(lambda: os.environ.pop("ARENA_CACHE_VERBOSE", None))

            sys.modules.pop(module_name, None)
            self.addCleanup(sys.modules.pop, module_name, None)
            module = importlib.import_module(module_name)

            settings = module.get_settings()
            if isinstance(settings, dict):
                self.assertFalse(settings.get("verbose"))
            else:
                self.assertFalse(settings.verbose)

            original_notify = module._notify_copy_event
            events: list[tuple[str, dict[str, object]]] = []

            def _fake_notify(
                event: str,
                *,
                category: str | None = None,
                src: Path | None = None,
                dst: Path | None = None,
                context: Mapping[str, object] | None = None,
                note: str | None = None,
            ) -> None:
                events.append(
                    (
                        event,
                        {
                            "category": category,
                            "src": src,
                            "dst": dst,
                            "context": context,
                            "note": note,
                        },
                    )
                )

            module._notify_copy_event = _fake_notify
            self.addCleanup(lambda: setattr(module, "_notify_copy_event", original_notify))

            cache_path = Path(cache_dir) / category / filename
            context_payload = {"node_id": "warmup-1"}

            module._copy_into_cache_lru(src_path, cache_path, category, context=context_payload)
            self.assertTrue(cache_path.exists())

            module._copy_into_cache_lru(src_path, cache_path, category, context=context_payload)

            event_names = [event for event, _ in events]
            self.assertEqual(
                event_names,
                [
                    module.COPY_EVENT_STARTED,
                    module.COPY_EVENT_COMPLETED,
                    module.COPY_EVENT_SKIPPED,
                ],
            )

            for _, details in events:
                self.assertEqual(details["context"], context_payload)

            self.assertEqual(events[-1][1]["note"], "exists")


if __name__ == "__main__":  # pragma: no cover - unittest main hook
    unittest.main()


