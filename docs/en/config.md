---
title: "Configuration"
description: "Environment variables and AutoCache node parameters."
---

[Overview](index.md) · [Quickstart](quickstart.md) · [CLI](cli.md) · **Configuration** · [Troubleshooting](troubleshooting.md)

---

# Environment variables

- `ARENA_CACHE_ROOT` — SSD cache root. Defaults:
  - Windows: `%LOCALAPPDATA%\ArenaAutoCache`
  - Linux/macOS: `<ComfyUI root>/ArenaAutoCache`
- `ARENA_CACHE_ENABLE` — `1`/`0` to enable/disable the runtime patch.
- `ARENA_CACHE_MAX_GB` — cache size limit in GiB (default `300`).
- `ARENA_LANG` — force node language (`en`/`ru`). Defaults to `COMFYUI_LANG`.

# AutoCache nodes
- Config — apply/override cache settings at runtime.
- Stats / StatsEx — cache statistics.
- Trim — clear cache by category.
- Manager — manage categories and paths.
- Audit / Warmup — audit presence and pre‑fill cache from lists/JSON workflow.

