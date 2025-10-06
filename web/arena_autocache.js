// Arena AutoCache Extension v4.1 - Conditional UI Management with .env sync
// Provides dynamic widget visibility control for Arena AutoCache nodes

console.log("[Arena AutoCache Extension v4.1] Loading...");

// Wait for app to be available
let extensionRegistered = false;
function waitForApp() {
    if (typeof app !== 'undefined' && app.registerExtension && !extensionRegistered) {
        // Check if extension is already registered
        if (window.arenaAutoCacheExtensionRegistered) {
            console.log("[Arena AutoCache Extension v4] Extension already registered, skipping...");
            return;
        }
        
        console.log("[Arena AutoCache Extension v4.1] App is ready, registering extension...");
        registerArenaAutoCache();
        extensionRegistered = true;
        window.arenaAutoCacheExtensionRegistered = true;
    } else if (!extensionRegistered) {
        console.log("[Arena AutoCache Extension v4] App not ready, waiting...");
        setTimeout(waitForApp, 100);
    }
}

function registerArenaAutoCache() {
// Register extension for conditional UI management
app.registerExtension({
    name: "ArenaAutoCache.ConditionalUI",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // Target only Arena AutoCache nodes
        if (nodeType.comfyClass === "ArenaAutoCacheSimple") {
            console.log("[Arena AutoCache] Registering conditional UI for ArenaAutoCacheSimple");
            
            // Store original onNodeCreated method
            const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
            
            // Override onNodeCreated to set up conditional UI
            nodeType.prototype.onNodeCreated = function() {
                // Call original method
                const result = originalOnNodeCreated?.apply(this, arguments);
                
                // Set up conditional UI management
                this.setupConditionalUI();
                
                return result;
            };
            
            // Add method to set up conditional UI
            nodeType.prototype.setupConditionalUI = function() {
                // Find enable_caching widget
                const enableCachingWidget = this.widgets.find(w => w.name === "enable_caching");
                if (!enableCachingWidget) {
                    console.warn("[Arena AutoCache] enable_caching widget not found");
                    return;
                }
                
                // Store reference to enable_caching widget
                this.enableCachingWidget = enableCachingWidget;
                
                // Set up button handlers for .env operations
                this.setupEnvButtonHandlers();
                
                // Auto-load settings from .env file if it exists
                this.autoLoadFromEnv();
                
                // List of widgets to hide/show based on enable_caching
                this.conditionalWidgets = this.widgets.filter(w => 
                    w.name !== "enable_caching" && 
                    w.name !== "unique_id" && 
                    w.name !== "prompt" && 
                    w.name !== "extra_pnginfo"
                );
                
                // Initial visibility update
                this.updateWidgetVisibility();
                
                // Listen for value changes
                const originalCallback = enableCachingWidget.callback;
                enableCachingWidget.callback = (value) => {
                    // Call original callback if exists
                    if (originalCallback) {
                        originalCallback.call(this, value);
                    }
                    
                    // Update widget visibility
                    this.updateWidgetVisibility();
                    
                    // Force node redraw
                    this.setDirtyCanvas(true);
                };
                
                console.log("[Arena AutoCache] Conditional UI setup complete");
            };
            
            // Add method to auto-load settings from .env file
            nodeType.prototype.autoLoadFromEnv = async function() {
                try {
                    console.log("[Arena AutoCache] Auto-loading settings from .env file...");
                    
                    const response = await fetch('/arena/env');
                    const result = await response.json();
                    
                    if (result.status === 'success' && result.env) {
                        console.log("[Arena AutoCache] .env file found, loading settings:", result.env);
                        this.applyEnvData(result.env);
                        this.showNotification("[OK] Settings loaded from .env file automatically!");
                    } else {
                        console.log("[Arena AutoCache] No .env file found, using defaults");
                    }
                } catch (error) {
                    console.log("[Arena AutoCache] No .env file available, using defaults:", error.message);
                }
            };
            
            // Add method to update widget visibility
            nodeType.prototype.updateWidgetVisibility = function() {
                if (!this.enableCachingWidget || !this.conditionalWidgets) {
                    return;
                }
                
                const isEnabled = this.enableCachingWidget.value;
                
                this.conditionalWidgets.forEach(widget => {
                    const widgetElement = this.widgets.find(w => w === widget)?.parent;
                    if (widgetElement) {
                        // Find the actual DOM element for this widget
                        const widgetEl = this.element.querySelector(`[data-widget-name="${widget.name}"]`);
                        if (widgetEl) {
                            if (isEnabled) {
                                widgetEl.style.display = '';
                                widgetEl.style.visibility = 'visible';
                            } else {
                                widgetEl.style.display = 'none';
                                widgetEl.style.visibility = 'hidden';
                            }
                        }
                    }
                });
                
                console.log(`[Arena AutoCache] Widget visibility updated: ${isEnabled ? 'shown' : 'hidden'}`);
            };
            
            // Add method to set up .env button handlers
            nodeType.prototype.setupEnvButtonHandlers = function() {
                // Find save_env_now widget
                const saveEnvWidget = this.widgets.find(w => w.name === "save_env_now");
                if (saveEnvWidget) {
                    const originalCallback = saveEnvWidget.callback;
                    saveEnvWidget.callback = (value) => {
                        if (originalCallback) {
                            originalCallback.call(this, value);
                        }
                        
                        if (value) {
                            console.log("[Arena AutoCache] Save .env now button clicked");
                            this.saveEnvNow();
                            // Reset button after action
                            setTimeout(() => {
                                saveEnvWidget.value = false;
                                this.setDirtyCanvas(true);
                            }, 100);
                        }
                    };
                }
                
                // Find sync_from_env widget
                const syncEnvWidget = this.widgets.find(w => w.name === "sync_from_env");
                if (syncEnvWidget) {
                    const originalCallback = syncEnvWidget.callback;
                    syncEnvWidget.callback = (value) => {
                        if (originalCallback) {
                            originalCallback.call(this, value);
                        }
                        
                        if (value) {
                            console.log("[Arena AutoCache] Sync from .env button clicked");
                            this.syncFromEnv();
                            // Reset button after action
                            setTimeout(() => {
                                syncEnvWidget.value = false;
                                this.setDirtyCanvas(true);
                            }, 100);
                        }
                    };
                }
                
                // Find live_env_sync widget
                const liveSyncWidget = this.widgets.find(w => w.name === "live_env_sync");
                if (liveSyncWidget) {
                    const originalCallback = liveSyncWidget.callback;
                    liveSyncWidget.callback = (value) => {
                        if (originalCallback) {
                            originalCallback.call(this, value);
                        }
                        
                        if (value) {
                            console.log("[Arena AutoCache] Live .env sync enabled");
                            this.startLiveSync();
                        } else {
                            console.log("[Arena AutoCache] Live .env sync disabled");
                            this.stopLiveSync();
                        }
                    };
                }
            };
            
            // Add method to save .env file immediately
            nodeType.prototype.saveEnvNow = async function() {
                try {
                    console.log("[Arena AutoCache] Saving .env file immediately...");
                    
                    // Collect current widget values
                    const envData = this.collectEnvData();
                    console.log("[Arena AutoCache] Collected env data:", envData);
                    
                    // Try API endpoint first
                    try {
                        const response = await fetch('/arena/env', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ env: envData })
                        });
                        
                        if (response.ok) {
                            const result = await response.json();
                            if (result.status === 'success') {
                                console.log("[Arena AutoCache] .env file saved via API:", result.message);
                                this.showNotification("[OK] .env file saved successfully!");
                                
                                // RU: Запускаем autopatch после сохранения .env
                                this.startAutopatch();
                                return;
                            }
                        }
                    } catch (apiError) {
                        console.warn("[Arena AutoCache] API not available, trying direct method:", apiError);
                    }
                    
                    // Fallback: direct file creation via ComfyUI's file system
                    console.log("[Arena AutoCache] Using direct file creation method...");
                    this.createEnvFileDirectly(envData);
                    
                } catch (error) {
                    console.error("[Arena AutoCache] Error saving .env:", error);
                    this.showNotification("[ERROR] Error saving .env file: " + error.message);
                }
            };
            
            // Add method to create .env file directly
            nodeType.prototype.createEnvFileDirectly = function(envData) {
                try {
                    // Create .env file content
                    let envContent = "# Arena AutoCache Environment Settings\n";
                    envContent += "# Generated automatically - do not edit manually\n\n";
                    
                    Object.entries(envData).forEach(([key, value]) => {
                        envContent += `${key}=${value}\n`;
                    });
                    
                    console.log("[Arena AutoCache] Creating .env file with content:", envContent);
                    
                    // Try to save via ComfyUI's file system
                    if (window.app && window.app.api) {
                        // Use ComfyUI's API to save file
                        const fileName = "arena_autocache.env";
                        const filePath = `user/${fileName}`;
                        
                        // Create a blob and save it
                        const blob = new Blob([envContent], { type: 'text/plain' });
                        const url = URL.createObjectURL(blob);
                        
                        // Trigger download
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = fileName;
                        a.style.display = 'none';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                        
                        console.log("[Arena AutoCache] .env file created and downloaded");
                        this.showNotification("[OK] .env file created and downloaded!");
                    } else {
                        // Fallback: show content in console
                        console.log("[Arena AutoCache] .env file content:");
                        console.log(envContent);
                        this.showNotification("[OK] .env content shown in console - copy to file manually");
                    }
                    
                } catch (error) {
                    console.error("[Arena AutoCache] Error creating .env file:", error);
                    this.showNotification("[ERROR] Error creating .env file: " + error.message);
                }
            };
            
            // Add method to sync from .env file
            nodeType.prototype.syncFromEnv = async function() {
                try {
                    console.log("[Arena AutoCache] Syncing from .env file...");
                    
                    const response = await fetch('/arena/env');
                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        console.log("[Arena AutoCache] .env data loaded:", result.env);
                        this.applyEnvData(result.env);
                        this.showNotification("[OK] Settings loaded from .env file!");
                    } else {
                        console.error("[Arena AutoCache] Failed to load .env:", result.message);
                        this.showNotification("[ERROR] Failed to load .env file: " + result.message);
                    }
                } catch (error) {
                    console.error("[Arena AutoCache] Error loading .env:", error);
                    this.showNotification("[ERROR] Error loading .env file: " + error.message);
                }
            };
            
            // Add method to collect current widget values
            nodeType.prototype.collectEnvData = function() {
                const envData = {};
                
                // Map widget names to env keys
                const widgetToEnvMap = {
                    'cache_root': 'ARENA_CACHE_ROOT',
                    'min_size_mb': 'ARENA_CACHE_MIN_SIZE_MB',
                    'max_cache_gb': 'ARENA_CACHE_MAX_GB',
                    'verbose': 'ARENA_CACHE_VERBOSE',
                    'cache_mode': 'ARENA_CACHE_MODE',
                    'auto_cache_enabled': 'ARENA_AUTO_CACHE_ENABLED',
                    'persist_env': 'ARENA_AUTOCACHE_AUTOPATCH'
                };
                
                this.widgets.forEach(widget => {
                    if (widgetToEnvMap[widget.name]) {
                        const envKey = widgetToEnvMap[widget.name];
                        let value = widget.value;
                        
                        // Convert boolean to string
                        if (typeof value === 'boolean') {
                            value = value ? '1' : '0';
                        }
                        
                        envData[envKey] = String(value);
                    }
                });
                
                return envData;
            };
            
            // Add method to apply .env data to widgets
            nodeType.prototype.applyEnvData = function(envData) {
                const envToWidgetMap = {
                    'ARENA_CACHE_ROOT': 'cache_root',
                    'ARENA_CACHE_MIN_SIZE_MB': 'min_size_mb',
                    'ARENA_CACHE_MAX_GB': 'max_cache_gb',
                    'ARENA_CACHE_VERBOSE': 'verbose',
                    'ARENA_CACHE_MODE': 'cache_mode',
                    'ARENA_AUTO_CACHE_ENABLED': 'auto_cache_enabled',
                    'ARENA_AUTOCACHE_AUTOPATCH': 'persist_env'
                };
                
                Object.entries(envData).forEach(([envKey, value]) => {
                    const widgetName = envToWidgetMap[envKey];
                    if (widgetName) {
                        const widget = this.widgets.find(w => w.name === widgetName);
                        if (widget) {
                            // Convert string back to appropriate type
                            let convertedValue = value;
                            if (widget.type === 'BOOLEAN') {
                                convertedValue = value === '1' || value === 'true';
                            } else if (widget.type === 'FLOAT') {
                                convertedValue = parseFloat(value);
                            }
                            
                            widget.value = convertedValue;
                            console.log(`[Arena AutoCache] Updated ${widgetName} to ${convertedValue}`);
                        }
                    }
                });
                
                // Force node redraw
                this.setDirtyCanvas(true);
            };
            
            // Add method to show notifications
            nodeType.prototype.showNotification = function(message) {
                // Simple notification - you can enhance this with a proper UI
                console.log(`[Arena AutoCache Notification] ${message}`);
                
                // Try to show in ComfyUI's notification system if available
                if (window.app && window.app.showNotification) {
                    window.app.showNotification(message);
                }
            };
            
            // Add method to start live sync
            nodeType.prototype.startLiveSync = function() {
                if (this.liveSyncInterval) {
                    clearInterval(this.liveSyncInterval);
                }
                
                this.liveSyncInterval = setInterval(async () => {
                    try {
                        const response = await fetch('/arena/env');
                        const result = await response.json();
                        
                        if (result.status === 'success' && result.env) {
                            // Check if any values changed
                            const currentData = this.collectEnvData();
                            const hasChanges = Object.keys(result.env).some(key => 
                                currentData[key] !== result.env[key]
                            );
                            
                            if (hasChanges) {
                                console.log("[Arena AutoCache] Live sync: .env file changed, updating UI");
                                this.applyEnvData(result.env);
                            }
                        }
                    } catch (error) {
                        console.error("[Arena AutoCache] Live sync error:", error);
                    }
                }, 1000); // Check every second
                
                console.log("[Arena AutoCache] Live sync started");
            };
            
            // Add method to stop live sync
            nodeType.prototype.stopLiveSync = function() {
                if (this.liveSyncInterval) {
                    clearInterval(this.liveSyncInterval);
                    this.liveSyncInterval = null;
                    console.log("[Arena AutoCache] Live sync stopped");
                }
            };
            
            // Add method to start autopatch
            nodeType.prototype.startAutopatch = async function() {
                try {
                    console.log("[Arena AutoCache] Starting autopatch...");
                    
                    // RU: Запускаем autopatch через API
                    const response = await fetch('/arena/autopatch', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ action: 'start' })
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        if (result.status === 'success') {
                            console.log("[Arena AutoCache] Autopatch started successfully");
                            this.showNotification("[OK] Autopatch started - caching enabled!");
                        } else {
                            console.error("[Arena AutoCache] Failed to start autopatch:", result.message);
                            this.showNotification("[ERROR] Failed to start autopatch: " + result.message);
                        }
                    } else {
                        console.error("[Arena AutoCache] Autopatch API not available");
                        this.showNotification("[ERROR] Autopatch API not available");
                    }
                } catch (error) {
                    console.error("[Arena AutoCache] Error starting autopatch:", error);
                    this.showNotification("[ERROR] Error starting autopatch: " + error.message);
                }
            };
            
            // Override onConfigure to ensure visibility is updated after configuration
            const originalOnConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function(info) {
                const result = originalOnConfigure?.apply(this, arguments);
                
                // Update visibility after configuration
                setTimeout(() => {
                    this.updateWidgetVisibility();
                }, 100);
                
                return result;
            };
        }
    }
});

