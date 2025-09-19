# How it works

**Single package** `ComfyUI_Arena` exposes:
- *legacy* nodes (existing functions, unchanged, just relocated);
- *autocache* runtime patcher for `folder_paths` to inject SSD cache first;
- *updater* helper to version and point `current` symlinks/junctions.

WIP parts are scaffolds; implementation to be generated via Codex prompts.
