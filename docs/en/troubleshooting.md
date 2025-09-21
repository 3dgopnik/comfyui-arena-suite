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
3. Starting with this release the module locates the `web` directory by walking up to the repository root, so manual symlinks or copies are no longer required.
4. Inspect the browser console: once the overlay finishes initialising it logs `Arena.AutoCache.Overlay loaded …`. If you instead see `Arena.AutoCache.Overlay failed to load: app not found`, ComfyUI never exposed the `app` object — restart the UI or update your installation.
5. Desktop builds that do not expose `graph.onNodeOutputsUpdated` automatically fall back to the node execution signal (`graph.onExecuted`). If the palette still refuses to refresh, check that no other extension overwrote that handler and search the console for `Arena.AutoCache.Overlay execution update failed` errors.

---

[← Back: Configuration](config.md)
