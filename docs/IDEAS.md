# Ideas

| id | title | area | score | status |
| --- | --- | --- | --- | --- |
| 2024-05-03-ops-ui | Expose per-mode presets for Arena AutoCache Ops to speed up common automation flows | AutoCache | 0.6 | proposed |
| 2024-05-03-benchmark-cli | Add a CLI wrapper around the Ops benchmarking logic for headless cache health checks | Tooling | 0.5 | proposed |
| 2024-05-04-audit-extended | Implement extended stats computation and settings overrides within the AutoCache Audit node | AutoCache | 0.4 | done |
| 2024-05-06-audit-presets | Ship reusable UI presets for common audit flows (stats only, trim only, audit+config) | AutoCache | 0.3 | proposed |
| 2024-05-06-summary-webhook | Allow summary_json payloads to be pushed to a webhook for external monitoring dashboards | Integrations | 0.5 | proposed |
| 2024-05-10-ops-mode-tooltips | Surface per-mode explanations directly in the Ops node UI to guide new operators | AutoCache | 0.4 | proposed |
| 2024-05-10-ops-mode-preset | Offer saved presets that preconfigure Ops node inputs for nightly trim or warmup-only runs | AutoCache | 0.5 | proposed |
| 2024-05-12-overlay-history | Persist AutoCache overlay snapshots per execution to review audit/warmup trends | AutoCache | 0.4 | proposed |
| 2024-05-12-overlay-settings | Expose overlay color and threshold tuning in a dedicated settings panel | UX | 0.5 | proposed |
| 2024-05-13-overlay-toggle | Offer a per-node hotkey or checkbox to temporarily hide the AutoCache overlay during graph editing | UX | 0.3 | proposed |
| 2024-05-13-overlay-export | Provide a small export panel that copies the latest summary and progress metrics from the overlay to the clipboard | Tooling | 0.4 | proposed |
| 2024-05-15-ui-schema-validator | Ship a lightweight CLI that diffs stored AutoCache payload schemas to catch breaking changes early | Testing | 0.4 | proposed |
| 2024-05-15-ui-payload-examples | Publish curated summary_json/warmup_json/trim_json samples in the docs for integrators | Docs | 0.3 | proposed |
| 2024-05-16-overlay-idle-animation | Add a subtle fade transition when the AutoCache overlay returns to the idle palette to emphasize recovery | UX | 0.2 | proposed |
| 2024-05-18-web-assets-check | Add an integration check that ensures the Arena web overlay assets are discoverable after installation | Testing | 0.3 | proposed |
| 2024-05-19-overlay-alias-config | Allow the overlay alias list to be extended from a user config file for niche deployments | UX | 0.3 | proposed |
| 2024-05-19-overlay-i18n-tooling | Build a CLI helper that replays localized payload samples against the overlay to guard translations | Testing | 0.4 | proposed |
| 2024-05-20-cache-env-ui | Provide a tiny Windows tray helper that toggles ARENA_CACHE_* variables and updates the current session | Tooling | 0.3 | proposed |
| 2024-05-21-cache-selector-cli | Offer a cross-platform CLI prompt for selecting the Arena cache directory when Windows dialogs are unavailable | Tooling | 0.2 | proposed |
| 2024-05-22-bootstrap-healthcheck | Add a smoke test script that validates persisted ARENA_CACHE_* variables and disk free space after running the bootstrap | Tooling | 0.3 | proposed |
| 2024-05-22-bootstrap-gui | Build a small WinUI front-end for managing Arena cache limits and toggles beyond the initial bootstrap | UX | 0.4 | proposed |
| 2024-05-23-bootstrap-escape-check | Add automated validation that cache paths ending with backslashes are safely escaped before persistence | Tooling | 0.2 | proposed |
| 2024-05-24-bootstrap-status-telemetry | Collect anonymous success metrics for the WinForms bootstrap helper to guide UX polish | Tooling | 0.2 | proposed |
| 2024-05-24-bootstrap-cli-tests | Automate CLI fallback smoke tests to verify bootstrap prompts on systems without PowerShell | Testing | 0.3 | proposed |
| 2024-05-25-legacy-healthcheck | Add a startup health check that reports which Arena submodules failed to load and why | Reliability | 0.3 | proposed |
| 2024-05-25-legacy-shim | Provide lightweight shim nodes that explain legacy dependencies when the module is missing | UX | 0.2 | proposed |
