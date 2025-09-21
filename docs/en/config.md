---
title: "Configuration"
description: "Placeholder for the upcoming English configuration guide."
---

[Overview](index.md) · [Quickstart](quickstart.md) · [CLI](cli.md) · **Configuration** · [Troubleshooting](troubleshooting.md)

---

# Configuration (translation pending)

The English configuration guide is not yet available. Please refer to `../ru/config.md` for detailed setup instructions.

**Windows bootstrap recap:** Run `scripts/arena_bootstrap_cache.bat` to select the cache directory and a GiB limit once; it writes `ARENA_CACHE_ROOT`, `ARENA_CACHE_MAX_GB`, `ARENA_CACHE_ENABLE`, and `ARENA_CACHE_VERBOSE` via `setx` and applies them to the current session.

**Temporary overrides:** Execute `call scripts/arena_set_cache.bat <cache_dir> [enable] [verbose]` from CMD when you need session-scoped adjustments without touching the persisted user variables.

---

[← Back: CLI](cli.md) · [Next: Troubleshooting →](troubleshooting.md)