// Legacy integration (kept for compatibility)
if (typeof app !== 'undefined' && app.graph) {
    // Integrate with ComfyUI's graph system
    const originalQueuePrompt = app.queuePrompt;
    
    app.queuePrompt = function(prompt, ...args) {
        // Intercept workflow execution for autocache
        if (window.arenaAutoCache && window.arenaAutoCache.isEnabled) {
            console.log("[Arena AutoCache] Intercepting workflow execution");
            this.processWorkflowForCache(prompt);
        }
        return originalQueuePrompt.call(this, prompt, ...args);
    };

    app.processWorkflowForCache = function(prompt) {
        // Process workflow nodes for model caching
        const nodes = prompt.workflow || {};
        for (const [nodeId, node] of Object.entries(nodes)) {
            if (node.class_type && this.isModelNode(node.class_type)) {
                this.cacheModelFromNode(node);
            }
        }
    };

    app.isModelNode = function(classType) {
        // Check if node type uses models
        const modelNodeTypes = [
            'CheckpointLoaderSimple',
            'VAELoader', 
            'LoraLoader',
            'CLIPLoader',
            'UNETLoader'
        ];
        return modelNodeTypes.includes(classType);
    };

    app.cacheModelFromNode = function(node) {
        // Extract model path and cache it
        if (node.inputs && node.inputs.ckpt_name) {
            const modelPath = this.getModelPath(node.inputs.ckpt_name);
            if (modelPath && window.arenaAutoCache) {
                window.arenaAutoCache.cacheModel(node.inputs.ckpt_name, modelPath);
            }
        }
    };

    app.getModelPath = function(modelName) {
        // Get full path to model file
        const modelDir = this.getModelDirectory();
        return `${modelDir}/${modelName}`;
    };

    app.getModelDirectory = function() {
        // Get ComfyUI models directory
        return '/models/checkpoints'; // Default path
    };

    console.log("[Arena AutoCache Extension v3] ComfyUI integration ready");
} else {
    console.warn("[Arena AutoCache Extension v3] ComfyUI not detected");
}
}

// Start waiting for app
waitForApp();