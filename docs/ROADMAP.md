# Roadmap

## Release Milestones

### v0.1.0 — Foundation & Legacy Migration
Deliverables
- Package skeleton so `ComfyUI_Arena` ships as a single bundle.
- Migrate legacy nodes without behaviour changes.
- Document install paths and migration steps.

Acceptance Criteria
- Legacy users can install via documented steps without manual moves.
- Existing workflows continue to work.
- README/install docs reflect final package boundaries.

### v0.2.0 — ArenaAutoCache MVP
Deliverables
- Ship “Arena AutoCache: Stats” (`ArenaAutoCacheStats`) and “Arena AutoCache: Trim” (`ArenaAutoCacheTrim`).
- Expose toggles (e.g., `ARENA_CACHE_ENABLE`) and document them.
- Provide example cache workflows and troubleshooting notes.

Acceptance Criteria
- Hit/miss statistics and trimming work end‑to‑end.
- Config variables toggle as documented.
- Troubleshooting covers top failure scenarios.

### v0.3.0 — ArenaUpdater MVP
Deliverables
- Implement update flows for Hugging Face and CivitAI assets with CLI status hooks.
- Document scheduling, credentials, and rollback guidance.
- Integrate updater logs with cache status outputs.

Acceptance Criteria
- Automated jobs pull updates within configured windows.
- Manual refresh and progress observation documented.
- Rollback steps validated in staging.

### v0.4.0 — Benchmarks & UI Observability
Deliverables
- Benchmark I/O throughput and cache hit‑rate; publish results and tuning tips.
- UI nodes rendering cache/updater status inside ComfyUI.
- Guidance for exporting metrics to external dashboards.

Acceptance Criteria
- Benchmark suite runs with published results.
- UI nodes render real‑time state and handle disabled features gracefully.
- External monitoring validated against a Prometheus‑compatible target.

## Planning Horizons

### Short‑Term (Next Release)
- Solidify caching workflows, finalize config docs, and collect feedback.

### Mid‑Term (Following Release)
- Prepare updater (credentials, quotas, staging) and align telemetry.

### Long‑Term (Beyond v0.3.0)
- Explore benchmarks and UI enhancements once foundations stabilize.
- Evaluate backlog items (e.g., multi‑instance cache coordination).

