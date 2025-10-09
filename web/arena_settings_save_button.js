// Arena Settings Save Button - Single unified interface

import { app } from "../../scripts/app.js";

// Logging helpers
const PREFIX = "[Arena Settings Save Button]";
function log(...args) { console.log(PREFIX, ...args); }
function warn(...args) { console.warn(PREFIX, ...args); }
function err(...args) { console.error(PREFIX, ...args); }

// DOM helpers
function qs(selector, root = document) { return root.querySelector(selector); }
function qsa(selector, root = document) { return Array.from(root.querySelectorAll(selector)); }

// Utility: wait for condition with timeout
async function waitFor(predicate, timeout = 10000, interval = 100) {
	const start = Date.now();
	while (Date.now() - start < timeout) {
		if (predicate()) return true;
		await new Promise(r => setTimeout(r, interval));
	}
	throw new Error("waitFor timeout");
}

// Helpers
function sanitizeNumber(value) {
    // Accept numbers with spaces or commas: "1 000", "1,000", "512".
    // Empty/invalid → null (fallback to defaults later).
    if (value === null || value === undefined) return null;
    const strRaw = String(value);
    const stripped = strRaw
        .replace(/[\u202F\u00A0\s]/g, "")
        .replace(/,/g, ".");
    if (stripped === "") return null;
    const num = Number(stripped);
    return Number.isFinite(num) ? num : null;
}

function getFromSettingsStore(settingId) {
    try {
        const s = app?.ui?.settings;
        // Try common getters used by ComfyUI
        if (typeof s?.get === 'function') {
            const v = s.get(settingId);
            if (v !== undefined && v !== null && v !== '') return v;
        }
        if (typeof s?.value === 'function') {
            const v = s.value(settingId);
            if (v !== undefined && v !== null && v !== '') return v;
        }
    } catch {}
    return null;
}

function getFromLocalStorage(settingId) {
    try {
        // 1) Known key in recent builds
        const knownKeys = [
            'Comfy.Settings',
            'comfy.settings',
            'settings',
        ];
        for (const k of knownKeys) {
            const raw = localStorage.getItem(k);
            if (!raw) continue;
            try {
                const obj = JSON.parse(raw);
                const v = obj?.[settingId];
                if (v !== undefined && v !== null && v !== '') return v;
            } catch {}
        }
        // 2) Brute-force scan
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i) || '';
            if (!/setting/i.test(key)) continue;
            try {
                const obj = JSON.parse(localStorage.getItem(key));
                const v = obj?.[settingId];
                if (v !== undefined && v !== null && v !== '') return v;
            } catch {}
        }
    } catch {}
    return null;
}

function findInputFor(settingId, expectedLabel) {
    // 1) Try direct id/name match
    const idKey = settingId.split(".").pop();
    const direct = document.querySelector(
        `#${idKey}, [id*="${idKey}"] , [name="${idKey}"], [name*="${idKey}"]`
    );
    if (direct) return direct;

    // 1.1) Try ComfyUI Settings container with data-id
    const container = document.querySelector(
        `[data-id="${settingId}"] , [data-id*="${settingId}"] , [data-id*="${idKey}"]`
    );
    if (container) {
        const inputInContainer = container.querySelector('input, select, textarea, [role="spinbutton"]');
        if (inputInContainer) return inputInContainer;
    }

    // 2) Search by label text proximity
    const rows = Array.from(document.querySelectorAll('tr, .p-field, .setting-row, div[class*="field"]'));
    for (const row of rows) {
        const text = (row.textContent || '').trim();
        if (text.includes(expectedLabel) || text.toLowerCase().includes(expectedLabel.toLowerCase())) {
            const input = row.querySelector('input, select, textarea, [role="spinbutton"]') ||
                          row.nextElementSibling?.querySelector('input, select, textarea, [role="spinbutton"]') ||
                          row.parentElement?.querySelector('input, select, textarea, [role="spinbutton"]');
            if (input) return input;
        }
    }

    // 3) Last resort: any input/select with data-id or dataset matching
    const any = Array.from(document.querySelectorAll('input, select, textarea'))
        .find(el => (el.id || '').includes(idKey) || (el.name || '').includes(idKey));
    return any || null;
}

