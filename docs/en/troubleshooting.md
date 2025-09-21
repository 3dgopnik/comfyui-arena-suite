---
title: "Troubleshooting"
description: "Common issues and fixes for Arena Suite."
---

[Overview](index.md) · [Quickstart](quickstart.md) · [CLI](cli.md) · [Configuration](config.md) · **Troubleshooting**

---

# Common issues

## Web overlay not loading
- Ensure `web/extensions/arena_autocache.js` exists.
- Check DevTools → Network for successful load.
- Check ComfyUI/browser consoles for errors.

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

