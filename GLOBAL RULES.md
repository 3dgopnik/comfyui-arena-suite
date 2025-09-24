# 🌍 Global Rules (универсальные)

Эти правила применяются ко всему коду, документации, агентам и рабочим процессам в репозитории.

## Общение
- Все задачи формулировать простыми словами на русском языке.
- Код и комментарии в коде писать на английском.
- Документация вести на русском (основная) и при необходимости на английском.

## Рабочий процесс
- **Одна задача = один чат = один Issue** в GitHub.
- Все шаги, комментарии, логи и прогресс фиксировать в комментариях Issue.
- Новая цель → новый чат и новый Issue.
- Коммиты должны быть маленькими и атомарными.

## Pull Requests
- Все изменения проходят через Pull Request.
- PR должен быть привязан к соответствующему Issue (`Closes #номер`).
- В PR обязательно указывать:
  * **Summary** — краткое описание цели.
  * **Changes** — список изменений.
  * **Docs** — список обновлённых документов.
  * **Changelog** — запись в `[Unreleased]`.
  * **Test Plan** — шаги тестирования и ожидаемый результат.
- Без зелёного CI PR не мержится.

## Документация
- Все изменения фиксировать в `CHANGELOG.md` (формат Keep a Changelog + SemVer).
- `ROADMAP.md` — стратегические задачи.
- `docs/ru/nodes/` — описание нод.
- `docs/examples/` — примеры.
- `docs/migration.md` — при breaking changes.
- Документация обновляется вместе с кодом в том же PR.

## Логи и отладка
- При решении проблем в Issue всегда прикладывать **фрагмент лога ошибки**.
- Лог может быть добавлен вручную в комментарий или автоматически извлечён агентом из путей, указанных в Project Rules.
- В комментариях фиксировать:
  * текст ошибки или stack trace,
  * дату/шаг возникновения,
  * результат после исправления.

## Safety & privacy
- Do not include secrets, API keys, or personal data in the repo.
- Avoid collecting or storing user-identifying information unless strictly required and documented.
- Follow platform ToS and license terms for any external API or model.

## Content restrictions
- No illegal, hateful, or disallowed content. Keep examples and tests safe and neutral.

## Dependencies
- Prefer minimal, well-maintained dependencies. Document new ones in PRs.
- Pin only when necessary (e.g., to avoid known regressions) and explain why in the PR.

## Testing
- Add or update tests under `tests/` for meaningful changes.
- Ensure CI remains green.

## Agents & nodes
- Follow `AGENTS.md` for structure, inputs/outputs, and testing guidance.
- Avoid side effects; do not perform network or disk writes outside allowed paths.

## Git and releases
- Use conventional, descriptive commit messages.
- Update `CHANGELOG.md` under `[Unreleased]` for user-visible changes.

## Development workflow
- Document all experiments and attempts in `EXPERIMENTS.md` before making changes.
- Use versioned node names for testing (e.g., `ArenaAutoCacheSmart v2.1`) while maintaining backward compatibility.
- Always check ComfyUI logs when debugging node issues: `C:\Users\acherednikov\AppData\Roaming\ComfyUI\logs\`
- Use structured debugging with clear prefixes: `[ArenaAutoCache]`, `[ComponentName]`, etc.

## Code maintenance
- Run `read_lints` after any code changes to catch syntax errors.
- Update both old and new versions of nodes when making changes.
- Keep experiments log updated with detailed technical information.
- Test backward compatibility with existing workflows before releasing changes.

## Testing instructions
- **ALWAYS provide clear step-by-step testing instructions after code changes**
- Format: "Что берем → Что подключаем → Куда нажимаем → Что ожидаем"
- Include specific node names, input/output connections, and expected results
- Document any known issues or limitations
- Keep instructions concise and actionable

