---
title: "Nodes"
description: "Reference for the ComfyUI Arena Suite nodes."
---

[Overview](index.md) · [Quickstart](quickstart.md) · [CLI](cli.md) · [Configuration](config.md) · [Troubleshooting](troubleshooting.md) · **Nodes**

---

# Arena nodes (summary)

Groups in ComfyUI:

## Basic
- ArenaAutoCache Analyze — zero‑input plan + warmup for the active workflow.
- ArenaAutoCache Ops — combined audit + warmup (+trim when selected).

## Advanced
- Dashboard, Manager, Trim, StatsEx.

## Utils
- GetActiveWorkflow, Stats.

Please refer to the Russian reference `../ru/nodes.md` for details and examples.

## Workflow allowlist

Audit/Warmup/Ops nodes refresh a workflow allowlist from the `items` and `workflow_json` inputs before they run. When `workflow_json` is empty the nodes try to read the active graph via `server.PromptServer` and continue with the current workflow. Only the enumerated category/name pairs trigger LRU copies; direct `folder_paths.get_full_path` calls without registration return source paths without priming the cache.

## Copy notifications

- `_copy_into_cache_lru` now emits `copy_started`, `copy_completed`, and `copy_skipped` events to the console (`[ArenaAutoCache] ...`) and mirrors them via `PromptServer.instance.send_sync("arena/autocache/copy_event", ...)` when the server is available. These events fire even when `ARENA_CACHE_VERBOSE` is disabled.
- Failures trigger a `copy_failed` event with the exception text so the overlay can flag the issue immediately.
- ArenaAutoCache Warmup and Ops expose an optional `log_context` string input. Supply plain text or a JSON object (e.g. `{ "node_id": "N42" }`); raw strings are wrapped into `{ "text": "..." }` automatically.
- Warmup always adds `node="ArenaAutoCacheWarmup"`, and Ops augments the context with `node="ArenaAutoCacheOps"` plus the active `mode`. The merged context is included in every copy event, letting the overlay link progress back to a concrete node execution.

