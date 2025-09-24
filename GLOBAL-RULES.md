# 🌍 Global Rules

Универсальные правила для всех кода, документации, агентов и рабочих процессов в репозитории.

## Общение
- Все задачи формулировать простыми словами на русском языке
- Код и комментарии в коде писать на английском
- Документация вести на русском (основная) и при необходимости на английском

## Рабочий процесс
- **Одна задача = один чат = один Issue** в GitHub
- **Агент сам создает Issue** для каждой новой задачи
- **Агент создает PR только после разрешения пользователя** - всегда спрашивать перед созданием PR
- Все шаги, комментарии, логи и прогресс фиксировать в комментариях Issue
- Новая цель → новый чат и новый Issue
- Коммиты должны быть маленькими и атомарными

## Pull Requests
- **Агент создает PR только после разрешения пользователя** - всегда спрашивать перед созданием PR
- Все изменения проходят через Pull Request
- PR должен быть привязан к соответствующему Issue (`Closes #номер`)
- В PR обязательно указывать:
  * **Summary** — краткое описание цели
  * **Changes** — список изменений
  * **Docs** — список обновлённых документов
  * **Changelog** — запись в `[Unreleased]`
  * **Test Plan** — шаги тестирования и ожидаемый результат
- Без зелёного CI PR не мержится

## Документация
- Все изменения фиксировать в `CHANGELOG.md` (формат Keep a Changelog + SemVer)
- `ROADMAP.md` — стратегические задачи
- `docs/ru/nodes/` — описание нод
- `docs/examples/` — примеры
- `docs/migration.md` — при breaking changes
- Документация обновляется вместе с кодом в том же PR

## Логи и отладка
- При решении проблем в Issue всегда прикладывать **фрагмент лога ошибки**
- Лог может быть добавлен вручную в комментарий или автоматически извлечён агентом из путей, указанных в Project Rules
- В комментариях фиксировать:
  * текст ошибки или stack trace
  * дату/шаг возникновения
  * результат после исправления

## Safety & Privacy
- Do not include secrets, API keys, or personal data in the repo
- Avoid collecting or storing user-identifying information unless strictly required and documented
- Follow platform ToS and license terms for any external API or model

## Content Restrictions
- No illegal, hateful, or disallowed content. Keep examples and tests safe and neutral

## Dependencies
- Prefer minimal, well-maintained dependencies. Document new ones in PRs
- Pin only when necessary (e.g., to avoid known regressions) and explain why in the PR

## Testing
- Add or update tests under `tests/` for meaningful changes
- Ensure CI remains green

## Git and Releases
- Use conventional, descriptive commit messages
- Update `CHANGELOG.md` under `[Unreleased]` for user-visible changes

## Code Maintenance
- Run `read_lints` after any code changes to catch syntax errors
- Update both old and new versions of nodes when making changes
- Test backward compatibility with existing workflows before releasing changes

## Testing Instructions
- **ALWAYS provide clear step-by-step testing instructions after code changes**
- Format: "Что берем → Что подключаем → Куда нажимаем → Что ожидаем"
- Include specific node names, input/output connections, and expected results
- Document any known issues or limitations
- Keep instructions concise and actionable

---

# 🤖 Agent Responsibilities

## GitHub MCP
- Создание и управление Issues
- Создание и управление Pull Requests
- Извлечение логов и прикрепление к Issues
- Управление метками и статусами

## ComfyUI MCP
- Интеграция с ComfyUI canvas
- Тестирование узлов
- Отладка workflow
- Валидация конфигураций

## Logging
- Автоматическое извлечение логов из указанных путей
- Структурированное логирование с префиксами: `[ArenaAutoCache]`, `[ComponentName]`
- Прикрепление логов к Issues при отладке

## Research
- Эксперименты и исследования фиксировать через GitHub Issues с меткой `research`
- В комментариях Issues вести структуру: Проблема → Попытки → Результат → Следующие шаги
- Статусы: ✅ Успешно, ❌ Неудачно, 🔄 В процессе, ⏸ Приостановлено, 🎯 Цель достигнута

## Agent Structure
Each agent should include:
1. **Description** – A concise summary of what the agent does and why it exists
2. **Inputs & Outputs** – Define the expected inputs and outputs clearly (JSON schema for Codex tasks or socket types for ComfyUI)
3. **Setup** – Instructions on how to install dependencies and register the agent
4. **Configuration** – Environment variables or parameters the agent supports
5. **Example** – A minimal example showing how to invoke the agent

## Best Practices
- Follow the global rules: All agents must comply with the constraints above
- Type safety: Use explicit types and validations for all inputs/outputs
- Modularity: Keep agents self-contained. Shared logic should live in a common library
- Testing: Provide unit tests or integration tests under `tests/` to verify the agent's behaviour
- Documentation: Update `README.md` or the `docs/` folder with a high-level overview of new agents

## ComfyUI Custom Nodes
When implementing a custom node:
- Follow the official ComfyUI guidelines for structure, registration and dependencies
- Define your node class in `custom_nodes/` and register it via the `NODE_CLASS_MAPPINGS` dict
- List all required pip packages in a `requirements.txt` or specify `NODE_REQUIREMENTS` in the module
- Document node inputs and outputs with meaningful names and default values
- Avoid side effects; nodes should not write to disk or perform network calls outside of allowed APIs

---

This document is living – feel free to propose improvements via pull requests.
