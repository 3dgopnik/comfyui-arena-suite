"""Tests for the Arena AutoCache web overlay integration."""

from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ArenaAutoCacheOverlayLocalizationTest(unittest.TestCase):
    """Ensure localized output labels are normalized for the overlay."""

    def test_overlay_updates_with_localized_output_names(self) -> None:
        extension_path = PROJECT_ROOT / "web" / "extensions" / "arena_autocache.js"
        script = textwrap.dedent(
            """
            const fs = require('node:fs');
            const vm = require('node:vm');

            const sourcePath = process.argv[1];
            const source = fs.readFileSync(sourcePath, 'utf8');

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

            vm.createContext(sandbox);
            vm.runInContext(source, sandbox, { filename: sourcePath });

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
            ["node", "-e", script, str(extension_path)],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout.strip())

        self.assertTrue(payload["decorated"])
        self.assertGreaterEqual(payload["dirtyCalls"], 1)
        self.assertEqual(payload["boxcolor"], "#2e7d32")

    def test_overlay_registers_when_app_is_delayed(self) -> None:
        extension_path = PROJECT_ROOT / "web" / "extensions" / "arena_autocache.js"
        script = textwrap.dedent(
            """
            const fs = require('node:fs');
            const vm = require('node:vm');

            const sourcePath = process.argv[1];
            const source = fs.readFileSync(sourcePath, 'utf8');

            const extensionHolder = { value: null, calls: 0 };

            const sandbox = { console };
            sandbox.setTimeout = setTimeout;
            sandbox.clearTimeout = clearTimeout;
            sandbox.globalThis = sandbox;
            sandbox.window = sandbox;
            sandbox.global = sandbox;

            vm.createContext(sandbox);
            vm.runInContext(source, sandbox, { filename: sourcePath });

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
            ["node", "-e", script, str(extension_path)],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout.strip())

        self.assertTrue(payload["registered"])
        self.assertEqual(payload["calls"], 1)


if __name__ == "__main__":  # pragma: no cover - unittest main hook
    unittest.main()
