// Arena AutoCache Extension v4 - Conditional UI Management
// Provides dynamic widget visibility control for Arena AutoCache nodes

console.log("[Arena AutoCache Extension v4] Loading...");

// Wait for app to be available
let extensionRegistered = false;
function waitForApp() {
    if (typeof app !== 'undefined' && app.registerExtension && !extensionRegistered) {
        console.log("[Arena AutoCache Extension v4] App is ready, registering extension...");
        registerArenaAutoCache();
        extensionRegistered = true;
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