# How it works

**Single package** `ComfyUI_Arena` exposes:
- *legacy* nodes (existing functions, unchanged, just relocated);
- *autocache* runtime patcher for `folder_paths` to inject SSD cache first;
- *updater* helper to version and point `current` symlinks/junctions.

WIP parts are scaffolds; implementation to be generated via Codex prompts.

When `ARENA_CACHE_ENABLE=0` the autocache patch stays inactive, while the
`ArenaAutoCacheStats` and `ArenaAutoCacheTrim` nodes still load and return
stubbed responses to signal that the cache is disabled.
