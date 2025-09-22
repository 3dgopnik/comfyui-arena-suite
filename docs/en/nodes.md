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

Audit/Warmup/Ops nodes refresh a workflow allowlist from the `items` and `workflow_json` inputs before they run. Only the enumerated category/name pairs trigger LRU copies; direct `folder_paths.get_full_path` calls without registration return source paths without priming the cache.

