"""Tests for the Arena AutoCache web overlay integration."""

from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _require_overlay_asset() -> Path:
    """Resolve the Arena AutoCache overlay asset or skip the test suite."""

    candidate = PROJECT_ROOT / "web" / "extensions" / "arena_autocache.js"
    if candidate.is_file():
        return candidate

    try:
        import custom_nodes.ComfyUI_Arena as arena  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001 - best-effort discovery
        pytest.skip("Arena AutoCache overlay asset is unavailable (default and package lookup failed)")

    web_directory = getattr(arena, "WEB_DIRECTORY", None)
    if not web_directory:
        pytest.skip("Arena AutoCache overlay asset is unavailable (WEB_DIRECTORY not configured)")

    overlay_path = Path(web_directory) / "extensions" / "arena_autocache.js"
    if overlay_path.is_file():
        return overlay_path

    pytest.skip("Arena AutoCache overlay asset is unavailable (WEB_DIRECTORY lookup missing file)")


class ArenaAutoCacheOverlayLocalizationTest(unittest.TestCase):
    """Ensure localized output labels are normalized for the overlay."""

    def setUp(self) -> None:
        self.extension_path = _require_overlay_asset()

    def test_overlay_updates_with_localized_output_names(self) -> None:
        script = textwrap.dedent(
            """
            const fs = require('node:fs');
            const vm = require('node:vm');

            const sourcePath = process.argv[1];
            const source = fs.readFileSync(sourcePath, 'utf8');
            const importLine = 'import { app } from "/scripts/app.js";';
            const patched = source.replace(importLine, 'const app = globalThis.app;');

            const extensionHolder = { value: null };
            const sandbox = { console };
            sandbox.app = {
              registerExtension(ext) {
                extensionHolder.value = ext;
              },
            };
            sandbox.globalThis = sandbox;
            sandbox.window = sandbox;
            sandbox.global = sandbox;
            sandbox.self = sandbox;

            vm.createContext(sandbox);
            vm.runInContext(patched, sandbox, { filename: sourcePath });

            if (!extensionHolder.value) {
              throw new Error('Extension not registered');
            }

            const extension = extensionHolder.value;

            const dirtyCalls = [];
            const graph = {
              _nodes: [],
              getNodeById(id) {
                return this._nodes.find((node) => node.id === id) || null;
              },
              setDirtyCanvas(flagA, flagB) {
                dirtyCalls.push([flagA, flagB]);
              },
            };

            const graphApp = { graph };

            const node = {
              id: 1,
              constructor: { comfyClass: 'ArenaAutoCacheOps' },
              graph,
              size: [200, 140],
              boxcolor: '#101010',
              bgcolor: '#202020',
              color: '#f0f0f0',
              title_color: '#ffffff',
            };

            graph._nodes.push(node);

            extension.init(graphApp);

            const localizedOutputs = {
              'JSON сводки': '{"ok": true, "ui": { "headline": "Тест" }}',
              'Прогрев JSON': '{"counts": { "warmed": 5, "total": 5 }}',
              'Обрезка JSON': '{"trimmed": 1, "items": 1 }',
            };

            extension.onNodeOutputsUpdated({ '1': localizedOutputs });

            const result = {
              dirtyCalls: dirtyCalls.length,
              boxcolor: node.boxcolor,
              decorated: Boolean(node.__arenaAutoCacheDecorated),
            };

            console.log(JSON.stringify(result));
            """
        ).strip()

        completed = subprocess.run(
            ["node", "-e", script, str(self.extension_path)],
            check=True,
            capture_output=True,
            text=True,
        )

        output_lines = [line for line in completed.stdout.splitlines() if line.strip()]
        payload = json.loads(output_lines[-1])

        self.assertTrue(payload["decorated"])
        self.assertGreaterEqual(payload["dirtyCalls"], 1)
        self.assertEqual(payload["boxcolor"], "#2e7d32")

    def test_overlay_registers_when_app_is_delayed(self) -> None:
        script = textwrap.dedent(
            """
            const fs = require('node:fs');
            const vm = require('node:vm');

            const sourcePath = process.argv[1];
            const source = fs.readFileSync(sourcePath, 'utf8');
            const importLine = 'import { app } from "/scripts/app.js";';
            const patched = source.replace(importLine, 'const app = globalThis.app;');

            const extensionHolder = { value: null, calls: 0 };

            const sandbox = { console };
            sandbox.setTimeout = setTimeout;
            sandbox.clearTimeout = clearTimeout;
            sandbox.globalThis = sandbox;
            sandbox.window = sandbox;
            sandbox.global = sandbox;
            sandbox.self = sandbox;

            vm.createContext(sandbox);
            vm.runInContext(patched, sandbox, { filename: sourcePath });

            sandbox.setTimeout(() => {
              sandbox.app = {
                registerExtension(ext) {
                  extensionHolder.value = ext;
                  extensionHolder.calls += 1;
                },
              };
            }, 10);

            sandbox.setTimeout(() => {
              if (!extensionHolder.value) {
                throw new Error('Extension not registered after delay');
              }
              console.log(JSON.stringify({ registered: Boolean(extensionHolder.value), calls: extensionHolder.calls }));
            }, 120);
            """
        ).strip()

        completed = subprocess.run(
            ["node", "-e", script, str(self.extension_path)],
            check=True,
            capture_output=True,
            text=True,
        )

        output_lines = [line for line in completed.stdout.splitlines() if line.strip()]
        payload = json.loads(output_lines[-1])

        self.assertTrue(payload["registered"])
        self.assertEqual(payload["calls"], 1)

    def test_overlay_falls_back_to_execution_events(self) -> None:
        script = textwrap.dedent(
            """
            const fs = require('node:fs');
            const vm = require('node:vm');

            const sourcePath = process.argv[1];
            const source = fs.readFileSync(sourcePath, 'utf8');
            const importLine = 'import { app } from "/scripts/app.js";';
            const patched = source.replace(importLine, 'const app = globalThis.app;');

            function createSignal(label) {
              const listeners = new Set();
              return {
                label,
                listeners,
                removedCount: 0,
                addListener(cb) { this.listeners.add(cb); },
                removeListener(cb) {
                  if (this.listeners.delete(cb)) {
                    this.removedCount += 1;
                  }
                },
                emit(...args) {
                  for (const cb of Array.from(this.listeners)) {
                    cb(...args);
                  }
                },
              };
            }

            const extensionHolder = { value: null };

            const sandbox = { console };
            sandbox.app = {
              registerExtension(ext) {
                extensionHolder.value = ext;
              },
            };
            sandbox.globalThis = sandbox;
            sandbox.window = sandbox;
            sandbox.global = sandbox;
            sandbox.self = sandbox;

            vm.createContext(sandbox);
            vm.runInContext(patched, sandbox, { filename: sourcePath });

            if (!extensionHolder.value) {
              throw new Error('Extension not registered');
            }

            const extension = extensionHolder.value;

            const dirtyCalls = [];

            const firstSignal = createSignal('first');
            const firstGraph = {
              _nodes: [],
              onExecuted: firstSignal,
              getNodeById(id) {
                return this._nodes.find((node) => node.id === id) || null;
              },
              setDirtyCanvas(flagA, flagB) {
                dirtyCalls.push(['first', flagA, flagB]);
              },
            };

            const graphApp = { graph: firstGraph };

            const nodeA = {
              id: 1,
              constructor: { comfyClass: 'ArenaAutoCacheAudit' },
              graph: firstGraph,
              size: [220, 160],
              boxcolor: '#151515',
              bgcolor: '#252525',
              color: '#f5f5f5',
              title_color: '#ffffff',
            };
            firstGraph._nodes.push(nodeA);

            extension.init(graphApp);

            const outputsA = {
              summary_json: '{"ok": true, "ui": {"headline": "Audit"}}',
            };

            firstSignal.emit(nodeA, outputsA);

            const firstState = {
              listeners: firstSignal.listeners.size,
              removedCount: firstSignal.removedCount,
              nodeColor: nodeA.boxcolor,
              decorated: Boolean(nodeA.__arenaAutoCacheDecorated),
            };

            const secondSignal = createSignal('second');
            const secondGraph = {
              _nodes: [],
              onExecuted: secondSignal,
              getNodeById(id) {
                return this._nodes.find((node) => node.id === id) || null;
              },
              setDirtyCanvas(flagA, flagB) {
                dirtyCalls.push(['second', flagA, flagB]);
              },
            };

            const nodeB = {
              id: 2,
              constructor: { comfyClass: 'ArenaAutoCacheOps' },
              graph: secondGraph,
              size: [200, 140],
              boxcolor: '#141414',
              bgcolor: '#242424',
              color: '#f2f2f2',
              title_color: '#ffffff',
            };
            secondGraph._nodes.push(nodeB);

            graphApp.graph = secondGraph;
            extension.loadedGraph();

            const midState = {
              firstListeners: firstSignal.listeners.size,
              firstRemoved: firstSignal.removedCount,
              secondListeners: secondSignal.listeners.size,
            };

            const outputsB = {
              warmup_json: '{"counts": {"total": 4, "warmed": 4}}',
              trim_json: '{"items": 0}',
            };

            secondSignal.emit(nodeB, outputsB);

            const finalState = {
              nodeAColor: nodeA.boxcolor,
              nodeBColor: nodeB.boxcolor,
              dirtyCalls: dirtyCalls.length,
              firstRemoved: firstSignal.removedCount,
              firstRemaining: firstSignal.listeners.size,
              secondListeners: secondSignal.listeners.size,
              nodeADecorated: Boolean(nodeA.__arenaAutoCacheDecorated),
              nodeBDecorated: Boolean(nodeB.__arenaAutoCacheDecorated),
            };

            console.log(JSON.stringify({ firstState, midState, finalState }));
            """
        ).strip()

        completed = subprocess.run(
            ["node", "-e", script, str(self.extension_path)],
            check=True,
            capture_output=True,
            text=True,
        )

        output_lines = [line for line in completed.stdout.splitlines() if line.strip()]
        payload = json.loads(output_lines[-1])

        self.assertTrue(payload["firstState"]["decorated"])
        self.assertEqual(payload["firstState"]["nodeColor"], "#2e7d32")
        self.assertEqual(payload["firstState"]["listeners"], 1)

        self.assertEqual(payload["midState"]["firstListeners"], 0)
        self.assertEqual(payload["midState"]["firstRemoved"], 1)
        self.assertEqual(payload["midState"]["secondListeners"], 1)

        self.assertEqual(payload["finalState"]["nodeBColor"], "#2e7d32")
        self.assertEqual(payload["finalState"]["firstRemaining"], 0)
        self.assertEqual(payload["finalState"]["secondListeners"], 1)
        self.assertGreaterEqual(payload["finalState"]["dirtyCalls"], 2)


if __name__ == "__main__":  # pragma: no cover - unittest main hook
    unittest.main()
