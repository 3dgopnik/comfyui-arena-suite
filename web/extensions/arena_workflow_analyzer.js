// Arena Workflow Analyzer Extension v1.0
// Analyzes ComfyUI workflow to extract model information for smart caching
// Location: web/extensions/arena_workflow_analyzer.js

console.log("[Arena Workflow Analyzer] Loading...");

// Wait for app to be available
let extensionRegistered = false;
function waitForApp() {
    if (typeof app !== 'undefined' && app.registerExtension && !extensionRegistered) {
        console.log("[Arena Workflow Analyzer] App is ready, registering extension...");
        registerWorkflowAnalyzer();
        extensionRegistered = true;
    } else if (!extensionRegistered) {
        console.log("[Arena Workflow Analyzer] App not ready, waiting...");
        setTimeout(waitForApp, 100);
    }
}

function registerWorkflowAnalyzer() {
// Register extension for workflow analysis
app.registerExtension({
    name: "Arena.WorkflowAnalyzer",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // Target only Arena AutoCache nodes
        if (nodeType.comfyClass === "ArenaAutoCacheSimple") {
            console.log("[Arena Workflow Analyzer] Registering workflow analysis for ArenaAutoCacheSimple");
            
            // Add workflow analysis methods to Arena AutoCache nodes
            nodeType.prototype.setupWorkflowAnalysis = function() {
                console.log("[Arena Workflow Analyzer] Setting up workflow analysis");
                
                // Store reference to this node
                this.workflowAnalyzer = this;
                
                // Initialize analysis state
                this.workflowAnalysis = {
                    enabled: false,
                    lastAnalysis: null,
                    models: new Set(),
                    analysisCount: 0
                };
                
                // Set up analysis trigger
                this.setupAnalysisTrigger();
            };
            
            // Set up analysis trigger when node is created
            const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                const result = originalOnNodeCreated?.apply(this, arguments);
                this.setupWorkflowAnalysis();
                return result;
            };
            
            // Set up analysis trigger
            nodeType.prototype.setupAnalysisTrigger = function() {
                // Listen for workflow changes
                if (app.graph) {
                    const originalGraphChanged = app.graph.onGraphChanged;
                    app.graph.onGraphChanged = () => {
                        originalGraphChanged?.apply(this, arguments);
                        this.triggerWorkflowAnalysis();
                    };
                }
                
                // Listen for prompt execution
                const originalQueuePrompt = app.queuePrompt;
                app.queuePrompt = (prompt, ...args) => {
                    this.analyzeWorkflowBeforeExecution(prompt);
                    return originalQueuePrompt.call(app, prompt, ...args);
                };
                
                console.log("[Arena Workflow Analyzer] Analysis triggers set up");
            };
            
            // Trigger workflow analysis
            nodeType.prototype.triggerWorkflowAnalysis = function() {
                if (!this.workflowAnalysis.enabled) {
                    return;
                }
                
                console.log("[Arena Workflow Analyzer] Triggering workflow analysis");
                
                try {
                    const workflow = this.getCurrentWorkflow();
                    if (workflow) {
                        this.analyzeWorkflow(workflow);
                    }
                } catch (error) {
                    console.error("[Arena Workflow Analyzer] Analysis error:", error);
                }
            };
            
            // Get current workflow from ComfyUI
            nodeType.prototype.getCurrentWorkflow = function() {
                try {
                    // Use ComfyUI's graphToPrompt method to get current workflow
                    const prompt = app.graphToPrompt();
                    if (prompt && prompt.workflow) {
                        return prompt.workflow;
                    }
                } catch (error) {
                    console.error("[Arena Workflow Analyzer] Failed to get workflow:", error);
                }
                return null;
            };
            
            // Analyze workflow for models
            nodeType.prototype.analyzeWorkflow = function(workflow) {
                console.log("[Arena Workflow Analyzer] Analyzing workflow...");
                
                const models = new Set();
                const nodes = workflow.nodes || [];
                
                // Analyze each node
                nodes.forEach(node => {
                    const nodeModels = this.extractModelsFromNode(node);
                    nodeModels.forEach(model => models.add(model));
                });
                
                // Update analysis state
                this.workflowAnalysis.models = models;
                this.workflowAnalysis.lastAnalysis = {
                    timestamp: Date.now(),
                    nodeCount: nodes.length,
                    modelCount: models.size,
                    models: Array.from(models)
                };
                
                this.workflowAnalysis.analysisCount++;
                
                console.log(`[Arena Workflow Analyzer] Found ${models.size} models:`, Array.from(models));
                
                // Send models to Python node for caching
                this.sendModelsToPython(Array.from(models));
            };
            
            // Extract models from a single node
            nodeType.prototype.extractModelsFromNode = function(node) {
                const models = new Set();
                
                if (!node || !node.class_type) {
                    return models;
                }
                
                const classType = node.class_type;
                const inputs = node.inputs || {};
                
                // RU: Расширенный список полей для поиска моделей
                const modelFields = [
                    // RU: Основные модели
                    'ckpt_name', 'model_name', 'checkpoint_name',
                    // RU: LoRA модели
                    'lora_name', 'lora_model', 'lora_file',
                    // RU: VAE модели
                    'vae_name', 'vae_model', 'vae_file',
                    // RU: CLIP модели
                    'clip_name', 'clip_model', 'clip_file',
                    // RU: ControlNet модели
                    'control_net_name', 'controlnet_name', 'control_net_model',
                    // RU: Upscale модели
                    'upscale_model_name', 'upscale_model', 'upscale_file',
                    // RU: Embeddings
                    'embeddings', 'embedding_name', 'embedding_file',
                    // RU: Hypernetworks
                    'hypernetwork_name', 'hypernetwork_model', 'hypernetwork_file',
                    // RU: IPAdapter модели
                    'ipadapter_name', 'ipadapter_model', 'ipadapter_file',
                    // RU: GLIGEN модели
                    'gligen_name', 'gligen_model', 'gligen_file',
                    // RU: AnimateDiff модели
                    'motion_model', 'motion_file', 'temporal_model',
                    // RU: T2I Adapter модели
                    't2i_adapter_name', 't2i_adapter_model', 't2i_adapter_file',
                    // RU: GGUF модели
                    'gguf_model', 'gguf_file', 'gguf_name',
                    // RU: UNet модели
                    'unet_model', 'unet_file', 'unet_name',
                    // RU: Diffusion модели
                    'diffusion_model', 'diffusion_file', 'diffusion_name'
                ];
                
                modelFields.forEach(field => {
                    if (inputs[field]) {
                        const modelName = inputs[field];
                        if (typeof modelName === 'string' && modelName.trim()) {
                            models.add({
                                name: modelName,
                                type: this.getModelType(field, classType),
                                field: field,
                                nodeId: node.id,
                                classType: classType
                            });
                        }
                    }
                });
                
                return models;
            };
            
            // Get model type from field name and class type
            nodeType.prototype.getModelType = function(field, classType) {
                // RU: Расширенный маппинг полей на типы моделей
                const typeMap = {
                    // RU: Основные модели
                    'ckpt_name': 'checkpoint',
                    'model_name': 'checkpoint',
                    'checkpoint_name': 'checkpoint',
                    // RU: LoRA модели
                    'lora_name': 'lora',
                    'lora_model': 'lora',
                    'lora_file': 'lora',
                    // RU: VAE модели
                    'vae_name': 'vae',
                    'vae_model': 'vae',
                    'vae_file': 'vae',
                    // RU: CLIP модели
                    'clip_name': 'clip',
                    'clip_model': 'clip',
                    'clip_file': 'clip',
                    // RU: ControlNet модели
                    'control_net_name': 'controlnet',
                    'controlnet_name': 'controlnet',
                    'control_net_model': 'controlnet',
                    // RU: Upscale модели
                    'upscale_model_name': 'upscale',
                    'upscale_model': 'upscale',
                    'upscale_file': 'upscale',
                    // RU: Embeddings
                    'embeddings': 'embedding',
                    'embedding_name': 'embedding',
                    'embedding_file': 'embedding',
                    // RU: Hypernetworks
                    'hypernetwork_name': 'hypernetwork',
                    'hypernetwork_model': 'hypernetwork',
                    'hypernetwork_file': 'hypernetwork',
                    // RU: IPAdapter модели
                    'ipadapter_name': 'ipadapter',
                    'ipadapter_model': 'ipadapter',
                    'ipadapter_file': 'ipadapter',
                    // RU: GLIGEN модели
                    'gligen_name': 'gligen',
                    'gligen_model': 'gligen',
                    'gligen_file': 'gligen',
                    // RU: AnimateDiff модели
                    'motion_model': 'animatediff',
                    'motion_file': 'animatediff',
                    'temporal_model': 'animatediff',
                    // RU: T2I Adapter модели
                    't2i_adapter_name': 't2i_adapter',
                    't2i_adapter_model': 't2i_adapter',
                    't2i_adapter_file': 't2i_adapter',
                    // RU: GGUF модели
                    'gguf_model': 'gguf',
                    'gguf_file': 'gguf',
                    'gguf_name': 'gguf',
                    // RU: UNet модели
                    'unet_model': 'unet',
                    'unet_file': 'unet',
                    'unet_name': 'unet',
                    // RU: Diffusion модели
                    'diffusion_model': 'diffusion',
                    'diffusion_file': 'diffusion',
                    'diffusion_name': 'diffusion'
                };
                
                // RU: Сначала проверяем маппинг полей
                if (typeMap[field]) {
                    return typeMap[field];
                }
                
                // RU: Если поле не найдено, определяем по типу ноды
                const classTypeMap = {
                    'CheckpointLoaderSimple': 'checkpoint',
                    'CheckpointLoader': 'checkpoint',
                    'LoadDiffusionModel': 'diffusion',
                    'LoraLoader': 'lora',
                    'LoraLoaderAdvanced': 'lora',
                    'VAELoader': 'vae',
                    'VAEDecode': 'vae',
                    'VAEEncode': 'vae',
                    'CLIPLoader': 'clip',
                    'CLIPLoaderGGUF': 'gguf',
                    'ControlNetLoader': 'controlnet',
                    'ControlNetApply': 'controlnet',
                    'UpscaleModelLoader': 'upscale',
                    'ImageUpscaleWithModel': 'upscale',
                    'LoadEmbedding': 'embedding',
                    'HypernetworkLoader': 'hypernetwork',
                    'IPAdapterLoader': 'ipadapter',
                    'IPAdapterApply': 'ipadapter',
                    'UNETLoader': 'unet',
                    'GLIGENLoader': 'gligen',
                    'AnimateDiffLoader': 'animatediff',
                    'T2IAdapterLoader': 't2i_adapter'
                };
                
                return classTypeMap[classType] || 'unknown';
            };
            
            // Analyze workflow before execution
            nodeType.prototype.analyzeWorkflowBeforeExecution = function(prompt) {
                if (!this.workflowAnalysis.enabled) {
                    return;
                }
                
                console.log("[Arena Workflow Analyzer] Analyzing workflow before execution");
                
                try {
                    // Extract models from prompt
                    const models = this.extractModelsFromPrompt(prompt);
                    if (models.length > 0) {
                        console.log(`[Arena Workflow Analyzer] Found ${models.length} models in prompt:`, models);
                        this.sendModelsToPython(models);
                    }
                } catch (error) {
                    console.error("[Arena Workflow Analyzer] Prompt analysis error:", error);
                }
            };
            
            // Extract models from prompt
            nodeType.prototype.extractModelsFromPrompt = function(prompt) {
                const models = [];
                
                if (!prompt || !prompt.workflow) {
                    return models;
                }
                
                const workflow = prompt.workflow;
                
                // Analyze each node in the prompt
                Object.entries(workflow).forEach(([nodeId, node]) => {
                    if (node && node.inputs) {
                        const nodeModels = this.extractModelsFromNode({...node, id: nodeId});
                        models.push(...nodeModels);
                    }
                });
                
                return models;
            };
            
            // Send models to Python node for caching
            nodeType.prototype.sendModelsToPython = function(models) {
                if (!models || models.length === 0) {
                    return;
                }
                
                console.log("[Arena Workflow Analyzer] Sending models to Python node:", models);
                
                // Send models via custom API endpoint
                this.sendModelsToServer(models);
            };
            
            // Send models to server
            nodeType.prototype.sendModelsToServer = function(models) {
                try {
                    const payload = {
                        models: models,
                        timestamp: Date.now(),
                        nodeId: this.id
                    };
                    
                    // Send to custom endpoint
                    fetch('/arena/analyze_workflow', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(payload)
                    }).then(response => {
                        if (response.ok) {
                            console.log("[Arena Workflow Analyzer] Models sent successfully");
                        } else {
                            console.error("[Arena Workflow Analyzer] Failed to send models:", response.status);
                        }
                    }).catch(error => {
                        console.error("[Arena Workflow Analyzer] Network error:", error);
                    });
                } catch (error) {
                    console.error("[Arena Workflow Analyzer] Send error:", error);
                }
            };
            
            // Enable/disable workflow analysis
            nodeType.prototype.setWorkflowAnalysisEnabled = function(enabled) {
                this.workflowAnalysis.enabled = enabled;
                console.log(`[Arena Workflow Analyzer] Analysis ${enabled ? 'enabled' : 'disabled'}`);
                
                if (enabled) {
                    this.triggerWorkflowAnalysis();
                }
            };
            
            // Get analysis results
            nodeType.prototype.getAnalysisResults = function() {
                return this.workflowAnalysis.lastAnalysis;
            };
        }
    }
});

