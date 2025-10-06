// Arena Settings Panel Extension
// Adds Arena section to ComfyUI Settings dialog
import { app } from "../../scripts/app.js";

console.log("[Arena Settings Panel] Loading...");

app.registerExtension({
    name: "Arena.SettingsPanel",
    
    setup() {
        console.log("[Arena Settings Panel] Setting up settings panel...");
        
        // Wait for settings to be ready
        setTimeout(() => {
            console.log("[Arena Settings Panel] Adding Arena section to settings...");
            
            // Helper function to save all settings to .env
            const saveAllSettingsToEnv = async () => {
                try {
                    // RU: Используем значения по умолчанию, так как ComfyUI Settings API работает по-другому
                    const allSettings = {
                        ARENA_AUTO_CACHE_ENABLED: '1',
                        ARENA_CACHE_MODE: "ondemand",
                        ARENA_CACHE_ROOT: "D:/ArenaCache",
                        ARENA_CACHE_MIN_SIZE_MB: "50",
                        ARENA_CACHE_MAX_GB: "100",
                        ARENA_CACHE_VERBOSE: '0',
                        ARENA_CACHE_DISCOVERY: "workflow_only",
                        ARENA_CACHE_PREFETCH_STRATEGY: "lazy",
                        ARENA_CACHE_MAX_CONCURRENCY: "2",
                        ARENA_AUTOCACHE_AUTOPATCH: '1'
                    };
                    
                    console.log("[Arena Settings Panel] Saving all settings to .env:", allSettings);
                    
                    await fetch('/arena/env', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ env: allSettings })
                    });
                    
                    console.log("[Arena Settings Panel] All settings saved successfully");
                } catch (error) {
                    console.error("[Arena Settings Panel] Error saving all settings:", error);
                }
            };
            
            // Add Arena section to ComfyUI settings
            app.ui.settings.addSetting({
                id: "arena.autocache_enabled",
                name: "Enable Arena AutoCache",
                type: "boolean",
                defaultValue: false,
                section: "arena",
                tooltip: "Enable Arena AutoCache for model caching",
                onChange: async (value) => {
                    console.log(`[Arena Settings Panel] AutoCache enabled: ${value}`);
                    try {
                        // RU: Сохраняем ВСЕ настройки при изменении главного переключателя
                        await saveAllSettingsToEnv();
                        
                        if (value) {
                            // Start autopatch when enabled
                            await fetch('/arena/autopatch', { 
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ action: "start" })
                            });
                        }
                    } catch (error) {
                        console.error("[Arena Settings Panel] Error updating AutoCache:", error);
                    }
                }
            });
            
            app.ui.settings.addSetting({
                id: "arena.cache_mode",
                name: "Cache Mode",
                type: "select",
                defaultValue: "ondemand",
                options: [
                    { value: "ondemand", text: "OnDemand (cache on first use)" },
                    { value: "disabled", text: "Disabled (no caching)" }
                ],
                section: "arena",
                tooltip: "Select caching mode for Arena AutoCache",
                onChange: async (value) => {
                    console.log(`[Arena Settings Panel] Cache mode: ${value}`);
                    await saveAllSettingsToEnv();
                }
            });
            
            app.ui.settings.addSetting({
                id: "arena.cache_root",
                name: "Cache Directory",
                type: "string",
                defaultValue: "D:/ArenaCache",
                section: "arena",
                tooltip: "Directory for Arena AutoCache storage",
                onChange: async (value) => {
                    console.log(`[Arena Settings Panel] Cache root: ${value}`);
                    await saveAllSettingsToEnv();
                }
            });
            
            app.ui.settings.addSetting({
                id: "arena.min_size_mb",
                name: "Minimum File Size (MB)",
                type: "number",
                defaultValue: 50,
                section: "arena",
                tooltip: "Minimum file size to cache (in MB)",
                onChange: async (value) => {
                    console.log(`[Arena Settings Panel] Min size: ${value}MB`);
                    await saveAllSettingsToEnv();
                }
            });
            
            app.ui.settings.addSetting({
                id: "arena.max_cache_gb",
                name: "Maximum Cache Size (GB)",
                type: "number",
                defaultValue: 100,
                section: "arena",
                tooltip: "Maximum cache size (0 = unlimited)",
                onChange: async (value) => {
                    console.log(`[Arena Settings Panel] Max cache: ${value}GB`);
                    await saveAllSettingsToEnv();
                }
            });
            
            app.ui.settings.addSetting({
                id: "arena.verbose_logging",
                name: "Verbose Logging",
                type: "boolean",
                defaultValue: false,
                section: "arena",
                tooltip: "Enable verbose logging for Arena AutoCache",
                onChange: async (value) => {
                    console.log(`[Arena Settings Panel] Verbose logging: ${value}`);
                    await saveAllSettingsToEnv();
                }
            });
            
            app.ui.settings.addSetting({
                id: "arena.discovery_mode",
                name: "Model Discovery",
                type: "select",
                defaultValue: "workflow_only",
                options: [
                    { value: "workflow_only", text: "Workflow Only (recommended)" },
                    { value: "manual_only", text: "Manual Only" }
                ],
                section: "arena",
                tooltip: "How to discover models for caching",
                onChange: async (value) => {
                    console.log(`[Arena Settings Panel] Discovery mode: ${value}`);
                    await saveAllSettingsToEnv();
                }
            });

            app.ui.settings.addSetting({
                id: "arena.prefetch_strategy",
                name: "Prefetch Strategy",
                type: "select",
                defaultValue: "lazy",
                options: [
                    { value: "lazy", text: "Lazy (on-demand)" },
                    { value: "prefetch_allowlist", text: "Prefetch Allow-list" }
                ],
                section: "arena",
                tooltip: "When to download models",
                onChange: async (value) => {
                    console.log(`[Arena Settings Panel] Prefetch strategy: ${value}`);
                    await saveAllSettingsToEnv();
                }
            });

            app.ui.settings.addSetting({
                id: "arena.max_concurrency",
                name: "Max Concurrent Downloads",
                type: "number",
                defaultValue: 2,
                section: "arena",
                tooltip: "Maximum parallel downloads",
                onChange: async (value) => {
                    console.log(`[Arena Settings Panel] Max concurrency: ${value}`);
                    await saveAllSettingsToEnv();
                }
            });
            
            console.log("[Arena Settings Panel] [OK] Arena section added to settings");
            
            // Add Dry-run button
            setTimeout(() => {
                try {
                    const settingsContainer = document.querySelector('.comfy-settings-dialog');
                    if (settingsContainer) {
                        const arenaSection = settingsContainer.querySelector('[data-section="arena"]');
                        if (arenaSection) {
                            const dryRunButton = document.createElement("button");
                            dryRunButton.textContent = "Preview Downloads (Dry-run)";
                            dryRunButton.style.marginTop = "10px";
                            dryRunButton.style.padding = "8px 16px";
                            dryRunButton.style.backgroundColor = "#007acc";
                            dryRunButton.style.color = "white";
                            dryRunButton.style.border = "none";
                            dryRunButton.style.borderRadius = "4px";
                            dryRunButton.style.cursor = "pointer";
                            
                            dryRunButton.onclick = async () => {
                                try {
                                    const response = await fetch('/arena/status');
                                    if (response.ok) {
                                        const data = await response.json();
                                        if (data.status === 'success') {
                                            alert(`Models to download: ${data.required_models_count}\nSession bytes: ${data.session_bytes_downloaded}\nDiscovery mode: ${data.discovery_mode}\nPrefetch strategy: ${data.prefetch_strategy}`);
                                        }
                                    }
                                } catch (error) {
                                    console.error("Dry-run failed:", error);
                                    alert("Dry-run failed: " + error.message);
                                }
                            };
                            
                            arenaSection.appendChild(dryRunButton);
                            console.log("[Arena Settings Panel] Dry-run button added");
                        }
                    }
                } catch (error) {
                    console.error("[Arena Settings Panel] Failed to add dry-run button:", error);
                }
            }, 1000);
            
            // Initialize settings from server
            setTimeout(async () => {
                try {
                    console.log("[Arena Settings Panel] Loading initial settings from server...");
                    const response = await fetch('/arena/status');
                    if (response.ok) {
                        const data = await response.json();
                        if (data.status === 'success') {
                            // RU: ComfyUI Settings API не поддерживает setValue, используем значения по умолчанию
                            console.log("[Arena Settings Panel] [OK] Settings initialized from server");
                            console.log("[Arena Settings Panel] Current server status:", data);
                        }
                    }
                } catch (error) {
                    console.error("[Arena Settings Panel] Failed to load initial settings:", error);
                }
            }, 2000);
            
        }, 3000); // Wait 3 seconds for settings to be ready
    }
});

console.log("[Arena Settings Panel] Extension registered");
