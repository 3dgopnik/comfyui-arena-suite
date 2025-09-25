// Arena AutoCache v3 - Core JavaScript functionality
// Provides autocache overlay and model path interception for ComfyUI

console.log("[Arena AutoCache v3] Loading...");

class ArenaAutoCache {
    constructor() {
        this.cacheDir = null;
        this.isEnabled = false;
        this.modelCache = new Map();
        this.init();
    }

    init() {
        // Initialize autocache functionality
        this.setupModelPathInterception();
        this.setupUIOverlay();
        console.log("[Arena AutoCache v3] Initialized");
    }

    setupModelPathInterception() {
        // Intercept model loading to redirect to cache
        const originalLoadModel = app.loadModel;
        app.loadModel = (modelName, ...args) => {
            const cachedPath = this.getCachedModelPath(modelName);
            if (cachedPath) {
                console.log(`[Arena AutoCache] Using cached model: ${modelName}`);
                return originalLoadModel.call(app, cachedPath, ...args);
            }
            return originalLoadModel.call(app, modelName, ...args);
        };
    }

    setupUIOverlay() {
        // Add autocache status overlay
        const overlay = document.createElement('div');
        overlay.id = 'arena-autocache-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            z-index: 10000;
            display: none;
        `;
        document.body.appendChild(overlay);
    }

    getCachedModelPath(modelName) {
        // Check if model is cached
        return this.modelCache.get(modelName) || null;
    }

    setCacheDir(path) {
        this.cacheDir = path;
        console.log(`[Arena AutoCache] Cache directory set to: ${path}`);
    }

    enable() {
        this.isEnabled = true;
        this.showOverlay('Arena AutoCache: Enabled');
    }

    disable() {
        this.isEnabled = false;
        this.showOverlay('Arena AutoCache: Disabled');
    }

    showOverlay(message) {
        const overlay = document.getElementById('arena-autocache-overlay');
        if (overlay) {
            overlay.textContent = message;
            overlay.style.display = 'block';
            setTimeout(() => {
                overlay.style.display = 'none';
            }, 3000);
        }
    }
}

// Initialize Arena AutoCache
window.arenaAutoCache = new ArenaAutoCache();