# ComfyUI Arena Suite

> TL;DR — AutoCache
> - Если `ARENA_CACHE_ROOT` не задан:
>   - Windows: `%LOCALAPPDATA%\ArenaAutoCache` (например, `C:\Users\you\AppData\Local\ArenaAutoCache`)
>   - Linux/macOS: `<корень ComfyUI>/ArenaAutoCache`
> - Установите `ARENA_CACHE_ROOT=<путь>` перед запуском ComfyUI — SSD‑патч будет писать туда. Узлы Arena AutoCache (Config/Stats/Trim/Manager) покажут активную директорию.
> - Перезапустите ComfyUI после изменения переменных окружения.
> - Примеры:
>   - PowerShell: `$env:ARENA_CACHE_ROOT='D:\ComfyCache'; python main.py`
>   - CMD: `set ARENA_CACHE_ROOT=D:\ComfyCache && python main.py`
>   - bash: `ARENA_CACHE_ROOT=/mnt/ssd/cache python main.py`
> - Переопределения: `ARENA_CACHE_ENABLE=0` временно отключает патч; `ARENA_CACHE_MAX_GB=512` ограничивает размер кэша (GiB).

Custom nodes for ComfyUI with the "Arena" prefix bundled in a single package.

RU: Набор узлов Arena: наследие (legacy), SSD‑кэширование (AutoCache) и утилиты обновления — всё в одном пакете для упрощения инсталляции ComfyUI.

## Features overview
- Legacy nodes — утилиты с прежними интерфейсами под `ComfyUI_Arena/legacy`.
- AutoCache — рантайм‑патч `folder_paths` с SSD‑кэшем + узлы Config/StatsEx/Trim/Manager.
- Audit & Warmup — проверка и прогрев кэша по спискам или workflow JSON.
- AutoCache web overlay — фронтенд‑надстройка, загружается из `web/extensions/arena_autocache.js`.
- Updater scaffolding — заготовки для Hugging Face/CivitAI (WIP) с управлением симлинками `current`.

## System requirements
- ComfyUI (актуальный `master`) с поддержкой кастом‑нодов.
- Python 3.10+
- Быстрый SSD для AutoCache
- [ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack) для legacy‑узлов (добавьте `ComfyUI-Impact-Pack/modules` в `PYTHONPATH`).

## Quick usage summary
1. Установите пакет через ComfyUI Manager → "Install from URL" (`https://github.com/<your-org>/comfyui-arena-suite`).
2. Обновите список узлов или перезапустите ComfyUI.
3. Добавьте узел с префиксом "Arena" (например, "Arena AutoCache: Stats" / `ArenaAutoCacheStats`).
4. Настройте SSD‑кэш и манифесты при необходимости (см. документацию ниже).

## Documentation
- Русская документация: `docs/ru/index.md`, `docs/ru/quickstart.md`, `docs/ru/cli.md`, `docs/ru/config.md`, `docs/ru/troubleshooting.md`, `docs/ru/nodes.md`
- English placeholders: `docs/en/index.md`, `docs/en/quickstart.md`, `docs/en/cli.md`, `docs/en/config.md`, `docs/en/troubleshooting.md`
- Правила для агентов: `AGENTS.md`

## Codex workflow (RU)
1. Идентификаторы по‑английски, комментарии на русском.
2. Описывайте задачи Issue: `Codex: <module> — <topic> — <YYYY-MM-DD>` с блоками SUMMARY / ISSUES & TASKS / TEST PLAN / NOTES.
3. Делайте PR с описанием и ссылками на изменения (см. `.github/pull_request_template.md`).
4. Ссылайтесь на Issue: `Refs #<id>`.
5. Обновляйте CHANGELOG (`[Unreleased]`) и соответствующие разделы `docs` в рамках PR.

## Contributing
- См. `CONTRIBUTING.md` для локального окружения и запуска тестов.
- Следуйте `AGENTS.md` и `GLOBAL RULES.md` при добавлении агентов/узлов.
- В CI запускаются тесты на PR — держите их зелёными.