// Global workflow analysis functions
window.ArenaWorkflowAnalyzer = {
    // Analyze current workflow
    analyzeCurrentWorkflow: function() {
        try {
            const prompt = app.graphToPrompt();
            if (prompt && prompt.workflow) {
                console.log("[Arena Workflow Analyzer] Current workflow:", prompt.workflow);
                return prompt.workflow;
            }
        } catch (error) {
            console.error("[Arena Workflow Analyzer] Failed to analyze current workflow:", error);
        }
        return null;
    },
    
    // Get all models in current workflow
    getCurrentWorkflowModels: function() {
        try {
            const workflow = this.analyzeCurrentWorkflow();
            if (!workflow) {
                return [];
            }
            
            const models = [];
            const nodes = workflow.nodes || [];
            
            nodes.forEach(node => {
                if (node && node.inputs) {
                    const nodeModels = this.extractModelsFromNode(node);
                    models.push(...nodeModels);
                }
            });
            
            return models;
        } catch (error) {
            console.error("[Arena Workflow Analyzer] Failed to get models:", error);
            return [];
        }
    },
    
    // Extract models from node
    extractModelsFromNode: function(node) {
        const models = [];
        
        if (!node || !node.inputs) {
            return models;
        }
        
        const inputs = node.inputs;
        const modelFields = [
            'ckpt_name', 'vae_name', 'lora_name', 'clip_name',
            'model_name', 'control_net_name', 'upscale_model_name',
            'embeddings', 'hypernetwork_name'
        ];
        
        modelFields.forEach(field => {
            if (inputs[field]) {
                const modelName = inputs[field];
                if (typeof modelName === 'string' && modelName.trim()) {
                    models.push({
                        name: modelName,
                        type: this.getModelType(field),
                        field: field,
                        nodeId: node.id,
                        classType: node.class_type
                    });
                }
            }
        });
        
        return models;
    },
    
    // Get model type from field
    getModelType: function(field) {
        const typeMap = {
            'ckpt_name': 'checkpoint',
            'vae_name': 'vae',
            'lora_name': 'lora',
            'clip_name': 'clip',
            'model_name': 'model',
            'control_net_name': 'controlnet',
            'upscale_model_name': 'upscale',
            'embeddings': 'embedding',
            'hypernetwork_name': 'hypernetwork'
        };
        return typeMap[field] || 'unknown';
    }
};

console.log("[Arena Workflow Analyzer] Extension loaded successfully");
}

// Start waiting for app
waitForApp();
