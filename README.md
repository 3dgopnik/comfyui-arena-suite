# ComfyUI Arena Suite

Custom nodes for ComfyUI with the **Arena** prefix bundled in a **single package**.

## Features overview
- **Legacy nodes** — migrated utilities that preserve the existing interfaces while living under `ComfyUI_Arena/legacy`.
- **AutoCache** — runtime patch for `folder_paths` that prefers an SSD cache to accelerate heavy model loads and exposes stats/trim helpers.
- **Updater scaffolding** — Hugging Face and CivitAI helpers (WIP) intended to keep local model folders in sync and manage `current` symlinks.

## System requirements
- **ComfyUI** with custom node support (tested on the current `master` branch).
- **Python 3.10+** as required by `pyproject.toml`.
- **Fast SSD storage** when enabling AutoCache to get the best throughput.
- **[ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack)** for legacy Arena nodes — install it via ComfyUI Manager or manually clone the repository so `ComfyUI-Impact-Pack/modules` is available on `PYTHONPATH`.

## Quick usage summary
1. Install the suite through **ComfyUI Manager → Install from URL** using your repository URL (for example, `https://github.com/<your-org>/comfyui-arena-suite`).
2. Refresh the custom nodes list or restart ComfyUI so the new Arena nodes load.
3. Drop nodes with the **Arena** prefix into your graph to verify the installation (e.g., `ArenaAutoCacheStats`).
4. Configure SSD caching and update manifests as needed — see the documentation below for detailed steps.

## Documentation
- 🇷🇺 Русская документация: [Обзор](docs/ru/index.md), [Быстрый старт](docs/ru/quickstart.md), [CLI](docs/ru/cli.md), [Конфигурация](docs/ru/config.md), [Диагностика](docs/ru/troubleshooting.md).
- 🇬🇧 English placeholders: [Overview](docs/en/index.md), [Quickstart](docs/en/quickstart.md), [CLI](docs/en/cli.md), [Configuration](docs/en/config.md),
- [Troubleshooting](docs/en/troubleshooting.md).
- [Agents rules](AGENTS.md) - guidelines for developing and integrating Codex & ComfyUI agents.

## Codex workflow
1. odex генерирует код (EN identifiers, RU comments).
2. Создаёт/обновляет Issue: `Codex: <module> — <topic> — <date>` с блоками
   **SUMMARY / ISSUES & TASKS / TEST PLAN / NOTES**.
3. Все изменения идут через PR; тело PR — по шаблону (см. `.github/pull_request_template.md`).
4. В коммитах ссылаться на Issue: `Refs #<номер>`.
5. CHANGELOG (`[Unreleased]`) и docs обновляются в том же PR.
