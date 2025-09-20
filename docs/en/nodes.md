---
title: "Nodes"
description: "Reference for the ComfyUI Arena Suite nodes and socket layout."
---

**Overview** · [Quickstart](quickstart.md) · [CLI](cli.md) · [Configuration](config.md) · [Troubleshooting](troubleshooting.md) · **Nodes**

---

# Arena node reference

This page lists all Arena nodes shipped with the package, their purpose and socket signatures. Socket names match the ComfyUI interface.

## AutoCache

### 🅰️ Arena AutoCache: Config (`ArenaAutoCacheConfig`)

Runtime helper that updates the SSD cache settings during a workflow run.

- **Inputs**
  - `cache_root` (`STRING`, defaults to the active value) — path to the cache directory. An empty string keeps the previous root.
  - `max_size_gb` (`INT`, ≥ 0) — cache size limit in GiB.
  - `enable` (`BOOLEAN`) — toggles the LRU cache patch.
  - `verbose` (`BOOLEAN`) — prints verbose log messages.
- **Outputs**
  - `STRING` — JSON with the `ok` flag, the effective settings and optional `error`/`note` fields.

### 🅰️ Arena AutoCache: Stats (`ArenaAutoCacheStats`)

Returns aggregated cache stats for a single category. When the cache is disabled, it responds with a stub containing `ok=false`.

- **Inputs**
  - `category` (`STRING`, default `"checkpoints"`) — cache category/folder name.
- **Outputs**
  - `STRING` — JSON exposing `category`, `cache_root`, `enabled`, `items`, `total_bytes`, `total_gb`, `max_size_gb`, `last_op`, `last_path` and an optional `note`.

### 🅰️ Arena AutoCache: StatsEx (`ArenaAutoCacheStatsEx`)

Extended statistics node with dedicated sockets for numeric values and session counters.

- **Inputs**
  - `category` (`STRING`, default `"checkpoints"`).
- **Outputs**
  - `STRING` (`json`) — same payload as **🅰️ Arena AutoCache: Stats** (`ArenaAutoCacheStats`).
  - `INT` (`items`) — number of cached entries.
  - `FLOAT` (`total_gb`) — total cache size in GiB.
  - `STRING` (`cache_root`) — resolved cache root path.
  - `INT` (`session_hits`) — session hit counter.
  - `INT` (`session_misses`) — session miss counter.
  - `INT` (`session_trims`) — session trim counter.

### 🅰️ Arena AutoCache Audit (`ArenaAutoCacheAudit`)

Checks whether source models exist and whether the cache already contains the corresponding files. Supports `items` lists (newline separated strings or JSON arrays) and auto-discovery from `workflow_json`. Only filenames with typical model extensions (`.safetensors`, `.ckpt`, `.pt`, `.pth`, `.onnx`, `.vae`, `.bin`, `.gguf`, `.yaml`, `.yml`, `.npz`, `.pb`, `.tflite`) are considered.

- **Inputs**
  - `items` (`STRING`, multiline) — `category:file` strings or a JSON array of strings/objects with `category` + `name`/`filename`.
  - `workflow_json` (`STRING`, multiline) — optional workflow JSON dump for automatic discovery.
  - `default_category` (`STRING`, default `"checkpoints"`) — fallback category when not specified.
- **Outputs**
  - `STRING` (`json`) — report listing each item with `cached`, `missing_cache`, `missing_source` statuses and aggregated `counts`.
  - `INT` (`total`) — number of unique entries in the report.
  - `INT` (`cached`) — entries already present in the cache.
  - `INT` (`missing`) — entries missing either from the cache or from the source directories.

### 🅰️ Arena AutoCache Warmup (`ArenaAutoCacheWarmup`)

Warms up the cache using the same `items`/`workflow_json` specification. The node ensures free space via `_lru_ensure_room`, copies missing files and updates the cache index (`_update_index_touch`, `_update_index_meta`).

- **Inputs**
  - `items` (`STRING`, multiline) — warmup targets (strings or JSON, identical to `Audit`).
  - `workflow_json` (`STRING`, multiline) — optional workflow JSON dump.
  - `default_category` (`STRING`, default `"checkpoints"`).
- **Outputs**
  - `STRING` (`json`) — execution report with per-item statuses (`copied`, `cached`, `missing_source`, `error_*`) and aggregated counters `warmed`, `copied`, `missing`, `errors`, `skipped`.
  - `INT` (`total`) — number of processed entries.
  - `INT` (`warmed`) — entries now cached.
  - `INT` (`copied`) — files copied during warmup.
  - `INT` (`missing`) — entries skipped because the source file is missing.
  - `INT` (`errors`) — failures such as trimming/copy errors.

### 🅰️ Arena AutoCache: Trim (`ArenaAutoCacheTrim`)

Manually runs the LRU maintenance routine for the selected category.

- **Inputs**
  - `category` (`STRING`, default `"checkpoints"`).
- **Outputs**
  - `STRING` — JSON containing `ok`, `category`, `trimmed`, `items`, `total_bytes`, `total_gb`, `max_size_gb` and a descriptive `note`.

### 🅰️ Arena AutoCache: Manager (`ArenaAutoCacheManager`)

Composite node that applies the configuration, optionally executes `Trim` and emits two JSON reports.

- **Inputs**
  - `cache_root` (`STRING`, defaults to the active value).
  - `max_size_gb` (`INT`, ≥ 0).
  - `enable` (`BOOLEAN`).
  - `verbose` (`BOOLEAN`).
  - `category` (`STRING`, default `"checkpoints"`).
  - `do_trim` (`BOOLEAN`, default `false`) — triggers trimming after configuration updates.
- **Outputs**
  - `STRING` (`stats_json`) — statistics JSON identical to **🅰️ Arena AutoCache: StatsEx** (`ArenaAutoCacheStatsEx`).
  - `STRING` (`action_json`) — execution log with a `config` object and, when enabled, `trim` details.

## Legacy

### 🅰️ Arena Make Tiles Segments (`Arena_MakeTilesSegs`)

Generates Impact Pack compatible `SEGS` for tiled upscale workflows. The node raises `IMPACT_MISSING_MESSAGE` if the dependency is missing.

- **Inputs**
  - `images` (`IMAGE`) — input image batch.
  - `width` (`INT`, 64–4096, step 8) — tile width.
  - `height` (`INT`, 64–4096, step 8) — tile height.
  - `crop_factor` (`FLOAT`, 1.0–10.0, step 0.01) — crop padding multiplier.
  - `min_overlap` (`INT`, 0–512, step 1) — minimum tile overlap.
  - `filter_segs_dilation` (`INT`, −255…255, step 1) — dilation for filter masks.
  - `mask_irregularity` (`FLOAT`, 0–1.0, step 0.01) — strength of random mask irregularities.
  - `irregular_mask_mode` (`STRING`, options `Reuse fast`, `Reuse quality`, `All random fast`, `All random quality`).
  - `filter_in_segs_opt` (`SEGS`, optional) — inclusion masks.
  - `filter_out_segs_opt` (`SEGS`, optional) — exclusion masks.
- **Outputs**
  - `SEGS` — tuple with the original image size and a list of Impact-compatible `SEG` segments.

---

[← Back: Troubleshooting](troubleshooting.md) · [Back to top ↑](#arena-node-reference)