// Read setting value using ComfyUI API + DOM fallback
async function getSettingValue(settingId) {
	try {
		// Map setting IDs to human-readable labels
		const labelMap = {
			'Arena.🔴 Enable Auto Cache': 'Enable Auto Cache',
			'Arena.🔴 Verbose Logging': 'Verbose Logging',
			'Arena.🟡 Cache Mode': 'Cache Mode',
			'Arena.🟡 Cache Directory': 'Cache Directory',
			'Arena.🟡 Min File Size (MB)': 'Min File Size (MB)',
            'Arena.🟡 Max Cache Size (GB)': 'Max Cache Size (GB)',
			'Arena.🟡 NAS Root Path': 'NAS Root Path',
			'Arena.🟡 Auto-scan NAS': 'Auto-scan NAS Structure',
			'Arena.🟡 NAS Scan Max Depth': 'NAS Scan Max Depth'
		};
        const expectedLabel = labelMap[settingId];
        if (!expectedLabel) {
            warn(`No label mapping for ${settingId}`);
            return null;
        }

        // 1) Try ComfyUI's official settings API (most reliable for PrimeVue InputNumber)
        try {
            if (app?.extensionManager?.setting?.get) {
                const apiValue = await app.extensionManager.setting.get(settingId);
                if (apiValue !== undefined && apiValue !== null) {
                    log(`  → ${settingId} (API): ${apiValue}`);
                    return apiValue;
                }
            }
        } catch (e) {
            warn(`Failed to read from settings API for ${settingId}:`, e);
        }

        // 2) Force commit DOM values before reading (for PrimeVue InputNumber timing issues)
        if (settingId.includes('max_cache_gb') || settingId.includes('min_size_mb') || 
            settingId.includes('max_concurrency') || settingId.includes('session_byte_budget') || 
            settingId.includes('cooldown_ms')) {
            document.activeElement?.blur(); // Force commit in-flight value
            await new Promise(resolve => setTimeout(resolve, 50)); // Small delay for DOM update
        }

        // 3) Try official store/localStorage
        if (settingId === 'arena.max_cache_gb') {
            const storeVal = getFromSettingsStore(settingId) ?? getFromLocalStorage(settingId);
            const storeNum = sanitizeNumber(storeVal);
            if (storeNum !== null) {
                log(`  → ${settingId} (store): ${storeNum}`);
                return storeNum;
            }
        }

        // 4) Fallback to DOM parsing (after commit)
        let input = findInputFor(settingId, expectedLabel);
        // Hard fallback for max_cache_gb which misbehaves in some builds
        if (!input && settingId === 'arena.max_cache_gb') {
            input = document.querySelector('[data-id="arena.max_cache_gb"] input, [data-id*="max_cache_gb"] input');
        }
        if (input) {
            if (input.type === 'checkbox' || input.getAttribute('role') === 'switch') {
                const checked = input.checked || input.getAttribute('aria-checked') === 'true';
                log(`  → ${settingId} (checkbox): ${checked}`);
                return checked;
            }
            // Try multiple sources for value: value, aria-valuenow, aria-valuetext, textContent (for combos)
            let raw = (input.value ?? '').toString();
            if (!raw) raw = input.getAttribute?.('aria-valuenow') || '';
            if (!raw) raw = input.getAttribute?.('aria-valuetext') || '';
            if (!raw) {
                // Some combo buttons store current text inside a button
                const container = input.closest('[data-id], tr, .p-field, .setting-row, div');
                const btn = container?.querySelector('button[aria-haspopup="listbox"], .p-dropdown, .p-select, [role="combobox"]');
                const btnText = btn?.textContent?.trim();
                if (btnText) raw = btnText;
                // PrimeVue InputNumber fallback by class
                if (!raw) {
                    const numInput = container?.querySelector('input.p-inputnumber-input, input[inputmode="numeric"], input[type="text"][aria-valuenow]');
                    const nv = numInput?.value || numInput?.getAttribute?.('aria-valuenow') || '';
                    if (nv) raw = nv;
                }
                // Last resort: extract first number-like token from container text
                if (!raw && container?.textContent) {
                    const m = container.textContent.replace(/\s+/g, ' ').match(/(-?\d+[\s,\.]?\d*)/);
                    if (m && m[1]) raw = m[1];
                }
            }
            if (input.type === 'number') {
                const num = sanitizeNumber(raw);
                log(`  → ${settingId} (number): ${num}`);
                return num; // may be null → handled by defaults later
            }
            if (settingId.endsWith('max_cache_gb') || settingId.endsWith('min_size_mb') ||
                settingId.endsWith('max_concurrency') || settingId.endsWith('session_byte_budget') ||
                settingId.endsWith('cooldown_ms')) {
                const num = sanitizeNumber(raw);
                log(`  → ${settingId} (text->number): ${num}`);
                return num; // may be null → handled by defaults later
            }
            const val = raw.trim();
            if (val === "") return null;
            log(`  → ${settingId}: "${val}"`);
            return val;
        }
	} catch (e) {
		err(`Failed to get ${settingId}:`, e);
	}
	warn(`Setting ${settingId} not found in DOM`);
	return null;
}

