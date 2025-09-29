---
title: "Overview"
description: "English documentation is under preparation."
---

Overview · [Quickstart](quickstart.md) · [CLI](cli.md) · [Configuration](config.md) · [Troubleshooting](troubleshooting.md) · [Nodes](nodes.md)

---

# ComfyUI Arena Suite v4.2.4 (English documentation)

> **TL;DR — Arena AutoCache (simple) v4.2.4**
> - Production-ready node for model caching
> - OnDemand mode - transparent caching on first access
> - Full configuration via .env files with autopatch
> - Thread-safe deduplication and safe cache cleanup
> - LRU-pruning up to 95% limit with detailed logging
> - Enhanced security with path depth validation
> - Deferred autopatch for better compatibility
> - Default cache root if `ARENA_CACHE_ROOT` is not set:
>   - Windows: `%LOCALAPPDATA%\ArenaAutoCache` (e.g. `C:\Users\you\AppData\Local\ArenaAutoCache`)
>   - Linux/macOS: `<ComfyUI root>/ArenaAutoCache`
> - Set `ARENA_CACHE_ROOT=<path>` before launching ComfyUI so the SSD patch writes to your desired location. Arena AutoCache nodes (Config/Stats/Trim/Manager) will show the active directory.
> - Restart ComfyUI after changing environment variables.
> - Examples:
>   - PowerShell: `$env:ARENA_CACHE_ROOT='D:\ComfyCache'; python main.py`
>   - CMD: `set ARENA_CACHE_ROOT=D:\ComfyCache && python main.py`
>   - bash: `ARENA_CACHE_ROOT=/mnt/ssd/cache python main.py`
> - Optional overrides: `ARENA_CACHE_ENABLE=0` temporarily disables the patch; `ARENA_CACHE_MAX_GB=512` caps the cache size (GiB).

For socket-level guidance refer to the [Nodes](nodes.md) reference.

Arena Suite combines: production-ready Arena AutoCache (simple) node and legacy nodes.

## Features
- **🅰️ Arena AutoCache (simple) v4.2.4** — production-ready node for model caching
- **Legacy nodes** — Arena Make Tiles Segments and others
- **Production-ready architecture** — thread-safe, safe cleanup, LRU-pruning
- **Enhanced security** — strict path depth validation for all platforms

## Requirements
- ComfyUI (current master branch)
- Python 3.10+
- SSD for better AutoCache performance

---

[Next: Quickstart →](quickstart.md)

