# ComfyUI Arena Suite

> **TL;DR — AutoCache setup**
> - Default cache root if `ARENA_CACHE_ROOT` is not set:
>   - Windows: `%LOCALAPPDATA%\ArenaAutoCache` (for example, `C:\Users\you\AppData\Local\ArenaAutoCache`)
>   - Linux/macOS: `<ComfyUI root>/ArenaAutoCache`
> - Set `ARENA_CACHE_ROOT=<path>` before launching ComfyUI so the SSD patch writes to your desired location. 🅰️ Arena AutoCache nodes (Config/Stats/Trim/Manager) will show the active directory.
> - Restart ComfyUI after changing environment variables.
> - Examples:
>   - PowerShell: `$env:ARENA_CACHE_ROOT='D:\ComfyCache'; python main.py`
>   - CMD: `set ARENA_CACHE_ROOT=D:\ComfyCache && python main.py`
>   - bash: `ARENA_CACHE_ROOT=/mnt/ssd/cache python main.py`
> - Optional overrides: `ARENA_CACHE_ENABLE=0` temporarily disables the patch; `ARENA_CACHE_MAX_GB=512` caps the cache size (GiB).

**EN:** Arena nodes bundle legacy helpers, SSD-aware caching, and updater utilities to streamline ComfyUI installations in one maintained package.
**RU:** Узлы Arena объединяют унаследованные инструменты, SSD-кэш и вспомогательные обновления, чтобы упростить поддержку ComfyUI в рамках единого пакета.

Custom nodes for ComfyUI with the **Arena** prefix bundled in a **single package**.

## Features overview
- **Legacy nodes** — migrated utilities that preserve the existing interfaces while living under `ComfyUI_Arena/legacy`.
- **AutoCache** — runtime patch for `folder_paths` that prefers an SSD cache, plus 🅰️ Arena AutoCache: Config/StatsEx/Trim/Manager nodes for in-graph control (see `custom_nodes/ComfyUI_Arena/README.md`).
- **Audit & Warmup nodes** — verify and pre-fill the SSD cache via multiline lists or workflow JSON (see `custom_nodes/ComfyUI_Arena/README.md`). **RU:** Узлы Audit/Warmup проверяют и прогревают SSD-кэш, принимают многострочные списки и JSON из `workflow_json` экспорта.
- **AutoCache web overlay** — bundled front-end extension that highlights Arena AutoCache nodes with live status bars; follow the enablement guide in `custom_nodes/ComfyUI_Arena/README.md` and `docs/ru/nodes.md`. **RU:** Встроенное веб-расширение подсвечивает узлы AutoCache и отображает прогресс; шаги подключения описаны в `custom_nodes/ComfyUI_Arena/README.md` и `docs/ru/nodes.md`.
- **Updater scaffolding** — Hugging Face and CivitAI helpers (WIP) intended to keep local model folders in sync and manage `current` symlinks.

## System requirements
- **ComfyUI** with custom node support (tested on the current `master` branch).
- **Python 3.10+** as required by `pyproject.toml`.
- **Fast SSD storage** when enabling AutoCache to get the best throughput.
- **[ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack)** for legacy Arena nodes — install it via ComfyUI Manager or manually clone the repository so `ComfyUI-Impact-Pack/modules` is available on `PYTHONPATH`.

## Quick usage summary
1. Install the suite through **ComfyUI Manager → Install from URL** using your repository URL (for example, `https://github.com/<your-org>/comfyui-arena-suite`).
2. Refresh the custom nodes list or restart ComfyUI so the new Arena nodes load.
3. Drop nodes with the **Arena** prefix into your graph to verify the installation (e.g., **🅰️ Arena AutoCache: Stats** / `ArenaAutoCacheStats`).
4. Configure SSD caching and update manifests as needed — see the documentation below for detailed steps.

## Documentation
- 🇷🇺 Русская документация: [Обзор](docs/ru/index.md), [Быстрый старт](docs/ru/quickstart.md), [CLI](docs/ru/cli.md), [Конфигурация](docs/ru/config.md), [Диагностика](docs/ru/troubleshooting.md).
- 🇬🇧 English placeholders: [Overview](docs/en/index.md), [Quickstart](docs/en/quickstart.md), [CLI](docs/en/cli.md), [Configuration](docs/en/config.md), [Troubleshooting](docs/en/troubleshooting.md).
- [Agents rules](AGENTS.md) - guidelines for developing and integrating Codex & ComfyUI agents.

## Codex workflow
1. Codex генерирует код (EN identifiers, RU comments).
2. Создаёт/обновляет Issue: `Codex: <module> — <topic> — <date>` с блоками **SUMMARY / ISSUES & TASKS / TEST PLAN / NOTES**.
3. Все изменения идут через PR; тело PR — по шаблону (см. `.github/pull_request_template.md`).
4. В коммитах ссылаться на Issue: `Refs #<номер>`.
5. CHANGELOG (`[Unreleased]`) и docs обновляются в том же PR.

