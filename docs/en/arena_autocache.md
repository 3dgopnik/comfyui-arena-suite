---
title: Arena AutoCache v5.0.0
description: Automatic model caching for ComfyUI with Settings UI and three modes
status: published
---

# Arena AutoCache v5.0.0 — Quick Guide

Arena AutoCache speeds up ComfyUI by caching models on a fast SSD.

## Modes
- OnDemand (default): cache on first use, non-blocking background copy
- Eager: warm up cache at ComfyUI start
- Disabled: turn caching off

## Configure via Settings UI (recommended)
1) Settings → arena → enable AutoCacheEnable
2) Set Cache Root (SSD)
3) Click "💾 Save to .env" → creates/updates `user/arena_autocache.env`

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
