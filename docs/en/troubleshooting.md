---
title: "Troubleshooting"
description: "Placeholder for the upcoming English troubleshooting guide."
---

[Overview](index.md) · [Quickstart](quickstart.md) · [CLI](cli.md) · [Configuration](config.md) · **Troubleshooting**

---

# Troubleshooting (translation pending)

Troubleshooting tips will be translated to English in a future update. Use the Russian reference in `../ru/troubleshooting.md` for guidance.

## AutoCache web overlay is missing
1. Restart ComfyUI so it reloads extensions after updating the package.
2. Verify that the `web/extensions/arena_autocache.js` file is present inside the Arena nodes repository folder.
3. If the ComfyUI log prints `[Arena] web assets missing: expected web/extensions/arena_autocache.js`, the package was installed without the `web` directory. Reinstall the suite keeping the repository structure intact and confirm the wheel includes the assets (`python -m build` then `unzip -l dist/*.whl | grep arena_autocache.js`).
4. Starting with this release the module locates the `web` directory by walking up to the repository root, so manual symlinks or copies are no longer required.
5. Inspect the browser console: once the overlay finishes initialising it logs `Arena.AutoCache.Overlay loaded …`. If you instead see `Arena.AutoCache.Overlay failed to load: app not found`, ComfyUI never exposed the `app` object — restart the UI or update your installation.
6. Desktop builds that do not expose `graph.onNodeOutputsUpdated` automatically fall back to the node execution signal (`graph.onExecuted`). If the palette still refuses to refresh, check that no other extension overwrote that handler and search the console for `Arena.AutoCache.Overlay execution update failed` errors.

## Package build smoke check
1. Ensure the `build` module is installed (`python -m pip install build`).
2. From the repository root run `python -m build` to produce the sdist and wheel under `dist/`.
3. Inspect the wheel archive (`unzip -l dist/*.whl`) and confirm it contains `web/extensions/arena_autocache.js`. If the file is missing, the static assets were not packaged.

---

[← Back: Configuration](config.md)
