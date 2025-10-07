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

// Read setting value directly from DOM (Settings dialog)
function getSettingValue(settingId) {
	try {
		// Map setting IDs to human-readable labels
		const labelMap = {
			'arena.autocache_enable': 'AutoCacheEnable',
			'arena.cache_mode': 'Cache Mode',
			'arena.cache_root': 'Cache Root',
			'arena.min_size_mb': 'Min Size',
			'arena.max_cache_gb': 'Max Cache',
			'arena.verbose_logging': 'Verbose Logging',
			'arena.discovery_mode': 'Discovery Mode',
			'arena.prefetch_strategy': 'Prefetch Strategy',
			'arena.max_concurrency': 'Max Concurrency',
			'arena.session_byte_budget': 'Session Budget',
			'arena.cooldown_ms': 'Cooldown'
		};
		
		const expectedLabel = labelMap[settingId];
		if (!expectedLabel) {
			warn(`No label mapping for ${settingId}`);
			return null;
		}
		
		// Find the row containing this label
		const rows = Array.from(document.querySelectorAll('tr, .p-field, .setting-row, div[class*="field"]'));
		
		for (const row of rows) {
			const text = (row.textContent || '').trim();
			// More flexible matching
			if (text.includes(expectedLabel) || text.toLowerCase().includes(expectedLabel.toLowerCase())) {
				// Find input/select in this row, siblings, or children
				const input = row.querySelector('input, select, textarea') || 
				              row.nextElementSibling?.querySelector('input, select, textarea') ||
				              row.parentElement?.querySelector('input, select, textarea');
				
				if (input) {
					if (input.type === 'checkbox' || input.getAttribute('role') === 'switch') {
						const checked = input.checked || input.getAttribute('aria-checked') === 'true';
						log(`  → ${settingId} (checkbox): ${checked}`);
						return checked;
					} else if (input.type === 'number') {
						const val = parseFloat(input.value) || 0;
						log(`  → ${settingId} (number): ${val}`);
						return val;
					} else if (input.type === 'text' || input.tagName === 'TEXTAREA') {
						const val = (input.value || '').trim();
						log(`  → ${settingId} (${input.type}): "${val}"`);
						return val;
					} else {
						log(`  → ${settingId} (${input.type}): ${input.value}`);
						return input.value;
					}
				}
			}
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
	name: "Arena.SettingsSaveButton",
	async setup() {
		try {
			log("Waiting for app.ui.settings...");
			await waitFor(() => app?.ui?.settings?.addSetting);
			log("app.ui.settings ready, registering settings...");

			// Register Save button FIRST (at the top)
			app.ui.settings.addSetting({
				id: "arena.aaa_save_button",
				name: "💾 Save Arena Settings",
				defaultValue: null,
				type: (name, setter, value) => {
					const tr = document.createElement("tr");
					const tdLabel = document.createElement("td");
					const tdCtrl = document.createElement("td");
					
					const btnSave = document.createElement("button");
					btnSave.textContent = "💾 Save to .env";
					btnSave.title = "Save all Arena settings to .env file";
					btnSave.style.cssText = "padding: 8px 16px; border-radius: 6px; border: 1px solid #666; background: #3a3a3a; color: #fff; cursor: pointer; font-weight: 500; width: 100%;";
					btnSave.onmouseenter = () => { btnSave.style.background = "#4a4a4a"; };
					btnSave.onmouseleave = () => { btnSave.style.background = "#3a3a3a"; };
					
					btnSave.addEventListener("click", async () => {
						try {
							log("=== SAVE BUTTON CLICKED ===");
							
							// TEMPORARY FIX: Ask user to confirm settings are correct
							const confirmSave = confirm("⚠️ Ready to save?\n\nMake sure you:\n✅ Enabled AutoCacheEnable (scroll up)\n✅ Filled Cache Root path\n\nClick OK to save all visible settings to .env file.");
							if (!confirmSave) {
								log("User cancelled save");
								return;
							}
							
							// Force enabled = true (user confirmed)
							const enabled = true;
							
							// Collect ALL text inputs from Settings dialog (fallback method)
							const allInputs = Array.from(document.querySelectorAll('.comfy-settings-dialog input[type="text"], input[type="text"]'));
							log(`Found ${allInputs.length} text inputs in Settings`);
							
							// Try to find Cache Root by scanning all text inputs for the value
							let cacheRoot = getSettingValue("arena.cache_root") || "";
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
							
							// ALL values converted to strings for backend
							const env = {
								ARENA_AUTO_CACHE_ENABLED: String(enabled ? 1 : 0),
								ARENA_AUTOCACHE_AUTOPATCH: String(enabled ? 1 : 0),
								ARENA_CACHE_MODE: String(getSettingValue("arena.cache_mode") || "ondemand"),
								ARENA_CACHE_ROOT: String(cacheRoot),
								ARENA_CACHE_MIN_SIZE_MB: String(getSettingValue("arena.min_size_mb") ?? 10),
								ARENA_CACHE_MAX_GB: String(getSettingValue("arena.max_cache_gb") ?? 0),
								ARENA_CACHE_VERBOSE: String(getSettingValue("arena.verbose_logging") ? 1 : 0),
								ARENA_CACHE_DISCOVERY: String(getSettingValue("arena.discovery_mode") || "workflow_only"),
								ARENA_CACHE_PREFETCH_STRATEGY: String(getSettingValue("arena.prefetch_strategy") || "lazy"),
								ARENA_CACHE_MAX_CONCURRENCY: String(getSettingValue("arena.max_concurrency") ?? 2),
								ARENA_CACHE_SESSION_BYTE_BUDGET: String(getSettingValue("arena.session_byte_budget") ?? 1073741824),
								ARENA_CACHE_COOLDOWN_MS: String(getSettingValue("arena.cooldown_ms") ?? 1000)
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

			// Register ALL settings (without category - let ComfyUI auto-group by id prefix)
			app.ui.settings.addSetting({ 
				id: "arena.autocache_enable", 
				name: "AutoCacheEnable", 
				type: "boolean", 
				defaultValue: false, 
				tooltip: "Enable Arena AutoCache" 
			});
			app.ui.settings.addSetting({ 
				id: "arena.cache_mode", 
				name: "Cache Mode", 
				type: "combo", 
				defaultValue: "ondemand", 
				options: ["ondemand", "disabled"],
				tooltip: "Caching mode" 
			});
			app.ui.settings.addSetting({ 
				id: "arena.cache_root", 
				name: "Cache Root", 
				type: "text", 
				defaultValue: "", 
				tooltip: "Path to cache directory (SSD)" 
			});
			app.ui.settings.addSetting({ 
				id: "arena.min_size_mb", 
				name: "Min Size (MB)", 
				type: "number", 
				defaultValue: 10, 
				tooltip: "Minimum file size to cache" 
			});
			app.ui.settings.addSetting({ 
				id: "arena.max_cache_gb", 
				name: "Max Cache (GB)", 
				type: "number", 
				defaultValue: 0, 
				tooltip: "Maximum cache size (0 = unlimited)" 
			});
			app.ui.settings.addSetting({ 
				id: "arena.verbose_logging", 
				name: "Verbose Logging", 
				type: "boolean", 
				defaultValue: false, 
				tooltip: "Enable verbose logging" 
			});
			app.ui.settings.addSetting({ 
				id: "arena.discovery_mode", 
				name: "Discovery Mode", 
				type: "combo", 
				defaultValue: "workflow_only", 
				options: ["workflow_only", "all_models"],
				tooltip: "Model discovery mode" 
			});
			app.ui.settings.addSetting({ 
				id: "arena.prefetch_strategy", 
				name: "Prefetch Strategy", 
				type: "combo", 
				defaultValue: "lazy", 
				options: ["lazy", "eager"],
				tooltip: "Prefetch strategy" 
			});
			app.ui.settings.addSetting({ 
				id: "arena.max_concurrency", 
				name: "Max Concurrency", 
				type: "number", 
				defaultValue: 2, 
				tooltip: "Max concurrent copy operations" 
			});
			app.ui.settings.addSetting({ 
				id: "arena.session_byte_budget", 
				name: "Session Budget (bytes)", 
				type: "number", 
				defaultValue: 1073741824, 
				tooltip: "Session byte budget (default 1GB)" 
			});
			app.ui.settings.addSetting({ 
				id: "arena.cooldown_ms", 
				name: "Cooldown (ms)", 
				type: "number", 
				defaultValue: 1000, 
				tooltip: "Cooldown between operations" 
			});

			log("All Arena settings registered (save button at top + 11 settings)");
		} catch (e) {
			err("Init failed", e);
		}
	}
});

log("Registered");
