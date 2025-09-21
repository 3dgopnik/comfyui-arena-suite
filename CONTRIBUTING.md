# Contributing

Thanks for your interest in improving ComfyUI Arena Suite!

This guide covers local setup, testing, and making clean pull requests.

## Prerequisites
- Python 3.10 or 3.11
- Git

## Local setup
1. Create and activate a virtual environment.
   - PowerShell: `py -3.11 -m venv .venv; . .venv/Scripts/Activate.ps1`
   - bash: `python3 -m venv .venv && source .venv/bin/activate`
2. Install the package (editable) and dev tools:
   - `pip install -e .`
   - `pip install -r requirements-dev.txt`

## Running tests
- Run all tests: `pytest -q`
- Run a specific test: `pytest tests/test_autocache_config.py::test_env_vars`

## Before opening a PR
- Ensure tests pass locally.
- Update docs under `docs/` if behavior or UX changes.
- Update `CHANGELOG.md` under the `[Unreleased]` section.
- Follow the PR template in `.github/pull_request_template.md`.

## Coding style
- Keep changes minimal and focused.
- Prefer explicit names and types.
- Match the current code layout; avoid drive-by refactors.

## Agents & nodes
- When adding agents or nodes, follow `AGENTS.md` and document inputs/outputs.
- Provide examples and, when possible, tests under `tests/`.

## Getting help
If you’re unsure about scope or approach, open a draft PR or a “Codex task” issue using the template provided.

