# ComfyUI_Arena

Single-package for all **Arena** nodes.

- `legacy/` — migrated from local install.
- `autocache/` — SSD auto-cache (WIP).
- `updater/` — model updater (WIP).

> Python bytecode and `__pycache__` are excluded by `.gitignore`.

## AutoCache nodes

### ArenaAutoCacheStats

Returns a JSON string with extended cache metadata:

- `category` — ComfyUI asset group.
- `cache_root` — absolute directory for the cache category.
- `enabled` — `true` when `ARENA_CACHE_ENABLE=1`.
- `items` — number of cached files tracked in the index.
- `total_bytes` / `total_gb` — aggregate cache size (bytes and GiB).
- `max_size_gb` — configured capacity limit.
- `last_op` / `last_path` — last cache event (`HIT`, `MISS`, `TRIM`, `COPY`) and the affected path.

### ArenaAutoCacheTrim

Returns a JSON string with the trim result:

- `ok` — `true` if the trim succeeded.
- `category` — cache category handled by the node.
- `trimmed` — list of file paths evicted during the run (empty when nothing was removed).
- `items`, `total_bytes`, `total_gb`, `max_size_gb` — snapshot of the cache after trimming.
- `note` — human-readable status (`trimmed to limit`, `cache disabled`, etc.).
