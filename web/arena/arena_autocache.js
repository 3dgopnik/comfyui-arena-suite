// Arena AutoCache v3 - Core JavaScript functionality
// Provides autocache overlay and model path interception for ComfyUI

console.log("[Arena AutoCache v3] Loading...");

class ArenaAutoCache {
    constructor() {
        this.cacheDir = null;
        this.isEnabled = false;
        this.modelCache = new Map();
        this.workflowFileDialog = null;
        this.init();
    }

    init() {
        // Initialize autocache functionality
        this.setupModelPathInterception();
        this.setupUIOverlay();
        this.setupWorkflowFileDialog();
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

    setupWorkflowFileDialog() {
        // Create workflow file selection dialog
        this.workflowFileDialog = document.createElement('div');
        this.workflowFileDialog.id = 'arena-workflow-dialog';
        this.workflowFileDialog.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 20000;
            display: none;
            justify-content: center;
            align-items: center;
        `;

        const dialogContent = document.createElement('div');
        dialogContent.style.cssText = `
            background: white;
            padding: 20px;
            border-radius: 10px;
            max-width: 600px;
            width: 90%;
            max-height: 80%;
            overflow-y: auto;
        `;

        dialogContent.innerHTML = `
            <h3>Arena AutoCache - Select Workflow File</h3>
            <div id="workflow-file-list" style="margin: 20px 0;">
                <p>Loading workflow files...</p>
            </div>
            <div style="text-align: right;">
                <button id="workflow-dialog-cancel" style="margin-right: 10px; padding: 8px 16px;">Cancel</button>
                <button id="workflow-dialog-refresh" style="margin-right: 10px; padding: 8px 16px;">Refresh</button>
            </div>
        `;

        this.workflowFileDialog.appendChild(dialogContent);
        document.body.appendChild(this.workflowFileDialog);

        // Setup event listeners
        document.getElementById('workflow-dialog-cancel').onclick = () => this.hideWorkflowDialog();
        document.getElementById('workflow-dialog-refresh').onclick = () => this.loadWorkflowFiles();
    }

    showWorkflowDialog() {
        console.log("[Arena AutoCache] Showing workflow file dialog");
        this.workflowFileDialog.style.display = 'flex';
        this.loadWorkflowFiles();
    }

    hideWorkflowDialog() {
        console.log("[Arena AutoCache] Hiding workflow file dialog");
        this.workflowFileDialog.style.display = 'none';
    }

    async loadWorkflowFiles() {
        const fileList = document.getElementById('workflow-file-list');
        fileList.innerHTML = '<p>Loading workflow files...</p>';

        try {
            // Try to get workflow files from ComfyUI API
            const response = await fetch('/api/workflows', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const workflows = await response.json();
                this.displayWorkflowFiles(workflows);
            } else {
                // Fallback: show manual file input
                this.showManualFileInput();
            }
        } catch (error) {
            console.log("[Arena AutoCache] API not available, showing manual input");
            this.showManualFileInput();
        }
    }

    displayWorkflowFiles(workflows) {
        const fileList = document.getElementById('workflow-file-list');
        
        if (!workflows || workflows.length === 0) {
            fileList.innerHTML = '<p>No workflow files found. Use manual selection below.</p>';
            this.showManualFileInput();
            return;
        }

        let html = '<h4>Available Workflow Files:</h4><ul style="list-style: none; padding: 0;">';
        
        workflows.forEach((workflow, index) => {
            const fileName = workflow.name || `workflow_${index + 1}.json`;
            const filePath = workflow.path || '';
            const modified = workflow.modified ? new Date(workflow.modified).toLocaleString() : 'Unknown';
            
            html += `
                <li style="padding: 10px; border: 1px solid #ddd; margin: 5px 0; border-radius: 5px; cursor: pointer;"
                    onclick="window.arenaAutoCache.selectWorkflowFile('${filePath}', '${fileName}')">
                    <strong>${fileName}</strong><br>
                    <small style="color: #666;">Path: ${filePath}</small><br>
                    <small style="color: #666;">Modified: ${modified}</small>
                </li>
            `;
        });
        
        html += '</ul>';
        fileList.innerHTML = html;
    }

    showManualFileInput() {
        const fileList = document.getElementById('workflow-file-list');
        fileList.innerHTML = `
            <h4>Manual File Selection:</h4>
            <p>Select a workflow file manually:</p>
            <input type="file" id="manual-workflow-file" accept=".json" style="width: 100%; padding: 8px; margin: 10px 0;">
            <button id="load-manual-file" style="padding: 8px 16px; margin-top: 10px;">Load Selected File</button>
        `;

        document.getElementById('load-manual-file').onclick = () => {
            const fileInput = document.getElementById('manual-workflow-file');
            if (fileInput.files.length > 0) {
                const file = fileInput.files[0];
                this.selectWorkflowFile(file.name, file.name);
            }
        };
    }

    selectWorkflowFile(filePath, fileName) {
        console.log(`[Arena AutoCache] Selected workflow file: ${fileName} (${filePath})`);
        
        // Store selected file for use by the node
        this.selectedWorkflowFile = filePath;
        
        // Show confirmation
        this.showOverlay(`Selected workflow: ${fileName}`);
        
        // Hide dialog
        this.hideWorkflowDialog();
        
        // Trigger workflow file selection event
        this.onWorkflowFileSelected(filePath, fileName);
    }

    onWorkflowFileSelected(filePath, fileName) {
        // This method can be overridden or extended
        console.log(`[Arena AutoCache] Workflow file selected: ${fileName}`);
        
        // Emit custom event for other components to listen
        const event = new CustomEvent('arena-workflow-selected', {
            detail: { filePath, fileName }
        });
        document.dispatchEvent(event);
    }

    getSelectedWorkflowFile() {
        return this.selectedWorkflowFile || null;
    }
}

// Initialize Arena AutoCache
window.arenaAutoCache = new ArenaAutoCache();