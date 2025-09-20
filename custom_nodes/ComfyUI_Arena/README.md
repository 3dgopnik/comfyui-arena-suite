# ComfyUI_Arena

Single-package for all **Arena** nodes.

- `legacy/` - migrated from local install.
- `autocache/` - SSD auto-cache.
- `updater/` - model updater (WIP).

> Python bytecode and `__pycache__` are excluded by `.gitignore`.

## AutoCache nodes

### ArenaAutoCacheConfig

Runtime configuration helper. Use it near the start of the workflow to pick the cache root, quota and toggle flags.

Inputs (required):

- `cache_root` - path to the SSD cache directory (defaults to current setting).
- `max_size_gb` - integer capacity limit (GiB).
- `enable` - switches the LRU cache on/off without restarting ComfyUI.
- `verbose` - prints debug messages to the console.

Output: single JSON string with `ok`, effective settings and optional `error`/`note` fields.

### ArenaAutoCacheStats

Backwards-compatible node that still returns the original JSON summary. Values: `category`, `cache_root`, `enabled`, `items`, `total_bytes`, `total_gb`, `max_size_gb`, `last_op`, `last_path` and optional `note`.

### ArenaAutoCacheStatsEx

Extended statistics with multiple sockets. Outputs: `(json, items, total_gb, cache_root, session_hits, session_misses, session_trims)`. The JSON mirrors the old stats output while the extra sockets expose numeric counters for UI widgets.

### ArenaAutoCacheTrim

Triggers manual LRU maintenance for a category. Output JSON includes `ok`, `category`, `trimmed`, `items`, `total_bytes`, `total_gb`, `max_size_gb` and `note`.

### ArenaAutoCacheManager

Convenience combo node. Applies configuration, optionally runs trim (`do_trim = true`) and returns a pair of JSON blobs: latest stats and action log. Useful for dashboard-style graphs; underlying nodes remain available for fine-grained control.