// POST JSON helper
async function postJson(url, payload) {
	const res = await fetch(url, { 
		method: "POST", 
		headers: { "Content-Type": "application/json" }, 
		body: JSON.stringify(payload) 
	});
	return res;
}

log("Loading...");
app.registerExtension({
	name: "Arena AutoCache Settings",
	async setup() {
		try {
			log("Waiting for app.ui.settings...");
			await waitFor(() => app?.ui?.settings?.addSetting);
			log("app.ui.settings ready, registering settings...");

            // Ensure a little right padding so inputs don't stick to the scrollbar
            try {
                const STYLE_ID = "arena-settings-right-padding";
                if (!document.getElementById(STYLE_ID)) {
                    const style = document.createElement("style");
                    style.id = STYLE_ID;
                    style.textContent = `
                        .comfy-settings-dialog tr > td:last-child { padding-right: 80px !important; }
                        .comfy-settings-dialog .setting-row > td:last-child { padding-right: 80px !important; }
                    `;
                    document.head.appendChild(style);
                }
            } catch {}

			// Register ALL settings (without category - let ComfyUI auto-group by id prefix)
			app.ui.settings.addSetting({ 
				id: "Arena.🔴 Enable Auto Cache", 
				name: "Enable Auto Cache", 
				type: "boolean", 
				defaultValue: false, 
				tooltip: "Enable automatic caching" 
			});
			app.ui.settings.addSetting({ 
				id: "Arena.🔴 Verbose Logging", 
				name: "Verbose Logging", 
				type: "boolean", 
				defaultValue: false, 
				tooltip: "Enable detailed cache logging" 
			});
			app.ui.settings.addSetting({ 
				id: "Arena.🟡 Cache Mode", 
				name: "Cache Mode", 
				type: "combo", 
				defaultValue: "ondemand", 
				options: ["ondemand", "disabled"],
				tooltip: "Caching mode (on-demand / always / off)" 
			});
			app.ui.settings.addSetting({ 
				id: "Arena.🟡 Cache Directory", 
				name: "Cache Directory", 
				type: "text", 
				defaultValue: "", 
				tooltip: "Directory for cache storage" 
			});
			// NEW: NAS path management (hybrid auto-scan + YAML fallback)
			app.ui.settings.addSetting({
				id: "Arena.🟡 NAS Root Path",
				name: "NAS Root Path",
				type: "text",
				defaultValue: "",
				tooltip: "Root path to NAS models (e.g. \\nas-3d\\Visual\\Lib\\SDModels). Leave empty to use extra_model_paths.yaml"
			});
			app.ui.settings.addSetting({
				id: "Arena.🟡 Auto-scan NAS",
				name: "Auto-scan NAS Structure",
				type: "boolean",
				defaultValue: true,
				tooltip: "Automatically scan NAS and register model paths on startup"
			});
			app.ui.settings.addSetting({
				id: "Arena.🟡 NAS Scan Max Depth",
				name: "NAS Scan Max Depth",
				type: "number",
				defaultValue: 3,
				tooltip: "Maximum recursion depth for NAS scanning (0=base only, 3=3 levels deep)"
			});
			app.ui.settings.addSetting({ 
				id: "Arena.🟡 Min File Size (MB)", 
				name: "Min File Size (MB)", 
				type: "number", 
				defaultValue: 1, 
				tooltip: "Minimum file size for caching and NAS scanning (1MB = embeddings, 10MB = models)" 
			});
			app.ui.settings.addSetting({ 
				id: "Arena.🟡 Max Cache Size (GB)", 
				name: "Max Cache Size (GB)", 
				type: "number", 
				defaultValue: 0, 
				tooltip: "Maximum cache size in gigabytes" 
			});

			// Button: Restore extra_model_paths.yaml from template
			app.ui.settings.addSetting({
				id: "Arena.🟢 Restore YAML",
				name: "Restore YAML File",
				defaultValue: null,
				type: (name, setter, value) => {
					const tr = document.createElement("tr");
					
					// Create empty label cell (hidden)
					const tdLabel = document.createElement("td");
					tdLabel.style.display = "none";
					
					// Create control cell with centered button
					const tdCtrl = document.createElement("td");
					tdCtrl.style.textAlign = "center";
					tdCtrl.style.padding = "20px 0";
					tdCtrl.style.width = "100%";
					
					const btnRestore = document.createElement("button");
					btnRestore.textContent = "Restore";
					btnRestore.title = "Restore Electron extra_model_paths.yaml from Arena template";
					btnRestore.style.cssText = "padding: 12px 48px; border-radius: 6px; border: 1px solid #666; background: #346599; color: #fff; cursor: pointer; font-weight: 500; font-size: 14px; min-width: 200px;";
					btnRestore.onmouseenter = () => { btnRestore.style.background = "#3b77b8"; };
					btnRestore.onmouseleave = () => { btnRestore.style.background = "#346599"; };
					btnRestore.onmousedown = () => { btnRestore.style.background = "#1d5086"; };
					btnRestore.onmouseup = () => { btnRestore.style.background = "#3b77b8"; };
					
					btnRestore.addEventListener("click", async () => {
						try {
							const res = await fetch('/arena/restore_yaml', { method: 'POST' });
							const data = await res.json().catch(() => ({}));
							if (res.ok && data?.status === 'success') {
								alert(`✅ ${data.message || 'YAML restored successfully'}`);
							} else {
								alert(`❌ Restore failed: ${data?.message || res.status}`);
							}
						} catch (e) {
							alert('❌ Restore failed: ' + e.message);
						}
					});
					
					tdCtrl.appendChild(btnRestore);
					tr.appendChild(tdLabel);
					tr.appendChild(tdCtrl);
					return tr;
				}
			});

			// Register Save button (at the bottom)
			app.ui.settings.addSetting({
				id: "Arena.🟢 Save Settings",
				name: "Save Settings",
				defaultValue: null,
				type: (name, setter, value) => {
					const tr = document.createElement("tr");
					
					// Create empty label cell (hidden)
					const tdLabel = document.createElement("td");
					tdLabel.style.display = "none";
					
					// Create control cell with centered button
					const tdCtrl = document.createElement("td");
					tdCtrl.style.textAlign = "center";
					tdCtrl.style.padding = "20px 0";
					tdCtrl.style.width = "100%";
					
					const btnSave = document.createElement("button");
					btnSave.textContent = "Save";
					btnSave.title = "Save all Arena settings to .env file";
					btnSave.style.cssText = "padding: 12px 48px; border-radius: 6px; border: 1px solid #666; background: #346599; color: #fff; cursor: pointer; font-weight: 500; font-size: 14px; min-width: 200px;";
					btnSave.onmouseenter = () => { btnSave.style.background = "#3b77b8"; };
					btnSave.onmouseleave = () => { btnSave.style.background = "#346599"; };
					btnSave.onmousedown = () => { btnSave.style.background = "#1d5086"; };
					btnSave.onmouseup = () => { btnSave.style.background = "#3b77b8"; };
					
                    btnSave.addEventListener("click", async () => {
						try {
							log("=== SAVE BUTTON CLICKED ===");
							
							// TEMPORARY FIX: Ask user to confirm settings are correct
							const confirmSave = confirm("⚠️ Ready to save?\n\nMake sure you:\n✅ Enabled AutoCacheEnable (scroll up)\n✅ Filled Cache Root path\n\nClick OK to save all visible settings to .env file.");
							if (!confirmSave) {
								log("User cancelled save");
								return;
							}
							
						// Default to disabled (user must explicitly enable via Arena button)
							const enabled = false;
							
						// Collect ALL text inputs from Settings dialog (fallback method)
							const allInputs = Array.from(document.querySelectorAll('.comfy-settings-dialog input[type="text"], input[type="text"]'));
							log(`Found ${allInputs.length} text inputs in Settings`);
							
							// Try to find Cache Root by scanning all text inputs for the value
						let cacheRoot = await getSettingValue("Arena.🟡 Cache Directory") || "";
						if (!cacheRoot) {
							// Fallback: find the first non-empty text input that looks like a path
							for (const input of allInputs) {
								const val = (input.value || '').trim();
								if (val && (val.includes('\\') || val.includes('/') || val.includes(':'))) {
									log(`Found potential cache_root: "${val}"`);
									cacheRoot = val;
									break;
								}
							}
						}

						// Read NAS settings
						const nasRoot = (await getSettingValue("Arena.🟡 NAS Root Path")) || "";
						const autoScan = !!(await getSettingValue("Arena.🟡 Auto-scan NAS"));
							
                            // Load existing .env to avoid overwriting with empty values
                            let existingEnv = {};
                            try {
                                const cur = await fetch('/arena/env');
                                if (cur.ok) {
                                    const data = await cur.json();
                                    existingEnv = data?.env || {};
                                }
                            } catch {}

                            const setOrKeep = (key, value, fallback) => {
                                if (value === null || value === undefined || value === "") {
                                    return existingEnv[key] ?? String(fallback);
                                }
                                return String(value);
                            };

                            // Resolve values from UI using ComfyUI API + DOM fallback
                            const ui_cache_mode = await getSettingValue("Arena.🟡 Cache Mode");
                            const ui_min_size = sanitizeNumber(await getSettingValue("Arena.🟡 Min File Size (MB)"));
                            let ui_max_gb = sanitizeNumber(await getSettingValue("Arena.🟡 Max Cache Size (GB)"));
                            if (ui_max_gb === null) {
                                try {
                                    const manual = prompt("Enter Max Cache (GB)", "");
                                    const mnum = sanitizeNumber(manual);
                                    if (mnum !== null) ui_max_gb = mnum;
                                } catch {}
                            }
                            const ui_verbose = await getSettingValue("Arena.🔴 Verbose Logging");
							const nasScanMaxDepth = await getSettingValue("Arena.🟡 NAS Scan Max Depth");

                            // Build env with merge semantics (keep previous if UI not readable)
							const env = {
                                ARENA_AUTO_CACHE_ENABLED: "0", // Always disabled by default
                                ARENA_AUTOCACHE_AUTOPATCH: "0", // Always disabled by default
                                ARENA_CACHE_MODE: setOrKeep("ARENA_CACHE_MODE", ui_cache_mode, "ondemand"),
                                ARENA_CACHE_ROOT: setOrKeep("ARENA_CACHE_ROOT", cacheRoot, existingEnv["ARENA_CACHE_ROOT"] || ""),
                                ARENA_CACHE_MIN_SIZE_MB: setOrKeep("ARENA_CACHE_MIN_SIZE_MB", ui_min_size, 1),
                                ARENA_CACHE_MAX_GB: setOrKeep("ARENA_CACHE_MAX_GB", ui_max_gb, 0),
								ARENA_CACHE_VERBOSE: setOrKeep("ARENA_CACHE_VERBOSE", ui_verbose ? 1 : 0, 0),
								ARENA_NAS_ROOT: setOrKeep("ARENA_NAS_ROOT", nasRoot, existingEnv["ARENA_NAS_ROOT"] || ""),
								ARENA_NAS_AUTO_SCAN: setOrKeep("ARENA_NAS_AUTO_SCAN", autoScan ? 1 : 0, existingEnv["ARENA_NAS_AUTO_SCAN"] ?? 1),
								ARENA_NAS_SCAN_MAX_DEPTH: setOrKeep("ARENA_NAS_SCAN_MAX_DEPTH", nasScanMaxDepth, 3)
                            };
							
							log("Saving to /arena/env", env);
							const res = await postJson("/arena/env", { env });
							log("Response status:", res.status, "ok:", res.ok);
							
							if (res.ok) {
								const responseData = await res.json();
								log("Response data:", responseData);
								alert(`✅ Settings saved to .env successfully!\n\nPath: C:\\ComfyUI\\user\\arena_autocache.env\n\nDetails: ${responseData.message || 'OK'}`);
							} else {
								const errorText = await res.text();
								err("Save failed response:", errorText);
								alert(`❌ Save failed (HTTP ${res.status})\n\n${errorText}`);
							}
						} catch (e) { 
							err("Save failed", e); 
							alert("❌ Save failed: " + e.message); 
						}
					});

					tdCtrl.appendChild(btnSave);
					tr.appendChild(tdLabel);
					tr.appendChild(tdCtrl);
					return tr;
				}
			});

			log("All Arena settings registered (save button at bottom + 6 settings)");
		} catch (e) {
			err("Init failed", e);
		}
	}
});

log("Registered");
