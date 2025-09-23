# Global Rules

These rules apply to all code, docs, agents, and workflows in this repository.

## Safety & privacy
- Do not include secrets, API keys, or personal data in the repo.
- Avoid collecting or storing user-identifying information unless strictly required and documented.
- Follow platform ToS and license terms for any external API or model.

## Content restrictions
- No illegal, hateful, or disallowed content. Keep examples and tests safe and neutral.

## Dependencies
- Prefer minimal, well-maintained dependencies. Document new ones in PRs.
- Pin only when necessary (e.g., to avoid known regressions) and explain why in the PR.

## Documentation
- Keep `README.md` and `docs/` up to date with behavior changes.
- Document configuration options and environment variables.

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

