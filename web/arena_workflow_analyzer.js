// Arena Workflow Analyzer Extension v1.2
// Analyzes ComfyUI workflow to extract model information for smart caching
// Location: web/extensions/arena_workflow_analyzer.js

console.log("[Arena Workflow Analyzer] Loading...");

// Wait for app to be available
let extensionRegistered = false;
function waitForApp() {
    if (typeof app !== 'undefined' && app.registerExtension && !extensionRegistered) {
        // Check if extension is already registered
        if (window.arenaWorkflowAnalyzerExtensionRegistered) {
            console.log("[Arena Workflow Analyzer] Extension already registered, skipping...");
            return;
        }
        
        console.log("[Arena Workflow Analyzer] App is ready, registering extension...");
        registerWorkflowAnalyzer();
        extensionRegistered = true;
        window.arenaWorkflowAnalyzerExtensionRegistered = true;
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
            nodeType.prototype.triggerWorkflowAnalysis = async function() {
                if (!this.workflowAnalysis.enabled) {
                    return;
                }
                
                console.log("[Arena Workflow Analyzer] Triggering workflow analysis");
                
                try {
                    const workflow = await this.getCurrentWorkflow();
                    if (workflow) {
                        this.analyzeWorkflow(workflow);
                    }
                } catch (error) {
                    console.error("[Arena Workflow Analyzer] Analysis error:", error);
                }
            };
            
    // Get current workflow from ComfyUI
    nodeType.prototype.getCurrentWorkflow = async function() {
        try {
            // Use ComfyUI's graphToPrompt method to get current workflow (async)
            const prompt = await app.graphToPrompt();
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
                // RU: Специальная логика для различных загрузчиков моделей
                const specialClassTypes = {
                    // RU: Text encoders
                    'DualCLIPLoader': 'text_encoders',
                    'FluxClipModel': 'text_encoders',
                    'QuadrupleCLIPLoader': 'text_encoders',
                    'T5TextEncoder': 'text_encoders',
                    'CLIPTextEncoder': 'text_encoders',
                    
                    // RU: CLIP Vision
                    'CLIPVisionLoader': 'clip_vision',
                    'CLIPVisionLoaderModelOnly': 'clip_vision',
                    
                    // RU: Embeddings
                    'EmbeddingLoader': 'embeddings',
                    'EmbeddingLoaderModelOnly': 'embeddings',
                    
                    // RU: Hypernetworks
                    'HypernetworkLoader': 'hypernetworks',
                    'HypernetworkLoaderModelOnly': 'hypernetworks',
                    
                    // RU: IPAdapter
                    'IPAdapterLoader': 'ipadapter',
                    'IPAdapterLoaderModelOnly': 'ipadapter',
                    
                    // RU: GLIGEN
                    'GLIGENLoader': 'gligen',
                    'GLIGENLoaderModelOnly': 'gligen',
                    
                    // RU: AnimateDiff
                    'AnimateDiffLoader': 'animatediff_models',
                    'AnimateDiffLoaderModelOnly': 'animatediff_models',
                    
                    // RU: T2I Adapter
                    'T2IAdapterLoader': 't2i_adapter',
                    'T2IAdapterLoaderModelOnly': 't2i_adapter',
                    
                    // RU: GGUF
                    'GGUFLoader': 'gguf_models',
                    'UNetLoaderGGUF': 'gguf_models',
                    'CLIPLoaderGGUF': 'gguf_models',
                    
                    // RU: UNet
                    'UNetLoader': 'unet_models',
                    'UNetLoaderModelOnly': 'unet_models',
                    
                    // RU: Diffusion
                    'DiffusionLoader': 'diffusion_models',
                    'DiffusionLoaderModelOnly': 'diffusion_models',
                    
                    // RU: Upscale
                    'UpscaleLoader': 'upscale_models',
                    'UpscaleLoaderModelOnly': 'upscale_models',
                    
                    // RU: ControlNet
                    'ControlNetLoader': 'controlnet',
                    'ControlNetLoaderModelOnly': 'controlnet',
                    
                    // RU: VAE
                    'VAELoader': 'vae',
                    'VAELoaderModelOnly': 'vae',
                    
                    // RU: LoRA
                    'LoraLoader': 'loras',
                    'LoraLoaderModelOnly': 'loras',
                    
                    // RU: Checkpoints
                    'CheckpointLoader': 'checkpoints',
                    'CheckpointLoaderSimple': 'checkpoints',
                    'CheckpointLoaderModelOnly': 'checkpoints',
                    
                    // RU: CLIP
                    'CLIPLoader': 'clip',
                    'CLIPLoaderModelOnly': 'clip'
                };
                
                // RU: Проверяем специальные типы классов
                if (specialClassTypes[classType]) {
                    return specialClassTypes[classType];
                }
                
                // RU: Расширенный маппинг полей на типы моделей
                const typeMap = {
                    // RU: Основные модели
                    'ckpt_name': 'checkpoints',
                    'model_name': 'checkpoints',
                    'checkpoint_name': 'checkpoints',
                    // RU: LoRA модели
                    'lora_name': 'loras',
                    'lora_model': 'loras',
                    'lora_file': 'loras',
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
                    'upscale_model_name': 'upscale_models',
                    'upscale_model': 'upscale_models',
                    'upscale_file': 'upscale_models',
                    // RU: Embeddings
                    'embeddings': 'embeddings',
                    'embedding_name': 'embeddings',
                    'embedding_file': 'embeddings',
                    // RU: Hypernetworks
                    'hypernetwork_name': 'hypernetworks',
                    'hypernetwork_model': 'hypernetworks',
                    'hypernetwork_file': 'hypernetworks',
                    // RU: IPAdapter модели
                    'ipadapter_name': 'ipadapter',
                    'ipadapter_model': 'ipadapter',
                    'ipadapter_file': 'ipadapter',
                    // RU: GLIGEN модели
                    'gligen_name': 'gligen',
                    'gligen_model': 'gligen',
                    'gligen_file': 'gligen',
                    // RU: AnimateDiff модели
                    'motion_model': 'animatediff_models',
                    'motion_file': 'animatediff_models',
                    'temporal_model': 'animatediff_models',
                    // RU: T2I Adapter модели
                    't2i_adapter_name': 't2i_adapter',
                    't2i_adapter_model': 't2i_adapter',
                    't2i_adapter_file': 't2i_adapter',
                    // RU: GGUF модели
                    'gguf_model': 'gguf_models',
                    'gguf_file': 'gguf_models',
                    'gguf_name': 'gguf_models',
                    // RU: UNet модели
                    'unet_model': 'unet_models',
                    'unet_file': 'unet_models',
                    'unet_name': 'unet_models',
                    // RU: Diffusion модели
                    'diffusion_model': 'diffusion_models',
                    'diffusion_file': 'diffusion_models',
                    'diffusion_name': 'diffusion_models',
                    // RU: CLIP Vision модели
                    'clip_vision_name': 'clip_vision',
                    'clip_vision_model': 'clip_vision',
                    'clip_vision_file': 'clip_vision',
                    // RU: Text encoders
                    'text_encoder_name': 'text_encoders',
                    'text_encoder_model': 'text_encoders',
                    'text_encoder_file': 'text_encoders'
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
    analyzeCurrentWorkflow: async function() {
        try {
            const prompt = await app.graphToPrompt();
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
    getCurrentWorkflowModels: async function() {
        try {
            const workflow = await this.analyzeCurrentWorkflow();
            if (!workflow) {
                console.log("[Arena Workflow Analyzer] No workflow found");
                return [];
            }
            
            console.log("[Arena Workflow Analyzer] Workflow structure:", workflow);
            
            const models = [];
            
            // RU: ComfyUI может возвращать workflow.nodes (массив) или workflow[nodeId] (объект)
            if (Array.isArray(workflow.nodes)) {
                console.log("[Arena Workflow Analyzer] Processing workflow.nodes array:", workflow.nodes.length, "nodes");
                workflow.nodes.forEach(node => {
                    if (node && node.inputs) {
                        const nodeModels = this.extractModelsFromNode(node);
                        models.push(...nodeModels);
                    }
                });
            } else if (typeof workflow === 'object') {
                console.log("[Arena Workflow Analyzer] Processing workflow object with", Object.keys(workflow).length, "node IDs");
                // RU: Обрабатываем как объект nodeId -> node
                Object.entries(workflow).forEach(([nodeId, node]) => {
                    if (node && typeof node === 'object' && node.inputs) {
                        const nodeModels = this.extractModelsFromNode({...node, id: nodeId});
                        models.push(...nodeModels);
                    }
                });
            } else {
                console.warn("[Arena Workflow Analyzer] Unknown workflow format:", typeof workflow);
            }
            
            console.log(`[Arena Workflow Analyzer] Found ${models.length} models total`);
            return models;
        } catch (error) {
            console.error("[Arena Workflow Analyzer] Failed to get models:", error);
            return [];
        }
    },
    
    // Extract models from node - UNIVERSAL approach
    extractModelsFromNode: function(node) {
        const models = [];
        
        if (!node) {
            return models;
        }
        
        const nodeType = node.type || node.class_type;
        
        // RU: Универсальный подход - ищем файлы с расширениями моделей во всех widgets_values
        if (!node.widgets_values || !Array.isArray(node.widgets_values)) {
            return models;
        }
        
        // RU: Поддерживаемые расширения моделей
        const modelExtensions = ['.safetensors', '.ckpt', '.pth', '.bin', '.gguf', '.sft', '.pt'];
        
        // RU: Категории по типу ноды (эвристика)
        const categoryByNodeType = {
            'CheckpointLoaderSimple': 'checkpoints',
            'CheckpointLoader': 'checkpoints',
            'VAELoader': 'vae',
            'LoraLoader': 'loras',
            'LoraLoaderModelOnly': 'loras',
            'ControlNetLoader': 'controlnet',
            'UpscaleModelLoader': 'upscale_models',
            'UNETLoader': 'diffusion_models',
            'CLIPLoader': 'clip',
            'DualCLIPLoader': 'clip',
            'TripleCLIPLoader': 'clip',
            'SUPIR_model_loader_v2': 'upscale_models',
            'UnetLoaderGGUF': 'gguf_models'
        };
        
        // RU: Проверяем каждое значение в widgets_values
        node.widgets_values.forEach((value, index) => {
            if (typeof value === 'string' && value.trim()) {
                // RU: Проверяем расширение файла
                const hasModelExtension = modelExtensions.some(ext => value.toLowerCase().endsWith(ext));
                
                if (hasModelExtension) {
                    // RU: Определяем категорию по типу ноды или по имени файла
                    let category = categoryByNodeType[nodeType] || this.detectCategoryFromFilename(value);
                    
                    models.push({
                        name: value,
                        type: category,
                        field: `widget_${index}`,
                        nodeId: node.id,
                        classType: nodeType
                    });
                }
            }
        });
        
        // RU: Логируем для диагностики
        if (models.length > 0) {
            console.log(`[Arena Workflow Analyzer] Extracted ${models.length} model(s) from node ${node.id} (${nodeType}):`, models);
        }
        
        return models;
    },
    
    // Detect category from filename (fallback)
    detectCategoryFromFilename: function(filename) {
        const lower = filename.toLowerCase();
        
        // RU: Определяем категорию по ключевым словам в имени файла
        if (lower.includes('lora') || lower.includes('lycoris')) return 'loras';
        if (lower.includes('vae') || lower.includes('ae.sft')) return 'vae';
        if (lower.includes('controlnet') || lower.includes('control_net')) return 'controlnet';
        if (lower.includes('upscale') || lower.includes('esrgan') || lower.includes('supir')) return 'upscale_models';
        if (lower.includes('unet') || lower.includes('diffusion')) return 'diffusion_models';
        if (lower.includes('clip') && !lower.includes('clipvision')) return 'clip';
        if (lower.includes('clipvision') || lower.includes('clip_vision')) return 'clip_vision';
        if (lower.includes('embedding') || lower.includes('embed')) return 'embeddings';
        if (lower.includes('t5') || lower.includes('text_encoder')) return 'text_encoders';
        
        // RU: По умолчанию считаем checkpoint
        return 'checkpoints';
    },
    
    // Get model type from field
    getModelType: function(field, classType) {
        // RU: Специальная логика для различных загрузчиков моделей
        const specialClassTypes = {
            // RU: Text encoders
            'DualCLIPLoader': 'text_encoders',
            'FluxClipModel': 'text_encoders',
            'QuadrupleCLIPLoader': 'text_encoders',
            'T5TextEncoder': 'text_encoders',
            'CLIPTextEncoder': 'text_encoders',
            
            // RU: CLIP Vision
            'CLIPVisionLoader': 'clip_vision',
            'CLIPVisionLoaderModelOnly': 'clip_vision',
            
            // RU: Embeddings
            'EmbeddingLoader': 'embeddings',
            'EmbeddingLoaderModelOnly': 'embeddings',
            
            // RU: Hypernetworks
            'HypernetworkLoader': 'hypernetworks',
            'HypernetworkLoaderModelOnly': 'hypernetworks',
            
            // RU: IPAdapter
            'IPAdapterLoader': 'ipadapter',
            'IPAdapterLoaderModelOnly': 'ipadapter',
            
            // RU: GLIGEN
            'GLIGENLoader': 'gligen',
            'GLIGENLoaderModelOnly': 'gligen',
            
            // RU: AnimateDiff
            'AnimateDiffLoader': 'animatediff_models',
            'AnimateDiffLoaderModelOnly': 'animatediff_models',
            
            // RU: T2I Adapter
            'T2IAdapterLoader': 't2i_adapter',
            'T2IAdapterLoaderModelOnly': 't2i_adapter',
            
            // RU: GGUF
            'GGUFLoader': 'gguf_models',
            'UNetLoaderGGUF': 'gguf_models',
            'CLIPLoaderGGUF': 'gguf_models',
            
            // RU: UNet
            'UNetLoader': 'unet_models',
            'UNetLoaderModelOnly': 'unet_models',
            
            // RU: Diffusion
            'DiffusionLoader': 'diffusion_models',
            'DiffusionLoaderModelOnly': 'diffusion_models',
            
            // RU: Upscale
            'UpscaleLoader': 'upscale_models',
            'UpscaleLoaderModelOnly': 'upscale_models',
            
            // RU: ControlNet
            'ControlNetLoader': 'controlnet',
            'ControlNetLoaderModelOnly': 'controlnet',
            
            // RU: VAE
            'VAELoader': 'vae',
            'VAELoaderModelOnly': 'vae',
            
            // RU: LoRA
            'LoraLoader': 'loras',
            'LoraLoaderModelOnly': 'loras',
            
            // RU: Checkpoints
            'CheckpointLoader': 'checkpoints',
            'CheckpointLoaderSimple': 'checkpoints',
            'CheckpointLoaderModelOnly': 'checkpoints',
            
            // RU: CLIP
            'CLIPLoader': 'clip',
            'CLIPLoaderModelOnly': 'clip'
        };
        
        // RU: Проверяем специальные типы классов
        if (specialClassTypes[classType]) {
            return specialClassTypes[classType];
        }
        
        const typeMap = {
            'ckpt_name': 'checkpoints',
            'vae_name': 'vae',
            'lora_name': 'loras',
            'clip_name': 'clip',
            'model_name': 'checkpoints',
            'control_net_name': 'controlnet',
            'upscale_model_name': 'upscale_models',
            'embeddings': 'embeddings',
            'hypernetwork_name': 'hypernetworks',
            'clip_vision_name': 'clip_vision',
            'text_encoder_name': 'text_encoders'
        };
        return typeMap[field] || 'unknown';
    }
};

console.log("[Arena Workflow Analyzer] Extension loaded successfully");
}

// Start waiting for app
waitForApp();
