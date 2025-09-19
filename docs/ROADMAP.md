# Roadmap

## Release Milestones

### ✅ v0.1.0 — Foundation & Legacy Migration
**Deliverables**
- Establish the project skeleton and packaging so `ComfyUI_Arena` can be distributed as a single custom node bundle.
- Migrate legacy nodes into the new layout without altering behavior, preserving workflows documented in [How it works](./HOW_IT_WORKS.md).
- Document baseline installation paths and migration steps in the [install guide](./INSTALL.md) and project README.

**Owners**
- Core maintainers (ops + node authors).

**Dependencies**
- Access to the legacy repository artifacts and migration notes.
- Agreement on the module layout to unblock downstream configuration updates.

**Acceptance Criteria**
- Legacy users can install the suite via the documented steps without manual file moves.
- Existing workflows continue to execute successfully after migration.
- README and installation docs reflect the new package boundaries.

### ⏳ v0.2.0 — ArenaAutoCache MVP
**Deliverables**
- Ship `ArenaAutoCacheStats` and `ArenaAutoCacheTrim` nodes with full metric coverage and trimming automation described in [How it works](./HOW_IT_WORKS.md).
- Expose configuration toggles (e.g., `ARENA_CACHE_ENABLE`) and document them alongside installation updates in the [install guide](./INSTALL.md).
- Provide example cache workflows and troubleshooting notes in `custom_nodes/ComfyUI_Arena/README.md`.

**Owners**
- Cache feature squad (core maintainers coordinating with storage ops).

**Dependencies**
- Stable v0.1.0 package layout and deployment instructions.
- Access to representative datasets for cache sizing benchmarks.

**Acceptance Criteria**
- Cache hit/miss statistics and automated trimming work end-to-end with sample workflows.
- Configuration variables can be toggled per the documentation without requiring code changes.
- Troubleshooting steps cover at least the top three failure scenarios observed during testing.

### 📝 v0.3.0 — ArenaUpdater MVP
**Deliverables**
- Implement update flows for Hugging Face and CivitAI assets, surfacing status via CLI hooks referenced in [How it works](./HOW_IT_WORKS.md).
- Document updater scheduling, credentials, and rollback guidance in a new section of the [install guide](./INSTALL.md) and the upcoming updater reference.
- Integrate updater logs with cache status outputs so operators can trace asset freshness.

**Owners**
- Distribution maintainers with support from infrastructure ops.

**Dependencies**
- Successful delivery of v0.2.0 cache metrics to provide baseline observability.
- API keys or download endpoints for Hugging Face and CivitAI content.

**Acceptance Criteria**
- Automated jobs pull and apply updates from both providers within configured windows.
- Operators can trigger manual refreshes and observe progress through documented interfaces.
- Rollback steps are validated in staging and captured in the updater documentation.

### ➕ v0.4.0 — Benchmarks & UI Observability
**Deliverables**
- Benchmark I/O throughput and cache hit-rate, publishing results alongside tuning tips in the [How it works](./HOW_IT_WORKS.md#how-it-works) deep dive.
- Introduce UI nodes that display cache and updater status directly inside ComfyUI, referencing usage examples in `custom_nodes/ComfyUI_Arena/README.md`.
- Provide guidance for exporting metrics to external dashboards for long-running deployments.

**Owners**
- Performance & UI maintainers with feedback from beta operators.

**Dependencies**
- Mature AutoCache instrumentation from v0.2.0.
- Updater telemetry streams from v0.3.0 to populate UI surfaces.

**Acceptance Criteria**
- Benchmark suite runs on CI or dedicated hardware with published comparative results.
- UI nodes render real-time cache/updater state and gracefully handle disabled features.
- External monitoring integration steps validated against at least one Prometheus-compatible target.

## Planning Horizons

### Short-Term (Next Release)
- Prioritize v0.2.0 delivery to solidify caching workflows, finalize configuration docs, and collect operator feedback for the updater design.
- Coordinate with documentation owners to expand the install and troubleshooting sections referenced above.

### Mid-Term (Following Release)
- Prepare the ArenaUpdater (v0.3.0) by defining credential management, API quotas, and staging environments.
- Align cache telemetry with updater reporting so both systems share dashboards ahead of UI integration.

### Long-Term (Beyond v0.3.0)
- Explore the v0.4.0 benchmarks and UI enhancements once cache and updater foundations stabilize.
- Evaluate additional backlog items (future `➕` milestones) such as multi-instance cache coordination or packaged observability exporters.

