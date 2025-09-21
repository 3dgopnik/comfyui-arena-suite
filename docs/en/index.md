---
title: "Overview"
description: "English documentation is under preparation."
---

Overview · [Quickstart](quickstart.md) · [CLI](cli.md) · [Configuration](config.md) · [Troubleshooting](troubleshooting.md) · [Nodes](nodes.md)

---

# Overview (English documentation coming soon)

> **TL;DR — AutoCache setup**
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

The English documentation is under preparation. Please refer to the Russian guide in `../ru/index.md` for up-to-date instructions.

---

[Next: Quickstart →](quickstart.md)

