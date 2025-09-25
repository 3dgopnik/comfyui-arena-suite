// Arena AutoCache Extension v3 - ComfyUI Integration
// Provides ComfyUI-specific integration for Arena AutoCache

console.log("[Arena AutoCache Extension v3] Loading...");

// ComfyUI extension integration
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