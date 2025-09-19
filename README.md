# ComfyUI Arena Suite

Custom nodes for ComfyUI with **Arena** prefix. **Single-package layout**:
- `ComfyUI_Arena/legacy` — migrated legacy nodes.
- `ComfyUI_Arena/autocache` — SSD auto-cache (WIP).
- `ComfyUI_Arena/updater` — model updater (HF/CivitAI, WIP).

## Install (ComfyUI Manager → Install from URL)
1) Copy this repo URL.
2) In ComfyUI Manager click **Install from URL**.
3) **Refresh custom nodes**.

> Manual: clone repo; the `custom_nodes/ComfyUI_Arena` folder is ready to use.
> 
## Codex workflow

1. Codex генерирует код (EN identifiers, RU comments).
2. Создаёт/обновляет Issue: `Codex: <module> — <topic> — <date>` с блоками
   **SUMMARY / ISSUES & TASKS / TEST PLAN / NOTES**.
3. Все изменения идут через PR; тело PR — по шаблону (см. `.github/pull_request_template.md`).
4. В коммитах ссылаться на Issue: `Refs #<номер>`.
5. CHANGELOG (`[Unreleased]`) и docs обновляются в том же PR.
