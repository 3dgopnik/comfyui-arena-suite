# AGENTS.md

## Purpose

This document defines the guidelines for creating, integrating and maintaining automated agents (such as Codex functions and ComfyUI nodes) within the **ComfyUI Arena Suite** repository. It complements the global rules defined in `GLOBAL RULES.md` and ensures consistency, safety and maintainability across the code base.

### Scope

- Agents are any scripts, bots or workflows that automatically run tasks, either via the Codex environment or as ComfyUI custom nodes.
- This document applies to internal developers and external contributors when adding new agents or modifying existing ones.

## Agent Structure

Each agent should live in its own module or node and include:

1. **Description** – A concise summary of what the agent does and why it exists.
2. **Inputs & Outputs** – Define the expected inputs and outputs clearly (e.g. JSON schema for Codex tasks or socket types for ComfyUI).
3. **Setup** – Instructions on how to install dependencies and register the agent with the ComfyUI / Codex environment.
4. **Configuration** – Environment variables or parameters the agent supports.
5. **Example** – A minimal example showing how to invoke the agent.

## Best Practices

- **Follow the global rules**: All agents must comply with the constraints in `GLOBAL RULES.md` (e.g. avoid prohibited content, respect API usage, and maintain privacy).
- **Type safety**: Use explicit types and validations for all inputs/outputs. In ComfyUI custom nodes, document the type of each socket.
- **Modularity**: Keep agents self-contained. Shared logic should live in a common library rather than being duplicated.
- **Testing**: Provide unit tests or integration tests under `tests/` to verify the agent’s behaviour.
- **Documentation**: Update `README.md` or the `docs/` folder with a high-level overview of new agents and link back to this file.

## ComfyUI Custom Nodes

When implementing a custom node:

- Follow the official ComfyUI guidelines for structure, registration and dependencies.
- Define your node class in `custom_nodes/` and register it via the `NODE_CLASS_MAPPINGS` dict.
- List all required pip packages in a `requirements.txt` or specify `NODE_REQUIREMENTS` in the module.
- Document node inputs and outputs with meaningful names and default values.
- Avoid side effects; nodes should not write to disk or perform network calls outside of allowed APIs.

## Pull Requests

When opening a pull request that adds or modifies an agent:

- Use a conventional commit title (e.g. `feat(agent): add XYZ bot` or `docs: update AGENTS.md`).
- Fill out the PR template completely and mention any new dependencies or configuration.
- Ensure linters (ruff/black/mypy) and tests pass in CI.
- In the PR description, reference this file and explain how the new agent follows these guidelines.

---

This document is living – feel free to propose improvements via pull requests.
