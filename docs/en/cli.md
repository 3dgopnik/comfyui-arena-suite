---
title: "CLI"
description: "Helper scripts for cache and model maintenance."
---

[Overview](index.md) · [Quickstart](quickstart.md) · **CLI** · [Configuration](config.md) · [Troubleshooting](troubleshooting.md)

---

# CLI helpers

Scripts under `scripts/` provide HF/CivitAI update helpers, disk benchmarking, and cache setup.

Examples:
```bash
python scripts/arena_updater_hf.py --help
python scripts/arena_updater_civitai.py --help
python scripts/arena_benchmark_disk.py --help
```

Windows quick actions:
- `call scripts/arena_set_cache.bat D:\ComfyCache 1 1`
- `scripts/arena_bootstrap_cache.bat` or `scripts/arena_bootstrap_cache.ps1`

---

[← Back: Quickstart](quickstart.md) · [Next: Configuration →](config.md)

