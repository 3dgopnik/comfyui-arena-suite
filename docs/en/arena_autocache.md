---
title: Arena AutoCache v5.1.0
description: Automatic model caching for ComfyUI with three Arena button modes
status: published
---

# Arena AutoCache v5.1.0 — Quick Guide

Arena AutoCache speeds up ComfyUI by caching models on a fast SSD with three Arena button modes.

## Arena Button Modes

### ⚫ Gray Mode (default)
- `ARENA_AUTO_CACHE_ENABLED=0`, `ARENA_AUTOCACHE_AUTOPATCH=0`
- System completely disabled
- Uses original model paths
- **Click button** → switches to red mode

### 🔴 Red Mode (active caching)
- `ARENA_AUTO_CACHE_ENABLED=1`, `ARENA_AUTOCACHE_AUTOPATCH=1`
- Caches new models + uses cache
- Non-blocking background copy
- **Click button** → switches to gray mode (disable)

### 🟢 Green Mode (read-only)
- `ARENA_AUTO_CACHE_ENABLED=1`, `ARENA_AUTOCACHE_AUTOPATCH=0`
- Uses cache, does NOT cache new models
- **Tooltip indicator**: "X models not cached (click to cache)"
- **Click button with indicator** → switches to red mode
- **Click button** → switches to gray mode

## Configure via Settings UI (recommended)
1) Settings → arena → set Cache Root (SSD)
2) Click "💾 Save to .env" → creates `user/arena_autocache.env` with **ENABLED=0, AUTOPATCH=0**
3) System remains disabled until activated via Arena button

## Arena Button Controls
- **Main button click**: gray ↔ red, red ↔ gray, green → gray
- **Dropdown menu** (arrow down): select any mode
- **Auto-detect mode** on load from API

## Configure via Node (alternative)
- Add AutoCache node on canvas, set `enable_caching=True`
- Active node overrides .env for current workflow

## .env variables
`ARENA_AUTO_CACHE_ENABLED`, `ARENA_CACHE_ROOT`, `ARENA_CACHE_MODE`,
`ARENA_CACHE_MIN_SIZE_MB`, `ARENA_CACHE_MAX_GB`, `ARENA_AUTOCACHE_AUTOPATCH`,
`ARENA_CACHE_VERBOSE`, `ARENA_CACHE_DISCOVERY`, `ARENA_CACHE_PREFETCH_STRATEGY`,
`ARENA_CACHE_MAX_CONCURRENCY`, `ARENA_CACHE_SESSION_BYTE_BUDGET`, `ARENA_CACHE_COOLDOWN_MS`

## Supported categories
checkpoints, loras, clip, vae, controlnet, upscale_models, embeddings,
hypernetworks, gguf_models, unet_models, diffusion_models

## Safety
Caching is OFF by default. Paths validated. Operations are thread‑safe.