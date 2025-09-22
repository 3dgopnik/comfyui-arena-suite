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
> - Узлы Arena AutoCache отображают подписи только на английском языке, переменные `ARENA_LANG`/`COMFYUI_LANG` игнорируются.

Custom nodes for ComfyUI with the "Arena" prefix bundled in a single package.

RU: Набор узлов Arena: наследие (legacy), SSD‑кэширование (AutoCache) и утилиты обновления — всё в одном пакете для упрощения инсталляции ComfyUI.

## Features overview
- Legacy nodes — утилиты с прежними интерфейсами под `ComfyUI_Arena/legacy`.
- AutoCache — рантайм‑патч `folder_paths` с SSD‑кэшем + узлы (Analyze/Ops/Config/StatsEx/Trim/Manager).
- Audit & Warmup — проверка и прогрев кэша по спискам или workflow JSON.
- (Отложено) UI‑оверлей был экспериментом и удалён по умолчанию для стабильности в ComfyUI Desktop. Возможное возвращение описано в ROADMAP.
- Updater scaffolding — заготовки для Hugging Face/CivitAI (WIP) с управлением симлинками `current`.

### AutoCache highlights
- Zero‑input UX: узлы `Analyze` и `Ops` работают от активного воркфлоу (пустой `workflow_json`).
- Fallback по `last_path`: если парсер не нашёл элементы в схеме, прогревается последняя использованная модель.
- Группы нод: `Arena/AutoCache/Basic`, `Advanced`, `Utils`.
- **Фильтры копирования**: автоматический пропуск мелких моделей (< 1 ГБ) и жёстко прописанных путей.
- **Визуальный индикатор**: нода `Copy Status` показывает прогресс копирования в реальном времени.

## System requirements
- ComfyUI (актуальный `master`) с поддержкой кастом‑нодов.
- Python 3.10+
- Быстрый SSD для AutoCache
- [ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack) для legacy‑узлов (добавьте `ComfyUI-Impact-Pack/modules` в `PYTHONPATH`).

## Quick usage summary
1. Установите пакет через ComfyUI Manager → "Install from URL" (`https://github.com/3dgopnik/comfyui-arena-suite`).
2. Обновите список узлов или перезапустите ComfyUI.
3. Добавьте узел из группы `Arena/AutoCache/Basic`:
   - для регулярной работы — `ArenaAutoCache Ops` (по умолчанию `audit_then_warmup`),
   - для оценки — `ArenaAutoCache Analyze` и подключите `Summary JSON` к `Show Any`,
   - для мониторинга — `ArenaAutoCache Copy Status` для отслеживания прогресса копирования.
4. По необходимости настройте SSD‑кэш (`ARENA_CACHE_ROOT`) и лимит (`ARENA_CACHE_MAX_GB`) — см. документацию ниже.

Примечание (ComfyUI Desktop): для перезагрузки фронтенда (JS‑расширений) используйте клавишу `R` в главном окне приложения. Изменения Python‑узлов требуют полного перезапуска Desktop.

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
