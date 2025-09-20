# ComfyUI Arena Suite

Custom nodes for ComfyUI with the **Arena** prefix bundled in a **single package**.

## Features overview
- **Legacy nodes** вЂ” migrated utilities that preserve the existing interfaces while living under `ComfyUI_Arena/legacy`.
- **AutoCache** — runtime patch for `folder_paths` that prefers an SSD cache, plus Config/StatsEx/Trim/Manager nodes for in-graph control (see `custom_nodes/ComfyUI_Arena/README.md`).
- **Updater scaffolding** вЂ” Hugging Face and CivitAI helpers (WIP) intended to keep local model folders in sync and manage `current` symlinks.

## System requirements
- **ComfyUI** with custom node support (tested on the current `master` branch).
- **Python 3.10+** as required by `pyproject.toml`.
- **Fast SSD storage** when enabling AutoCache to get the best throughput.
- **[ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack)** for legacy Arena nodes вЂ” install it via ComfyUI Manager or manually clone the repository so `ComfyUI-Impact-Pack/modules` is available on `PYTHONPATH`.

## Quick usage summary
1. Install the suite through **ComfyUI Manager в†’ Install from URL** using your repository URL (for example, `https://github.com/<your-org>/comfyui-arena-suite`).
2. Refresh the custom nodes list or restart ComfyUI so the new Arena nodes load.
3. Drop nodes with the **Arena** prefix into your graph to verify the installation (e.g., `ArenaAutoCacheStats`).
4. Configure SSD caching and update manifests as needed вЂ” see the documentation below for detailed steps.

## Documentation
- рџ‡·рџ‡є Р СѓСЃСЃРєР°СЏ РґРѕРєСѓРјРµРЅС‚Р°С†РёСЏ: [РћР±Р·РѕСЂ](docs/ru/index.md), [Р‘С‹СЃС‚СЂС‹Р№ СЃС‚Р°СЂС‚](docs/ru/quickstart.md), [CLI](docs/ru/cli.md), [РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ](docs/ru/config.md), [Р”РёР°РіРЅРѕСЃС‚РёРєР°](docs/ru/troubleshooting.md).
- рџ‡¬рџ‡§ English placeholders: [Overview](docs/en/index.md), [Quickstart](docs/en/quickstart.md), [CLI](docs/en/cli.md), [Configuration](docs/en/config.md),
- [Troubleshooting](docs/en/troubleshooting.md).
- [Agents rules](AGENTS.md) - guidelines for developing and integrating Codex & ComfyUI agents.

## Codex workflow
1. odex РіРµРЅРµСЂРёСЂСѓРµС‚ РєРѕРґ (EN identifiers, RU comments).
2. РЎРѕР·РґР°С‘С‚/РѕР±РЅРѕРІР»СЏРµС‚ Issue: `Codex: <module> вЂ” <topic> вЂ” <date>` СЃ Р±Р»РѕРєР°РјРё
   **SUMMARY / ISSUES & TASKS / TEST PLAN / NOTES**.
3. Р’СЃРµ РёР·РјРµРЅРµРЅРёСЏ РёРґСѓС‚ С‡РµСЂРµР· PR; С‚РµР»Рѕ PR вЂ” РїРѕ С€Р°Р±Р»РѕРЅСѓ (СЃРј. `.github/pull_request_template.md`).
4. Р’ РєРѕРјРјРёС‚Р°С… СЃСЃС‹Р»Р°С‚СЊСЃСЏ РЅР° Issue: `Refs #<РЅРѕРјРµСЂ>`.
5. CHANGELOG (`[Unreleased]`) Рё docs РѕР±РЅРѕРІР»СЏСЋС‚СЃСЏ РІ С‚РѕРј Р¶Рµ PR.


