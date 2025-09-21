---
title: "Nodes"
description: "Reference for the ComfyUI Arena Suite nodes and socket layout."
---

**Overview** · [Quickstart](quickstart.md) · [CLI](cli.md) · [Configuration](config.md) · [Troubleshooting](troubleshooting.md) · **Nodes**

---

# Arena node reference

This page lists all Arena nodes shipped with the package, their purpose and socket signatures. Socket names match the ComfyUI interface.

## AutoCache web overlay

The suite ships with the `web/extensions/arena_autocache.js` front-end extension, which automatically hooks into ComfyUI and listens to the `summary_json`/`warmup_json`/`trim_json` sockets.

### Enablement

1. **Install the repository as a whole.** ComfyUI Manager clones everything into `custom_nodes/comfyui-arena-suite`. For manual installs copy the files under `web/extensions/` into `ComfyUI/web/extensions/`.
2. **Restart ComfyUI.** Reload the interface after installing or updating so the `arena_autocache.js` extension initializes.
3. **Add a supported node.** Drop `ArenaAutoCacheDashboard`, `ArenaAutoCacheOps`, or `ArenaAutoCacheAudit` and run the workflow so they emit JSON on the relevant sockets.
4. **Watch the highlights.** Once data is available the header, progress bars, and tooltips refresh automatically.

### UI cues and hints

- **Status headline.** Pulled from `summary_json.ui.headline`; before the first update it falls back to “Arena AutoCache”.
- **Color palette.** Headers turn green (`ok`), amber (`warn`), or red (`error`). While idle the default ComfyUI colors stay untouched.
- **Progress bars.** Separate gauges represent audit, warmup, trim, and overall cache usage (`Capacity`) based on the JSON counters.
- **Report details.** Up to four lines from `ui.details` are rendered beneath the status, making it easy to surface short notes.
- **Warnings.** The `⚠` badge appears when models are missing, warmups fail, trim notes require attention, or JSON parsing fails.
- **Localization.** Socket titles in any language (`Summary JSON`, `JSON сводки`, `Прогрев JSON`, `Обрезка JSON`, etc.) are normalized to the canonical `summary`/`warmup`/`trim` fields so the overlay refreshes regardless of the UI locale.

The overlay currently covers `ArenaAutoCacheAudit`, `ArenaAutoCacheDashboard`, and `ArenaAutoCacheOps` and requires no additional toggles.

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
  - `extended_stats` (`BOOLEAN`, optional) — collects extended statistics for all detected categories and augments `summary_json` with aggregates.
  - `apply_settings` (`BOOLEAN`, optional) — applies overrides from `settings_json` before running the audit.
  - `do_trim_now` (`BOOLEAN`, optional) — runs the LRU trim against every affected category right after the audit completes.
  - `settings_json` (`STRING`, multiline, optional) — JSON payload with `cache_root`, `max_size_gb`, `enable`, `verbose` overrides used when `apply_settings=true`.
- **Outputs**
  - `STRING` (`json`) — report listing each item with `cached`, `missing_cache`, `missing_source` statuses and aggregated `counts`. The payload also includes `ui` and `timings.duration_seconds` fields for dashboard rendering.
  - `INT` (`total`) — number of unique entries in the report.
  - `INT` (`cached`) — entries already present in the cache.
  - `INT` (`missing`) — entries missing either from the cache or from the source directories.
  - `STRING` (`summary_json`) — UI summary with an `actions` list (settings/stats/trim), `stats_meta`/`audit_meta` blocks, the processed categories, and per-operation timings.

> **Limitations**: `apply_settings` updates the global cache configuration, while `do_trim_now` trims every category discovered through `items` and `workflow_json`. When multiple categories are detected, `summary_json` aggregates their stats and records each trim result in the `actions` list.

### 🅰️ Arena AutoCache Warmup (`ArenaAutoCacheWarmup`)

Warms up the cache using the same `items`/`workflow_json` specification. The node ensures free space via `_lru_ensure_room`, copies missing files and updates the cache index (`_update_index_touch`, `_update_index_meta`).

- **Inputs**
  - `items` (`STRING`, multiline) — warmup targets (strings or JSON, identical to `Audit`).
  - `workflow_json` (`STRING`, multiline) — optional workflow JSON dump.
  - `default_category` (`STRING`, default `"checkpoints"`).
- **Outputs**
  - `STRING` (`json`) — execution report with per-item statuses (`copied`, `cached`, `missing_source`, `error_*`) and aggregated counters `warmed`, `copied`, `missing`, `errors`, `skipped`, plus `ui` and `timings.duration_seconds` metadata.
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

### 🅰️ Arena AutoCache: Dashboard (`ArenaAutoCacheDashboard`)

Composite node that surfaces stats, audit, optional trim and settings changes in a single summary. It is designed for dashboards: the emitted JSON always contains enriched `ui` and `timings` blocks.

- **Inputs**
  - `category` (`STRING`, default `"checkpoints"`).
  - `items` (`STRING`, multiline) — audit targets.
  - `workflow_json` (`STRING`, multiline) — optional workflow dump used for auto-discovery.
  - `default_category` (`STRING`, default `"checkpoints"`).
  - `extended_stats` (`BOOLEAN`, default `false`) — include a `ui` block in `stats_json` with human-readable hints.
  - `apply_settings` (`BOOLEAN`, default `false`) — apply overrides from `settings_json` before collecting stats.
  - `do_trim_now` (`BOOLEAN`, default `false`) — run trim immediately and include the result in the summary.
  - `settings_json` (`STRING`, multiline) — JSON overrides for `cache_root`, `max_size_gb`, `enable`, `verbose`.
- **Outputs**
  - `STRING` (`summary_json`) — combined view with `config`, `stats`, `audit`, `trim` sections and a `timings` map.
  - `STRING` (`stats_json`) — stats payload (with optional `ui`/`timings` when `extended_stats=true`).
  - `STRING` (`audit_json`) — audit payload enriched with `ui`/`timings`.

### 🅰️ Arena AutoCache: Ops (`ArenaAutoCacheOps`)

Swiss-army node for automation workflows. It can run audits, warmups, trims, or an audit-then-warmup combo and optionally benchmark the resulting cache throughput.

- **Inputs**
  - `category` (`STRING`, default `"checkpoints"`).
  - `items` (`STRING`, multiline) — shared specification used by audit/warmup.
  - `workflow_json` (`STRING`, multiline) — optional workflow dump used for auto-discovery.
  - `default_category` (`STRING`, default `"checkpoints"`).
  - `mode` (`STRING`, default `"audit_then_warmup"`) — one of `audit`, `warmup`, `audit_then_warmup`, `trim`.
  - `benchmark_samples` (`INT`, default `0`) — number of cache files to read for throughput metrics (0 disables benchmarking).
  - `benchmark_read_mb` (`FLOAT`, default `0.0`) — read cap per sample in MiB.
- **Outputs**
  - `STRING` (`summary_json`) — UI-friendly JSON combining stats, warmup, trim and optional audit, including a `timings` map (with `benchmark` info when enabled).
  - `STRING` (`warmup_json`) — warmup report or a stub when the mode skips warmup.
  - `STRING` (`trim_json`) — trim report or a stub when the mode skips trimming.

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
