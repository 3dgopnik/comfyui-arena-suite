// Arena Simple Header Extension - Based on ComfyUI-Crystools approach
// Simple button in ComfyUI header for Arena AutoCache
import { app } from "../../scripts/app.js";


// RU: Cache modes for Arena button
                const CACHE_MODES = {
                    GRAY: 'gray',   // ARENA_AUTO_CACHE_ENABLED=0, ARENA_AUTOCACHE_AUTOPATCH=0
                    RED: 'red',     // ARENA_AUTO_CACHE_ENABLED=1, ARENA_AUTOCACHE_AUTOPATCH=1  
                    GREEN: 'green'  // ARENA_AUTO_CACHE_ENABLED=1, ARENA_AUTOCACHE_AUTOPATCH=0
                };

app.registerExtension({
    name: "ArenaSimple.Header",
    
    setup() {
            
            // Wait for DOM to be ready
            setTimeout(() => {
                console.log("[Arena Simple Header] DOM timeout started...");
                
                // Try to find the menu element using ComfyUI-Crystools approach
                const queueButton = document.getElementById('queue-button');
                console.log("[Arena Simple Header] Queue button found:", queueButton);
                
                if (!queueButton) {
                    console.error("[Arena Simple Header] Queue button not found!");
                    return;
                }
                
                // Create Arena button group (like ComfyUI Run button - split button)
                const buttonGroup = document.createElement('div');
                buttonGroup.className = 'arena-button-group';
                buttonGroup.style.cssText = `
                    display: flex;
                    align-items: center;
                    background: #3a3a3a;
                    border: 1px solid #555;
                    border-radius: 6px;
                    overflow: hidden;
                    min-height: 32px;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
                    transition: all 0.2s ease;
                    cursor: pointer;
                    user-select: none;
                `;

                // Main button with progress bar
                const mainButton = document.createElement('button');
                mainButton.className = 'arena-main-button';
        mainButton.innerHTML = `
            <div class="arena-button-content">
                <div class="arena-progress-bar" style="display: none;">
                    <div class="arena-progress-fill"></div>
                </div>
                <span class="arena-progress-text" style="z-index: 2; position: relative; display: none; margin-right: 6px; font-weight: bold; font-size: 12px;">0%</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 6px; z-index: 2; position: relative;">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                <span style="z-index: 2; position: relative;">ACACHE</span>
            </div>
        `;
                mainButton.title = 'Arena AutoCache (Click to toggle)';
                mainButton.style.cssText = `
                    background: transparent;
                    color: #e0e0e0;
                    border: none;
                    padding: 6px 12px;
                    margin: 0;
                    cursor: pointer;
                    font-size: 13px;
                    font-weight: 500;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.15s ease;
                    min-width: 60px;
                    height: 30px;
                    border-right: 1px solid #555;
                    position: relative;
                    overflow: hidden;
                `;

                // Settings button (opens ComfyUI settings)
                const settingsButton = document.createElement('button');
                settingsButton.className = 'arena-settings-button';
                settingsButton.innerHTML = `
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm8.94 3c-.46-4.17-3.77-7.48-7.94-7.94V1h-2v2.06C6.83 3.52 3.52 6.83 3.06 11H1v2h2.06c.46 4.17 3.77 7.48 7.94 7.94V23h2v-2.06c4.17-.46 7.48-3.77 7.94-7.94H23v-2h-2.06zM12 19c-3.87 0-7-3.13-7-7s3.13-7 7-7 7 3.13 7 7-3.13 7-7 7z"/>
                    </svg>
                `;
                settingsButton.title = 'Открыть настройки Arena AutoCache';
                settingsButton.style.cssText = `
                    background: transparent;
                    color: #e0e0e0;
                    border: none;
                    padding: 6px 8px;
                    margin: 0;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.15s ease;
                    width: 24px;
                    height: 30px;
                `;

                // RU: Add settings button click handler
                settingsButton.addEventListener('click', (e) => {
                    e.stopPropagation();
                    console.log("[Arena Simple Header] Settings button clicked!");
                    
                    // RU: Try to find and click existing settings button in ComfyUI
                    try {
                        // Method 1: Look for settings button by various selectors
                        const selectors = [
                            '[title*="Settings"]',
                            '[title*="settings"]', 
                            '.settings-btn',
                            '#settings-btn',
                            'button[aria-label*="settings"]',
                            'button[aria-label*="Settings"]',
                            '.comfy-settings-btn',
                            '[data-tooltip*="settings"]',
                            '[data-tooltip*="Settings"]'
                        ];
                        
                        let foundButton = null;
                        for (const selector of selectors) {
                            foundButton = document.querySelector(selector);
                            if (foundButton) {
                                console.log(`[Arena Simple Header] Found settings button with selector: ${selector}`);
                                break;
                            }
                        }
                        
                        if (foundButton) {
                            console.log("[Arena Simple Header] Clicking existing settings button");
                            foundButton.click();
                            
                            // RU: Try to navigate to Arena section after settings open
                            setTimeout(() => {
                                try {
                                    // Method 1: Look for Arena section/tab
                                    const arenaSection = document.querySelector('[data-id="arena"], .arena-section, #arena, [href*="arena"]');
                                    if (arenaSection) {
                                        console.log("[Arena Simple Header] Found Arena section, clicking it");
                                        arenaSection.click();
                                        return;
                                    }
                                    
                                    // Method 2: Look for Arena in settings list (more specific)
                                    const settingsElements = document.querySelectorAll('div, span, button, a, li, td, th');
                                    for (const item of settingsElements) {
                                        if (item.textContent && 
                                            item.textContent.toLowerCase().includes('arena') && 
                                            !item.textContent.includes('@layer') &&
                                            !item.textContent.includes('CSS') &&
                                            item.textContent.length < 100) { // Avoid long CSS/text content
                                            console.log("[Arena Simple Header] Found Arena item:", item.textContent.trim());
                                            if (item.click) {
                                                item.click();
                                                break;
                                            }
                                        }
                                    }
                                    
                                    // Method 3: Look for specific Arena settings patterns
                                    const arenaPatterns = [
                                        'Arena AutoCache',
                                        'Arena Settings', 
                                        'Arena Configuration',
                                        'Arena',
                                        'arena'
                                    ];
                                    
                                    for (const pattern of arenaPatterns) {
                                        const elements = document.querySelectorAll('*');
                                        for (const elem of elements) {
                                            if (elem.textContent && 
                                                elem.textContent.trim() === pattern &&
                                                elem.click) {
                                                console.log(`[Arena Simple Header] Found exact match: "${pattern}"`);
                                                elem.click();
                                                return;
                                            }
                                        }
                                    }
                                } catch (error) {
                                    console.error("[Arena Simple Header] Error navigating to Arena section:", error);
                                }
                            }, 500); // Wait for settings to fully load
                            
                            return;
                        }
                        
                        // Method 2: Try to trigger via keyboard shortcut (Ctrl+,)
                        console.log("[Arena Simple Header] Trying keyboard shortcut Ctrl+,");
                        const ctrlCommaEvent = new KeyboardEvent('keydown', {
                            key: ',',
                            code: 'Comma',
                            ctrlKey: true,
                            bubbles: true
                        });
                        document.dispatchEvent(ctrlCommaEvent);
                        
                        // Method 3: Try app.ui.settings if available
                        if (app && app.ui && app.ui.settings && typeof app.ui.settings.show === 'function') {
                            console.log("[Arena Simple Header] Using app.ui.settings.show()");
                            app.ui.settings.show();
                            
                            // RU: Try to navigate to Arena section
                            setTimeout(() => {
                                try {
                                    const arenaSection = document.querySelector('[data-id="arena"], .arena-section, #arena, [href*="arena"]');
                                    if (arenaSection) {
                                        console.log("[Arena Simple Header] Found Arena section, clicking it");
                                        arenaSection.click();
                                    } else {
                                        // Look for Arena text and click it (more specific)
                                        const arenaPatterns = [
                                            'Arena AutoCache',
                                            'Arena Settings', 
                                            'Arena Configuration',
                                            'Arena',
                                            'arena'
                                        ];
                                        
                                        for (const pattern of arenaPatterns) {
                                            const elements = document.querySelectorAll('div, span, button, a, li, td, th');
                                            for (const elem of elements) {
                                                if (elem.textContent && 
                                                    elem.textContent.trim() === pattern &&
                                                    !elem.textContent.includes('@layer') &&
                                                    elem.click) {
                                                    console.log(`[Arena Simple Header] Found exact match: "${pattern}"`);
                                                    elem.click();
                                                    return;
                                                }
                                            }
                                        }
                                    }
                                } catch (error) {
                                    console.error("[Arena Simple Header] Error navigating to Arena section:", error);
                                }
                            }, 500);
                            
                            return;
                        }
                        
                        console.warn("[Arena Simple Header] No settings button or API found");
                        
                    } catch (error) {
                        console.error("[Arena Simple Header] Failed to open settings:", error);
                    }
                });

                // Hover effects
                buttonGroup.addEventListener('mouseenter', () => {
                    buttonGroup.style.background = '#4a4a4a';
                    buttonGroup.style.borderColor = '#666';
                    mainButton.style.background = '#4a4a4a';
                    settingsButton.style.background = '#4a4a4a';
                });

                buttonGroup.addEventListener('mouseleave', () => {
                    buttonGroup.style.background = '#3a3a3a';
                    buttonGroup.style.borderColor = '#555';
                    mainButton.style.background = 'transparent';
                    settingsButton.style.background = 'transparent';
                });

                // RU: No active state animations to prevent header jerking

                // Add buttons to group
                buttonGroup.appendChild(mainButton);
                buttonGroup.appendChild(settingsButton);
                
                // RU: No dropdown menu functionality for now

                // Use mainButton for compatibility with existing code
                const button = mainButton;
                
                // Analyze existing ComfyUI structure to find the right place
                console.log("[Arena Simple Header] Analyzing ComfyUI DOM structure...");
                
                // Look for ComfyUI floating toolbar/dockable panel (but NOT actionbar)
                const floatingToolbar = document.querySelector('.comfy-toolbar') ||
                                      document.querySelector('.floating-toolbar') ||
                                      document.querySelector('.dockable-toolbar') ||
                                      document.querySelector('.toolbar-floating') ||
                                      document.querySelector('[class*="toolbar"][class*="float"]');
                
                // Exclude actionbar (where Run button is) - we don't want to add to it
                const actionbar = document.querySelector('.actionbar, [class*="actionbar"]');
                if (actionbar) {
                    console.log("[Arena Simple Header] Found actionbar (Run button panel) - will avoid it:", actionbar);
                }
                
                console.log("[Arena Simple Header] Floating toolbar found:", floatingToolbar);
                
                // Find all existing buttons in the header area
                const existingButtons = document.querySelectorAll('button[id*="queue"], button[class*="queue"], button[class*="run"], button[class*="manager"]');
                console.log("[Arena Simple Header] Existing buttons found:", existingButtons.length);
                
                // Look for ComfyUI-Crystools buttons (they use ComfyButtonGroup)
                const crystoolsButtons = document.querySelectorAll('.comfy-button-group button, .crystools-button');
                console.log("[Arena Simple Header] ComfyUI-Crystools buttons found:", crystoolsButtons.length);
                
                // Look for any draggable/dockable elements
                const draggableElements = document.querySelectorAll('[draggable="true"], [class*="drag"], [class*="dock"]');
                console.log("[Arena Simple Header] Draggable elements found:", draggableElements.length);
                
                // Find the main ComfyUI header container
                let targetContainer = null;
                let insertionMethod = 'append';
                
                // Create Arena Actionbar (based on ComfyUI Actionbar implementation)
                console.log("[Arena Simple Header] Creating Arena Actionbar...");
                
                // Load saved position from localStorage
                const getStoredPosition = () => {
                    try {
                        const stored = localStorage.getItem('Arena.Actionbar.Position');
                        return stored ? JSON.parse(stored) : { x: window.innerWidth - 200, y: 20 };
                    } catch {
                        return { x: window.innerWidth - 200, y: 20 };
                    }
                };
                
                const savePosition = (position) => {
                    try {
                        localStorage.setItem('Arena.Actionbar.Position', JSON.stringify(position));
                    } catch (e) {
                        console.warn('[Arena Simple Header] Failed to save position:', e);
                    }
                };
                
                const getStoredDocked = () => {
                    try {
                        const stored = localStorage.getItem('Arena.Actionbar.Docked');
                        return stored === 'true';
                    } catch {
                        return false;
                    }
                };
                
                const saveDocked = (docked) => {
                    try {
                        localStorage.setItem('Arena.Actionbar.Docked', docked.toString());
                    } catch (e) {
                        console.warn('[Arena Simple Header] Failed to save docked state:', e);
                    }
                };
                
                // Create Arena Actionbar container (styled like ComfyUI Run menu)
                const arenaActionbar = document.createElement('div');
                arenaActionbar.className = 'arena-actionbar';
                arenaActionbar.style.cssText = `
                    position: fixed;
                    background: #2a2a2a;
                    border: 1px solid #444;
                    border-radius: 6px;
                    padding: 4px 6px;
                    display: flex;
                    align-items: center;
                    gap: 4px;
                    z-index: 10000;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                    transition: all 0.3s ease;
                    cursor: grab;
                    user-select: none;
                    min-height: 36px;
                `;
                
                // Add drag handle (like ComfyUI Run menu - 6 dots pattern)
                const dragHandle = document.createElement('div');
                dragHandle.className = 'arena-drag-handle';
                dragHandle.style.cssText = `
                    width: 16px;
                    height: 16px;
                    background: transparent;
                    border-radius: 2px;
                    cursor: grab;
                    margin-right: 8px;
                    display: flex;
                    flex-wrap: wrap;
                    align-items: center;
                    justify-content: center;
                    padding: 2px;
                `;
                dragHandle.title = 'Drag to move';
                
                // Create 6 dots pattern (2x3 grid like ComfyUI)
                for (let i = 0; i < 6; i++) {
                    const dot = document.createElement('div');
                    dot.style.cssText = `
                        width: 2px;
                        height: 2px;
                        background: #999;
                        border-radius: 50%;
                        margin: 1px;
                    `;
                    dragHandle.appendChild(dot);
                }
                
                // Initialize position and state
                const storedPosition = getStoredPosition();
                const isDocked = getStoredDocked();
                
                if (isDocked) {
                    // Try to dock in header - use the same logic as drag docking
                    const comfyuiMenu = document.querySelector('.comfyui-menu.flex.items-center');
                    if (comfyuiMenu) {
                        arenaActionbar.style.position = 'relative';
                        arenaActionbar.style.top = 'auto';
                        arenaActionbar.style.right = 'auto';
                        arenaActionbar.style.left = 'auto';
                        arenaActionbar.style.background = 'transparent';
                        arenaActionbar.style.border = 'none';
                        arenaActionbar.style.padding = '4px';
                        arenaActionbar.style.boxShadow = 'none';
                        arenaActionbar.style.backdropFilter = 'none';
                        arenaActionbar.style.cursor = 'default';
                        comfyuiMenu.appendChild(arenaActionbar);
                        console.log("[Arena Simple Header] Arena Actionbar docked in comfyui-menu on startup");
                    } else {
                        // Fallback: Try other header selectors
                        const headerArea = document.querySelector('.header, .toolbar, .comfyui-toolbar, .main-header');
                        if (headerArea) {
                            arenaActionbar.style.position = 'relative';
                            arenaActionbar.style.top = 'auto';
                            arenaActionbar.style.right = 'auto';
                            arenaActionbar.style.left = 'auto';
                            arenaActionbar.style.background = 'transparent';
                            arenaActionbar.style.border = 'none';
                            arenaActionbar.style.padding = '4px';
                            arenaActionbar.style.boxShadow = 'none';
                            arenaActionbar.style.backdropFilter = 'none';
                            arenaActionbar.style.cursor = 'default';
                            headerArea.appendChild(arenaActionbar);
                            console.log("[Arena Simple Header] Arena Actionbar docked in fallback header");
                        } else {
                            // Fallback to floating if no header found
                            arenaActionbar.style.left = storedPosition.x + 'px';
                            arenaActionbar.style.top = storedPosition.y + 'px';
                            document.body.appendChild(arenaActionbar);
                            console.log("[Arena Simple Header] Arena Actionbar floating (no header found)");
                        }
                    }
                } else {
                    // Floating position
                    arenaActionbar.style.left = storedPosition.x + 'px';
                    arenaActionbar.style.top = storedPosition.y + 'px';
                    document.body.appendChild(arenaActionbar);
                    console.log("[Arena Simple Header] Arena Actionbar floating");
                }
                
                // Add drag handle to actionbar
                arenaActionbar.appendChild(dragHandle);
                targetContainer = arenaActionbar;
                
                // Enhanced dragging logic (based on ComfyUI) - мгновенный drag
                let isDragging = false;
                let dragStart = { x: 0, y: 0 };
                let elementStart = { x: 0, y: 0 };
                let dragThreshold = 5; // Минимальное расстояние для начала drag
                
                const startDrag = (e) => {
                    // Предотвращаем дергание других элементов
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Если закреплен, сначала открепляем
                    if (arenaActionbar.style.position === 'relative') {
                        console.log("[Arena Simple Header] Undocking for drag...");
                        
                        // Сохраняем позицию курсора для undock
                        const currentRect = arenaActionbar.getBoundingClientRect();
                        const position = {
                            x: e.clientX - 50,
                            y: e.clientY - 20
                        };
                        savePosition(position);
                        saveDocked(false);
                        
                        // Делаем floating
                        arenaActionbar.style.position = 'fixed';
                        arenaActionbar.style.top = position.y + 'px';
                        arenaActionbar.style.left = position.x + 'px';
                        arenaActionbar.style.background = '#2a2a2a';
                        arenaActionbar.style.border = '1px solid #444';
                        arenaActionbar.style.padding = '4px 6px';
                        arenaActionbar.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.3)';
                        arenaActionbar.style.cursor = 'grab';
                        
                        // Перемещаем в body
                        document.body.appendChild(arenaActionbar);
                        
                        console.log("[Arena Simple Header] Undocked successfully");
                    }
                    
                    isDragging = true;
                    dragStart.x = e.clientX;
                    dragStart.y = e.clientY;
                    elementStart.x = parseInt(arenaActionbar.style.left) || 0;
                    elementStart.y = parseInt(arenaActionbar.style.top) || 0;
                    
                    // Visual feedback during drag (like ComfyUI)
                    arenaActionbar.style.cursor = 'grabbing';
                    arenaActionbar.style.transition = 'none';
                    arenaActionbar.style.opacity = '0.8';
                    arenaActionbar.style.transform = 'scale(1.02)';
                    arenaActionbar.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.6)';
                    document.body.style.userSelect = 'none';
                    
                    console.log("[Arena Simple Header] Drag started");
                };
                
                const doDrag = (e) => {
                    if (!isDragging) return;
                    
                    // Предотвращаем дергание других элементов
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const deltaX = e.clientX - dragStart.x;
                    const deltaY = e.clientY - dragStart.y;
                    
                    // Проверяем минимальное расстояние для начала drag
                    const dragDistance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
                    if (dragDistance < dragThreshold) return;
                    
                    arenaActionbar.style.left = (elementStart.x + deltaX) + 'px';
                    arenaActionbar.style.top = (elementStart.y + deltaY) + 'px';
                    arenaActionbar.style.right = 'auto';
                    
                    // Check for docking zones during drag (like ComfyUI Run menu)
                    const rect = arenaActionbar.getBoundingClientRect();
                    const shouldDock = rect.top < 120; // Top 120px is header area
                    
                    if (shouldDock) {
                        // Show docking zone highlight only during active drag
                        arenaActionbar.style.background = '#1a4a1a'; // Green tint
                        arenaActionbar.style.border = '1px solid #4a9a4a';
                        
                        // Also highlight potential docking areas
                        const headerSelectors = [
                            '#queue-button', 
                            '.comfy-menu', 
                            '.comfyui-menu.flex.items-center', // Приоритетный селектор из логов
                            '.header', 
                            '.toolbar', 
                            '.comfyui-toolbar'
                        ];
                        
                        for (const selector of headerSelectors) {
                            const element = document.querySelector(selector);
                            if (element && element.style.display !== 'none') {
                                // Add temporary highlight class
                                element.style.boxShadow = '0 0 10px rgba(74, 154, 74, 0.5)';
                                element.style.transition = 'box-shadow 0.2s ease';
                            }
                        }
                    } else {
                        // Remove docking highlight
                        arenaActionbar.style.background = '#2a2a2a';
                        arenaActionbar.style.border = '1px solid #444';
                        
                        // Remove highlights from docking zones
                        const headerSelectors = [
                            '#queue-button', 
                            '.comfy-menu', 
                            '.comfyui-menu.flex.items-center',
                            '.header', 
                            '.toolbar', 
                            '.comfyui-toolbar'
                        ];
                        
                        for (const selector of headerSelectors) {
                            const element = document.querySelector(selector);
                            if (element) {
                                element.style.boxShadow = '';
                            }
                        }
                    }
                };
                
                const endDrag = () => {
                    if (!isDragging) return;
                    
                    isDragging = false;
                    
                    // Reset visual feedback
                    arenaActionbar.style.cursor = 'grab';
                    arenaActionbar.style.transition = 'all 0.3s ease';
                    arenaActionbar.style.opacity = '1';
                    arenaActionbar.style.transform = 'scale(1)';
                    arenaActionbar.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.3)';
                    document.body.style.userSelect = '';
                    
                    // Clear all docking zone highlights
                    const headerSelectors = [
                        '#queue-button', 
                        '.comfy-menu', 
                        '.header', 
                        '.toolbar', 
                        '.comfyui-toolbar'
                    ];
                    
                    for (const selector of headerSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            element.style.boxShadow = '';
                        }
                    }
                    
                    // Check for docking (like ComfyUI does)
                    const rect = arenaActionbar.getBoundingClientRect();
                    const shouldDock = rect.top < 120; // Top 120px is header area
                    
                    if (shouldDock) {
                        console.log("[Arena Simple Header] Attempting to dock...");
                        
                        // Try multiple header selectors (ComfyUI has different layouts)
                        const headerSelectors = [
                            '#queue-button',  // Try queue button first - we know it exists
                            '.comfyui-menu',  // ComfyUI Desktop specific
                            '.comfy-menu', 
                            '.header', 
                            '.toolbar', 
                            '.comfyui-toolbar', 
                            '.main-header',
                            '[class*="menu"]',
                            '[class*="header"]',
                            'header',  // Generic header element
                            '[data-v-95a7d5d6]'  // Vue component identifier from logs
                        ];
                        
                        let headerArea = null;
                        let foundSelector = null;
                        for (const selector of headerSelectors) {
                            headerArea = document.querySelector(selector);
                            if (headerArea && headerArea.offsetHeight > 0 && headerArea.style.display !== 'none') {
                                foundSelector = selector;
                                console.log(`[Arena Simple Header] Found header with selector: ${selector}`);
                                break;
                            }
                        }
                        
                        if (headerArea) {
                            console.log("[Arena Simple Header] Header area found:", headerArea);
                            console.log("[Arena Simple Header] Header classes:", headerArea.className);
                            console.log("[Arena Simple Header] Header parent:", headerArea.parentElement);
                            
                            // Special handling for queue-button
                            if (foundSelector === '#queue-button') {
                                console.log("[Arena Simple Header] Special handling for queue-button");
                                
                                // Try to find the comfyui-menu container (from logs)
                                const comfyuiMenu = document.querySelector('.comfyui-menu.flex.items-center');
                                if (comfyuiMenu) {
                                    console.log("[Arena Simple Header] Found comfyui-menu container:", comfyuiMenu);
                                    
                                    // Visual feedback for successful docking
                                    arenaActionbar.style.background = '#1a4a1a'; // Green tint
                                    arenaActionbar.style.border = '1px solid #4a9a4a';
                                    
                                    setTimeout(() => {
                                        // Dock in comfyui-menu container
                                        arenaActionbar.style.position = 'relative';
                                        arenaActionbar.style.top = 'auto';
                                        arenaActionbar.style.right = 'auto';
                                        arenaActionbar.style.left = 'auto';
                                        arenaActionbar.style.background = 'transparent';
                                        arenaActionbar.style.border = 'none';
                                        arenaActionbar.style.padding = '4px';
                                        arenaActionbar.style.boxShadow = 'none';
                                        arenaActionbar.style.backdropFilter = 'none';
                                        arenaActionbar.style.cursor = 'default';
                                        
                                        // Insert in comfyui-menu container
                                        comfyuiMenu.appendChild(arenaActionbar);
                                        saveDocked(true);
                                        console.log("[Arena Simple Header] Arena Actionbar docked successfully in comfyui-menu container");
                                    }, 300);
                                    return;
                                }
                                
                                // Fallback: Try to insert after queue button
                                const queueButtonParent = headerArea.parentElement;
                                if (queueButtonParent) {
                                    console.log("[Arena Simple Header] Queue button parent found:", queueButtonParent);
                                    
                                    // Visual feedback for successful docking
                                    arenaActionbar.style.background = '#1a4a1a'; // Green tint
                                    arenaActionbar.style.border = '1px solid #4a9a4a';
                                    
                                    setTimeout(() => {
                                        // Dock after queue button
                                        arenaActionbar.style.position = 'relative';
                                        arenaActionbar.style.top = 'auto';
                                        arenaActionbar.style.right = 'auto';
                                        arenaActionbar.style.left = 'auto';
                                        arenaActionbar.style.background = 'transparent';
                                        arenaActionbar.style.border = 'none';
                                        arenaActionbar.style.padding = '4px';
                                        arenaActionbar.style.boxShadow = 'none';
                                        arenaActionbar.style.backdropFilter = 'none';
                                        arenaActionbar.style.cursor = 'default';
                                        
                                        // Insert after queue button
                                        queueButtonParent.insertBefore(arenaActionbar, headerArea.nextSibling);
                                        saveDocked(true);
                                        console.log("[Arena Simple Header] Arena Actionbar docked successfully after queue button");
                                    }, 300);
                                    return;
                                }
                            }
                            
                            // Try to dock directly in the header area first
                            if (headerArea.style.display !== 'none' && headerArea.offsetHeight > 0) {
                                console.log("[Arena Simple Header] Trying to dock directly in header area");
                                
                                // Visual feedback for successful docking
                                arenaActionbar.style.background = '#1a4a1a'; // Green tint
                                arenaActionbar.style.border = '1px solid #4a9a4a';
                                
                                setTimeout(() => {
                                    // Dock directly in header
                                    arenaActionbar.style.position = 'relative';
                                    arenaActionbar.style.top = 'auto';
                                    arenaActionbar.style.right = 'auto';
                                    arenaActionbar.style.left = 'auto';
                                    arenaActionbar.style.background = 'transparent';
                                    arenaActionbar.style.border = 'none';
                                    arenaActionbar.style.padding = '4px';
                                    arenaActionbar.style.boxShadow = 'none';
                                    arenaActionbar.style.backdropFilter = 'none';
                                    arenaActionbar.style.cursor = 'default';
                                    
                                    headerArea.appendChild(arenaActionbar);
                                    saveDocked(true);
                                    console.log("[Arena Simple Header] Arena Actionbar docked successfully in header area");
                                }, 300);
                                return;
                            }
                            
                            // If direct docking failed, try parent container
                            let container = headerArea.parentElement;
                            while (container && container !== document.body) {
                                console.log("[Arena Simple Header] Checking container:", container);
                                console.log("[Arena Simple Header] Container classes:", container.className);
                                
                                // Look for a container that could hold our button
                                if (container.style.display !== 'none' && 
                                    container.offsetHeight > 0 && 
                                    (container.classList.contains('flex') || 
                                     container.style.display === 'flex' ||
                                     container.tagName === 'HEADER' ||
                                     container.classList.contains('toolbar') ||
                                     container.classList.contains('comfy-menu') ||
                                     container.tagName === 'DIV')) {
                                    console.log("[Arena Simple Header] Found suitable container:", container);
                                    break;
                                }
                                container = container.parentElement;
                            }
                            
                            if (container && container !== document.body) {
                                // Visual feedback for successful docking
                                arenaActionbar.style.background = '#1a4a1a'; // Green tint
                                arenaActionbar.style.border = '1px solid #4a9a4a';
                                
                                setTimeout(() => {
                                    // Dock in container
                                    arenaActionbar.style.position = 'relative';
                                    arenaActionbar.style.top = 'auto';
                                    arenaActionbar.style.right = 'auto';
                                    arenaActionbar.style.left = 'auto';
                                    arenaActionbar.style.background = 'transparent';
                                    arenaActionbar.style.border = 'none';
                                    arenaActionbar.style.padding = '4px';
                                    arenaActionbar.style.boxShadow = 'none';
                                    arenaActionbar.style.backdropFilter = 'none';
                                    arenaActionbar.style.cursor = 'default';
                                    
                                    container.appendChild(arenaActionbar);
                                    saveDocked(true);
                                    console.log("[Arena Simple Header] Arena Actionbar docked successfully in container");
                                }, 300);
                                return;
                            }
                        }
                        
                        console.log("[Arena Simple Header] No suitable header container found for docking");
                    }
                    
                    // Save floating position
                    const currentPosition = {
                        x: parseInt(arenaActionbar.style.left) || 0,
                        y: parseInt(arenaActionbar.style.top) || 0
                    };
                    savePosition(currentPosition);
                    saveDocked(false);
                    console.log("[Arena Simple Header] Arena Actionbar position saved:", currentPosition);
                };
                
                // Add event listeners - упрощенная логика без двойных нажатий
                dragHandle.addEventListener('mousedown', startDrag);
                document.addEventListener('mousemove', doDrag);
                document.addEventListener('mouseup', endDrag);
                
                // RU: Add click handler with three-mode logic
                button.addEventListener('click', async (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log("[Arena Simple Header] Button clicked!");
                    
                    // RU: No loading state to prevent header jerking
                    
                    try {
                        // RU: Determine next mode based on current mode
                        let nextMode;
                        switch (currentCacheMode) {
                            case CACHE_MODES.GRAY:
                                // White → Red (enable caching)
                                nextMode = CACHE_MODES.RED;
                                break;
                            case CACHE_MODES.RED:
                                // Red → Green (disable autopatch, keep enabled)
                                nextMode = CACHE_MODES.GREEN;
                                break;
                            case CACHE_MODES.GREEN:
                                // Green → White (disable everything)
                                nextMode = CACHE_MODES.GRAY;
                                break;
                            default:
                                nextMode = CACHE_MODES.GRAY;
                        }
                        
                        console.log(`[Arena Simple Header] Switching from ${currentCacheMode} to ${nextMode}`);
                        
                        // RU: Set new cache mode
                        await setCacheMode(nextMode);
                        
                        // RU: No need to restore button text
                        
                        console.log(`[Arena Simple Header] Cache mode switched to ${nextMode} successfully`);
                        
                    } catch (error) {
                        console.error("[Arena Simple Header] Error:", error);
                        // RU: No need to restore button text
                        buttonGroup.style.background = '#dc2626'; // Red for error
                        mainButton.title = `Error: ${error.message}`;
                        
                        // RU: Reset after 3 seconds
                        setTimeout(() => {
                            updateButtonAppearance();
                        }, 3000);
                    }
                });
                
                // Add button group to floating toolbar (вместо кнопки)
                targetContainer.appendChild(buttonGroup);
                console.log("[Arena Simple Header] Button group added to floating toolbar");
                console.log("[Arena Simple Header] Button group element:", buttonGroup);
                console.log("[Arena Simple Header] Button group visible:", buttonGroup.offsetWidth > 0 && buttonGroup.offsetHeight > 0);
                console.log("[Arena Simple Header] Button group parent:", buttonGroup.parentElement);
                
                // RU: Добавляем CSS стили для прогресс-бара (как у Crystools)
                const progressStyles = document.createElement('style');
                progressStyles.textContent = `
                    .arena-button-content {
                        position: relative;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        width: 100%;
                        height: 100%;
                    }
                    
            .arena-progress-bar {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                border-radius: 3px;
                overflow: hidden;
                pointer-events: none;
            }
            
            .arena-progress-fill {
                position: absolute;
                top: 0;
                left: 0;
                height: 100%;
                width: 0%;
                background: linear-gradient(90deg, rgba(76, 175, 80, 0.3) 0%, rgba(69, 160, 73, 0.3) 100%);
                transition: width 0.3s ease;
            }
                    
                    /* RU: Анимация копирования - кнопка заливается цветом */
                    .arena-main-button.copying {
                        background: linear-gradient(90deg, #2E7D32 0%, #388E3C 100%);
                        border-color: #4CAF50;
                    }
                    
                    .arena-main-button.copying .arena-progress-bar {
                        display: block;
                    }
                `;
                document.head.appendChild(progressStyles);
                console.log("[Arena Simple Header] Progress bar styles added");
                
                // RU: Initialize cache mode state
                let currentCacheMode = CACHE_MODES.GRAY;
                let uncachedModelsCount = 0;
                let progressPollingInterval = null;
                
                // RU: Functions for progress bar management
        function updateProgressBar(copyStatus) {
            const progressBar = mainButton.querySelector('.arena-progress-bar');
            const progressFill = mainButton.querySelector('.arena-progress-fill');
            const progressText = mainButton.querySelector('.arena-progress-text');
            
            if (!progressBar || !progressFill || !progressText) {
                return;
            }
            
            if (copyStatus.is_copying) {
                // RU: Показываем прогресс-бар и цифры
                progressBar.style.display = 'block';
                progressText.style.display = 'inline-block';
                
                // RU: Обновляем прогресс
                const progress = copyStatus.current_file_progress || 0;
                progressFill.style.width = `${progress}%`;
                progressText.textContent = `${progress}%`;
                
                // RU: Обновляем title с информацией о копировании
                const currentFile = copyStatus.current_file || 'Unknown';
                const copiedMB = Math.round((copyStatus.current_file_copied || 0) / 1024 / 1024);
                const totalMB = Math.round((copyStatus.current_file_size || 0) / 1024 / 1024);
                mainButton.title = `Copying: ${currentFile}\nProgress: ${copiedMB}/${totalMB} MB (${progress}%)`;
                
            } else {
                // RU: Скрываем прогресс-бар и цифры
                progressBar.style.display = 'none';
                progressText.style.display = 'none';
                
                // RU: Восстанавливаем обычный title
                updateButtonAppearance();
            }
        }
                
                async function checkCopyStatus() {
                    try {
                        const response = await fetch('/arena/copy_status');
                        if (response.ok) {
                            const data = await response.json();
                            if (data.status === 'success' && data.copy_status) {
                                updateProgressBar(data.copy_status);
                                
                                // RU: Если копирование активно - продолжаем polling
                                if (data.copy_status.is_copying) {
                                    if (!progressPollingInterval) {
                                        progressPollingInterval = setInterval(checkCopyStatus, 500); // 500ms
                                    }
                                } else {
                                    // RU: Если копирование завершено - останавливаем polling
                                    if (progressPollingInterval) {
                                        clearInterval(progressPollingInterval);
                                        progressPollingInterval = null;
                                    }
                                }
                            }
                        }
                    } catch (error) {
                        console.warn("[Arena Simple Header] Failed to check copy status:", error);
                    }
                }
                
                function startProgressPolling() {
                    if (!progressPollingInterval) {
                        progressPollingInterval = setInterval(checkCopyStatus, 1000); // 1s
                    }
                }
                
                function stopProgressPolling() {
                    if (progressPollingInterval) {
                        clearInterval(progressPollingInterval);
                        progressPollingInterval = null;
                    }
                }
                
                // RU: Functions for cache mode management
                async function checkUncachedModels() {
                    try {
                        const response = await fetch('/arena/uncached_models');
                        const data = await response.json();
                        uncachedModelsCount = data.uncached_count || 0;
                        return uncachedModelsCount;
                    } catch (error) {
                        console.warn("[Arena Simple Header] Failed to check uncached models:", error);
                        uncachedModelsCount = 0;
                        return 0;
                    }
                }
                
                function updateButtonAppearance() {
                    // RU: Reset button group appearance to default
                    buttonGroup.style.background = '#3a3a3a';
                    buttonGroup.style.borderColor = '#555';
                    settingsButton.style.color = '#e0e0e0';
                    
                    // RU: Keep text color white, change only icon color
                    mainButton.style.color = '#e0e0e0'; // Always white text
                    
                    // RU: Change only the icon color in the circle
                    const iconPath = mainButton.querySelector('svg path');
                    
                    switch (currentCacheMode) {
                        case CACHE_MODES.GRAY:
                            if (iconPath) iconPath.style.fill = '#e0e0e0'; // White icon
                            mainButton.title = 'Arena AutoCache: Выключено (клик для включения)';
                            break;
                        case CACHE_MODES.RED:
                            if (iconPath) iconPath.style.fill = '#ff6b6b'; // Red icon
                            mainButton.title = 'Arena AutoCache: Активное кеширование (клик для выключения)';
                            break;
                        case CACHE_MODES.GREEN:
                            if (iconPath) iconPath.style.fill = '#51cf66'; // Green icon
                            if (uncachedModelsCount > 0) {
                                mainButton.title = `Arena AutoCache: Только использование\n${uncachedModelsCount} моделей не в кеше\n(клик для перехода в режим кеширования)`;
                            } else {
                                mainButton.title = 'Arena AutoCache: Только использование (все модели в кеше)';
                            }
                            break;
                    }
                }
                
                async function setCacheMode(mode) {
                    console.log(`[Arena Simple Header] Setting cache mode to: ${mode}`);
                    currentCacheMode = mode;
                    
                    let enabled, autopatch;
                    switch (mode) {
                        case CACHE_MODES.GRAY:
                            enabled = false;
                            autopatch = false;
                            break;
                        case CACHE_MODES.RED:
                            enabled = true;
                            autopatch = true;
                            break;
                        case CACHE_MODES.GREEN:
                            enabled = true;
                            autopatch = false; // Only read from cache, don't cache new models
                            break;
                        default:
                            console.error(`[Arena Simple Header] Unknown cache mode: ${mode}`);
                            return;
                    }
                    
                    try {
                        // RU: Update environment variables
                        const updateResponse = await fetch('/arena/env', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                                env: {
                                    ARENA_AUTO_CACHE_ENABLED: enabled ? '1' : '0',
                                    ARENA_AUTOCACHE_AUTOPATCH: autopatch ? '1' : '0'
                                }
                            })
                        });
                        
                        if (updateResponse.ok) {
                            console.log(`[Arena Simple Header] Cache mode updated successfully: ${mode}`);
                        } else {
                            console.warn(`[Arena Simple Header] Failed to update cache mode: ${updateResponse.status}`);
                        }
                        
                        // RU: Если переключились на RED режим - сразу анализируем workflow и запускаем кеширование
                        if (mode === CACHE_MODES.RED) {
                            try {
                                console.log("[Arena Simple Header] RED mode activated - analyzing workflow and prefetching models...");
                                
                                // RU: Парсим текущий workflow
                                const prompt = app.graphToPrompt();
                                if (prompt && prompt.output) {
                                    // RU: Извлекаем все модели из prompt
                                    const models = [];
                                    Object.entries(prompt.output).forEach(([nodeId, node]) => {
                                        if (node.inputs) {
                                            // RU: Ищем все поля которые могут содержать имена моделей
                                            Object.entries(node.inputs).forEach(([key, value]) => {
                                                if (typeof value === 'string' && (
                                                    key.includes('ckpt') || key.includes('checkpoint') || 
                                                    key.includes('model') || key.includes('lora') || 
                                                    key.includes('vae') || key.includes('clip') ||
                                                    key.includes('controlnet') || key.includes('upscale')
                                                )) {
                                                    // RU: Определяем категорию по имени поля
                                                    let category = 'checkpoints';
                                                    if (key.includes('lora')) category = 'loras';
                                                    else if (key.includes('vae')) category = 'vae';
                                                    else if (key.includes('clip')) category = 'clip';
                                                    else if (key.includes('controlnet')) category = 'controlnet';
                                                    else if (key.includes('upscale')) category = 'upscale_models';
                                                    
                                                    models.push({ category, filename: value });
                                                }
                                            });
                                        }
                                    });
                                    
                                    if (models.length > 0) {
                                        console.log(`[Arena Simple Header] Found ${models.length} models in workflow:`, models);
                                        
                                        // RU: Отправляем на backend для предзагрузки
                                        const prefetchResponse = await fetch('/arena/analyze_workflow', {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({ 
                                                models: models,
                                                action: 'prefetch'
                                            })
                                        });
                                        
                                        if (prefetchResponse.ok) {
                                            console.log(`[Arena Simple Header] Prefetch started for ${models.length} models`);
                                        }
                                    } else {
                                        console.log("[Arena Simple Header] No models found in workflow");
                                    }
                                }
                            } catch (error) {
                                console.warn("[Arena Simple Header] Failed to prefetch workflow models:", error);
                            }
                        }
                        
                        // RU: Update button appearance
                        updateButtonAppearance();
                        
                        // RU: Check uncached models for green mode
                        if (mode === CACHE_MODES.GREEN) {
                            await checkUncachedModels();
                            updateButtonAppearance();
                        }
                        
                        // RU: Start progress polling for RED mode
                        if (mode === CACHE_MODES.RED) {
                            startProgressPolling();
                        } else {
                            stopProgressPolling();
                        }
                        
                        // RU: Start autopatch if needed
                        if (mode === CACHE_MODES.RED) {
                            try {
                                // RU: Use ONLY ArenaWorkflowAnalyzer to collect models
                                let requiredModels = [];
                                
                                if (window.ArenaWorkflowAnalyzer?.getCurrentWorkflowModels) {
                                    try {
                                        console.log('[Arena Simple Header] Using ArenaWorkflowAnalyzer to detect models...');
                                        const models = await window.ArenaWorkflowAnalyzer.getCurrentWorkflowModels();
                                        
                                        if (models && models.length > 0) {
                                            requiredModels = models.map(m => ({ 
                                                category: m.type, 
                                                filename: m.name 
                                            }));
                                            
                                            console.log(`[Arena Simple Header] ✅ Found ${requiredModels.length} models via ArenaWorkflowAnalyzer:`);
                                            requiredModels.forEach(m => {
                                                console.log(`  - ${m.category}/${m.filename}`);
                                            });
                                        } else {
                                            console.warn('[Arena Simple Header] ArenaWorkflowAnalyzer returned no models');
                                        }
                                    } catch (error) {
                                        console.warn('[Arena Simple Header] ArenaWorkflowAnalyzer failed:', error);
                                    }
                                } else {
                                    console.warn('[Arena Simple Header] ⚠️ ArenaWorkflowAnalyzer not available - prefetch disabled, ondemand caching will work on Run');
                                }
                                
                                // RU: NO FALLBACK - if Analyzer doesn't work, no prefetch
                                // Ondemand caching will still work when user clicks Run

                                // RU: Send models to workflow analyzer to auto-extend categories
                                if (requiredModels.length > 0) {
                                    try {
                                        console.log(`[Arena Simple Header] Sending ${requiredModels.length} models to workflow analyzer...`);
                                        const analyzeResp = await fetch('/arena/analyze_workflow', {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({ models: requiredModels })
                                        });
                                        if (analyzeResp.ok) {
                                            console.log('[Arena Simple Header] ✅ Workflow analyzer processed models');
                                        }
                                    } catch (anErr) {
                                        console.warn('[Arena Simple Header] analyze_workflow failed:', anErr);
                                    }
                                }

                                // RU: Start autopatch with required models for prefetch
                                const body = requiredModels.length > 0
                                    ? { action: 'start', required_models: requiredModels }
                                    : { action: 'start' };

                                console.log(`[Arena Simple Header] Starting autopatch with ${requiredModels.length} models...`);
                                const resp = await fetch('/arena/autopatch', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify(body)
                                });
                                
                                if (resp.ok) {
                                    const data = await resp.json().catch(() => ({}));
                                    console.log('[Arena Simple Header] ✅ Autopatch response:', data);
                                    if (data.cache_hits !== undefined && data.cache_misses !== undefined) {
                                        console.log(`  Cache hits: ${data.cache_hits}, Cache misses: ${data.cache_misses}, Planned: ${data.planned || 0}`);
                                    }
                                } else {
                                    console.warn('[Arena Simple Header] ❌ Autopatch HTTP error:', resp.status);
                                }
                            } catch (autopatchError) {
                                console.warn("[Arena Simple Header] Autopatch failed:", autopatchError);
                            }
                        }
                        
                    } catch (error) {
                        console.error("[Arena Simple Header] Error setting cache mode:", error);
                    }
                }
                
                // RU: Initialize button state with three-mode logic
                setTimeout(async () => {
                    try {
                        // RU: Try API to get current state
                        let enabled = false;
                        let autopatch = false;
                        
                        try {
                            const response = await fetch('/arena/env');
                            if (response.ok) {
                                const data = await response.json();
                                enabled = data.env?.ARENA_AUTO_CACHE_ENABLED === '1';
                                autopatch = data.env?.ARENA_AUTOCACHE_AUTOPATCH === '1';
                                console.log(`[Arena Simple Header] Got state from API: enabled=${enabled}, autopatch=${autopatch}`);
                            }
                        } catch (apiError) {
                            console.warn("[Arena Simple Header] API not available for initial state, using defaults");
                        }
                        
                        // RU: Determine initial cache mode
                        // If .env file exists, default to GREEN mode, otherwise GRAY (white icon)
                        if (!enabled && !autopatch) {
                            currentCacheMode = CACHE_MODES.GRAY; // White icon (no .env)
                        } else if (autopatch) {
                            currentCacheMode = CACHE_MODES.RED; // Red icon (active caching)
                        } else if (enabled && !autopatch) {
                            currentCacheMode = CACHE_MODES.GREEN; // Green icon (.env exists, default)
                        } else {
                            currentCacheMode = CACHE_MODES.GRAY; // Fallback to white
                        }
                        
                        console.log(`[Arena Simple Header] Initial cache mode: ${currentCacheMode}`);
                        
                        // RU: Update button appearance based on mode
                        updateButtonAppearance();
                        
                        // RU: Check uncached models for green mode
                        if (currentCacheMode === CACHE_MODES.GREEN) {
                            await checkUncachedModels();
                            updateButtonAppearance();
                        }
                        
                        // RU: Start progress polling if in RED mode
                        if (currentCacheMode === CACHE_MODES.RED) {
                            startProgressPolling();
                        }
                        
                    } catch (error) {
                        console.error("[Arena Simple Header] Failed to get initial state:", error);
                        // RU: Default to gray state
                        currentCacheMode = CACHE_MODES.GRAY;
                        updateButtonAppearance();
                    }
                }, 1000);
                
                // RU: Ensure safe reset on window close (sets 0/0 with keepalive)
                const resetEnv = () => {
                    try {
                        fetch('/arena/env', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                env: {
                                    ARENA_AUTO_CACHE_ENABLED: '0',
                                    ARENA_AUTOCACHE_AUTOPATCH: '0'
                                }
                            }),
                            keepalive: true
                        });
                    } catch {}
                };

                window.addEventListener('beforeunload', resetEnv);
                window.addEventListener('pagehide', resetEnv);
                
                // RU: Очищаем polling при закрытии страницы
                window.addEventListener('beforeunload', stopProgressPolling);
                window.addEventListener('pagehide', stopProgressPolling);

            }, 2000); // Wait 2 seconds for DOM
        }
});

console.log("[Arena Simple Header] Extension registered");
