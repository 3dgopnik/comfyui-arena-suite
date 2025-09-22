---
title: "Nodes"
description: "Reference for the ComfyUI Arena Suite nodes."
---

[Overview](index.md) · [Quickstart](quickstart.md) · [CLI](cli.md) · [Configuration](config.md) · [Troubleshooting](troubleshooting.md) · **Nodes**

---

# Arena nodes (summary)

This page will provide a detailed reference for Arena nodes. For now, please refer to the Russian page `../ru/nodes.md` and the in‑UI socket tooltips.

Covered groups:
- AutoCache (Config, Stats/StatsEx, Trim, Manager, Dashboard, Ops, Audit/Warmup)
- Legacy helpers

## Workflow allowlist

Audit/Warmup/Ops nodes refresh a workflow allowlist from the `items` and `workflow_json` inputs before they run. When `workflow_json` is empty the nodes try to read the active graph via `server.PromptServer` and continue with the current workflow. Only the enumerated category/name pairs trigger LRU copies; direct `folder_paths.get_full_path` calls without registration return source paths without priming the cache.

## Copy notifications

- `_copy_into_cache_lru` now emits `copy_started`, `copy_completed`, and `copy_skipped` events to the console (`[ArenaAutoCache] ...`) and mirrors them via `PromptServer.instance.send_sync("arena/autocache/copy_event", ...)` when the server is available. These events fire even when `ARENA_CACHE_VERBOSE` is disabled.
- Failures trigger a `copy_failed` event with the exception text so the overlay can flag the issue immediately.
- ArenaAutoCache Warmup and Ops expose an optional `log_context` string input. Supply plain text or a JSON object (e.g. `{ "node_id": "N42" }`); raw strings are wrapped into `{ "text": "..." }` automatically.
- Warmup always adds `node="ArenaAutoCacheWarmup"`, and Ops augments the context with `node="ArenaAutoCacheOps"` plus the active `mode`. The merged context is included in every copy event, letting the overlay link progress back to a concrete node execution.

