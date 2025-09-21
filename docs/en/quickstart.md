---
title: "Quickstart"
description: "Placeholder for the upcoming English quickstart guide."
---

[Overview](index.md) · **Quickstart** · [CLI](cli.md) · [Configuration](config.md) · [Troubleshooting](troubleshooting.md)

---

# Quickstart (translation pending)

The English quickstart will be added soon. For installation steps please consult the Russian version in `../ru/quickstart.md` and review [“Important (TL;DR): cache folder”](index.md#important-tldr-cache-folder) for the cache setup summary.

**AutoCache web overlay note:** When installing manually, place the repository under `ComfyUI/custom_nodes/comfyui-arena-suite/` so the front-end auto-discovers the `web` folder. After restarting ComfyUI open DevTools → **Network** to confirm `extensions/arena_autocache.js` loads, and check the ComfyUI/browser consoles for warnings.

**Windows cache bootstrap (summary):**
- Run `scripts/arena_bootstrap_cache.bat` once after installation. With PowerShell available it opens the WinForms helper for picking the folder and limit; otherwise it falls back to the CLI prompts. The script persists `ARENA_CACHE_ROOT`, `ARENA_CACHE_MAX_GB`, `ARENA_CACHE_ENABLE`, and `ARENA_CACHE_VERBOSE` for your user profile.
- Use `call scripts/arena_set_cache.bat <cache_dir> [enable] [verbose]` whenever you need to temporarily override the variables for the current CMD session only.

---

[← Back: Overview](index.md) · [Next: CLI →](cli.md)
