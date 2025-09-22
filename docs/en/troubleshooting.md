---
title: "Troubleshooting"
description: "Common issues and fixes for Arena Suite."
---

[Overview](index.md) · [Quickstart](quickstart.md) · [CLI](cli.md) · [Configuration](config.md) · **Troubleshooting**

---

# Common issues

## Web overlay
The experimental UI overlay has been removed by default to prioritize stability on ComfyUI Desktop. Refer to the roadmap for future plans.

## Environment variables ignored
- Set variables before launching ComfyUI.
- Example (PowerShell): `$env:ARENA_CACHE_ROOT='D:\ComfyCache'; python main.py`
- Restart ComfyUI after changes.

## Nodes missing
- Refresh custom nodes or restart ComfyUI.
- Verify the repository is under `ComfyUI/custom_nodes/comfyui-arena-suite`.

## Cache not on SSD
- Inspect active path in `ArenaAutoCacheConfig/Stats`.
- Update `ARENA_CACHE_ROOT` and restart.

## Cache warmup is asynchronous
- The first lookup returns the original source path while a background worker copies the file into the cache.
- Subsequent requests reuse the cached copy. Test helpers can call `custom_nodes.ComfyUI_Arena.autocache.arena_auto_cache.wait_for_copy_queue()` to wait until the queue drains.

## ComfyUI Desktop: how to reload the UI
- ComfyUI Desktop does not use F5. Press the `R` key (English layout) in the app window to reload the frontend (JS extensions, including the Arena overlay).
- Frontend reload does not restart Python nodes. If you changed `.py` code, fully restart Desktop (close and reopen).
- To refresh the list of custom nodes use “Refresh custom nodes” in Manager (if available) or restart Desktop.
