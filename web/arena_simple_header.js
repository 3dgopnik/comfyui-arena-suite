// Arena Simple Header Extension - Based on ComfyUI-Crystools approach
// Simple button in ComfyUI header for Arena AutoCache
import { app } from "../../scripts/app.js";

console.log("[Arena Simple Header] Loading...");

app.registerExtension({
    name: "ArenaSimple.Header",
        
        setup() {
            console.log("[Arena Simple Header] Setting up simple header button...");
            
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

                // Main button
                const mainButton = document.createElement('button');
                mainButton.className = 'arena-main-button';
                mainButton.innerHTML = `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 6px;">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                    <span>ARENA</span>
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
                `;

                // Dropdown arrow button (like Run button)
                const dropdownButton = document.createElement('button');
                dropdownButton.className = 'arena-dropdown-button';
                dropdownButton.innerHTML = `
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M7 10l5 5 5-5z"/>
                    </svg>
                `;
                dropdownButton.title = 'Arena Options';
                dropdownButton.style.cssText = `
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

                // Hover effects
                buttonGroup.addEventListener('mouseenter', () => {
                    buttonGroup.style.background = '#4a4a4a';
                    buttonGroup.style.borderColor = '#666';
                    mainButton.style.background = '#4a4a4a';
                    dropdownButton.style.background = '#4a4a4a';
                });

                buttonGroup.addEventListener('mouseleave', () => {
                    buttonGroup.style.background = '#3a3a3a';
                    buttonGroup.style.borderColor = '#555';
                    mainButton.style.background = 'transparent';
                    dropdownButton.style.background = 'transparent';
                });

                // Active state
                mainButton.addEventListener('mousedown', () => {
                    buttonGroup.style.background = '#2a2a2a';
                    buttonGroup.style.transform = 'scale(0.98)';
                });

                dropdownButton.addEventListener('mousedown', () => {
                    buttonGroup.style.background = '#2a2a2a';
                    buttonGroup.style.transform = 'scale(0.98)';
                });

                document.addEventListener('mouseup', () => {
                    buttonGroup.style.transform = 'scale(1)';
                });

                // Add buttons to group
                buttonGroup.appendChild(mainButton);
                buttonGroup.appendChild(dropdownButton);

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
                
                // Add click handler with proper toggle logic
                button.addEventListener('click', async (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log("[Arena Simple Header] Button clicked!");
                    
                    // Show loading state
                    const originalText = button.innerHTML;
                    button.innerHTML = '...';
                    button.style.background = '#666';
                    
                    try {
                        // Try to get current state from localStorage first
                        let currentEnabled = false;
                        try {
                            const stored = localStorage.getItem('Arena.AutoCache.Enabled');
                            currentEnabled = stored === 'true';
                        } catch {}
                        
                        // Try to get from API if available
                        try {
                            const response = await fetch('/arena/env');
                            if (response.ok) {
                                const data = await response.json();
                                currentEnabled = data.env?.ARENA_AUTO_CACHE_ENABLED === '1';
                                console.log("[Arena Simple Header] Got state from API:", currentEnabled);
                            }
                        } catch (apiError) {
                            console.warn("[Arena Simple Header] API not available, using localStorage:", apiError);
                        }
                        
                        const newEnabled = !currentEnabled;
                        console.log(`[Arena Simple Header] Current: ${currentEnabled}, New: ${newEnabled}`);
                        
                        // Save to localStorage immediately
                        try {
                            localStorage.setItem('Arena.AutoCache.Enabled', newEnabled.toString());
                        } catch (storageError) {
                            console.warn("[Arena Simple Header] Failed to save to localStorage:", storageError);
                        }
                        
                        // Try to update via API if available
                        try {
                            const updateResponse = await fetch('/arena/env', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ 
                                    env: { ARENA_AUTO_CACHE_ENABLED: newEnabled ? '1' : '0' }
                                })
                            });
                            
                            if (updateResponse.ok) {
                                console.log("[Arena Simple Header] API update successful");
                            } else {
                                console.warn("[Arena Simple Header] API update failed:", updateResponse.status);
                            }
                        } catch (apiError) {
                            console.warn("[Arena Simple Header] API update failed:", apiError);
                        }
                        
                        // Update button group appearance
                        mainButton.innerHTML = originalText;
                        if (newEnabled) {
                            buttonGroup.style.background = '#2a5a2a';
                            buttonGroup.style.borderColor = '#4a9a4a';
                            mainButton.style.color = '#90ee90';
                            dropdownButton.style.color = '#90ee90';
                            mainButton.title = 'Arena AutoCache: ON (Click to disable)';
                        } else {
                            buttonGroup.style.background = '#3a3a3a';
                            buttonGroup.style.borderColor = '#555';
                            mainButton.style.color = '#e0e0e0';
                            dropdownButton.style.color = '#e0e0e0';
                            mainButton.title = 'Arena AutoCache: OFF (Click to enable)';
                        }
                        
                        console.log(`[Arena Simple Header] Cache ${newEnabled ? 'enabled' : 'disabled'} successfully`);
                        
                        // If enabling, try to start autopatch
                        if (newEnabled) {
                            try {
                                await fetch('/arena/autopatch', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ action: "start" })
                                });
                                console.log("[Arena Simple Header] Autopatch started");
                            } catch (autopatchError) {
                                console.warn("[Arena Simple Header] Autopatch failed:", autopatchError);
                            }
                        }
                        
                    } catch (error) {
                        console.error("[Arena Simple Header] Error:", error);
                        button.innerHTML = originalText;
                        button.style.background = '#dc2626'; // Red for error
                        button.title = `Error: ${error.message}`;
                        
                        // Reset after 3 seconds
                        setTimeout(() => {
                            // Try to get saved state
                            try {
                                const stored = localStorage.getItem('Arena.AutoCache.Enabled');
                                const isEnabled = stored === 'true';
                                if (isEnabled) {
                                    buttonGroup.style.background = '#2a5a2a';
                                    buttonGroup.style.borderColor = '#4a9a4a';
                                    mainButton.style.color = '#90ee90';
                                    dropdownButton.style.color = '#90ee90';
                                } else {
                                    buttonGroup.style.background = '#3a3a3a';
                                    buttonGroup.style.borderColor = '#555';
                                    mainButton.style.color = '#e0e0e0';
                                    dropdownButton.style.color = '#e0e0e0';
                                }
                                mainButton.title = `Arena AutoCache: ${isEnabled ? 'ON' : 'OFF'}`;
                            } catch {
                                buttonGroup.style.background = '#3a3a3a';
                                buttonGroup.style.borderColor = '#555';
                                mainButton.style.color = '#e0e0e0';
                                dropdownButton.style.color = '#e0e0e0';
                                mainButton.title = 'Arena AutoCache (Click to toggle)';
                            }
                        }, 3000);
                    }
                });
                
                // Add button group to floating toolbar (вместо кнопки)
                targetContainer.appendChild(buttonGroup);
                console.log("[Arena Simple Header] Button group added to floating toolbar");
                console.log("[Arena Simple Header] Button group element:", buttonGroup);
                console.log("[Arena Simple Header] Button group visible:", buttonGroup.offsetWidth > 0 && buttonGroup.offsetHeight > 0);
                console.log("[Arena Simple Header] Button group parent:", buttonGroup.parentElement);
                
                // Initialize button state
                setTimeout(async () => {
                    try {
                        // Try localStorage first
                        let enabled = false;
                        try {
                            const stored = localStorage.getItem('Arena.AutoCache.Enabled');
                            enabled = stored === 'true';
                        } catch {}
                        
                        // Try API if available
                        try {
                            const response = await fetch('/arena/env');
                            if (response.ok) {
                                const data = await response.json();
                                enabled = data.env?.ARENA_AUTO_CACHE_ENABLED === '1';
                                // Update localStorage with API value
                                localStorage.setItem('Arena.AutoCache.Enabled', enabled.toString());
                            }
                        } catch (apiError) {
                            console.warn("[Arena Simple Header] API not available for initial state, using localStorage");
                        }
                        
                        // Set button group appearance
                        if (enabled) {
                            buttonGroup.style.background = '#2a5a2a';
                            buttonGroup.style.borderColor = '#4a9a4a';
                            mainButton.style.color = '#90ee90';
                            dropdownButton.style.color = '#90ee90';
                        } else {
                            buttonGroup.style.background = '#3a3a3a';
                            buttonGroup.style.borderColor = '#555';
                            mainButton.style.color = '#e0e0e0';
                            dropdownButton.style.color = '#e0e0e0';
                        }
                        
                        mainButton.title = `Arena AutoCache: ${enabled ? 'ON' : 'OFF'} (Click to toggle)`;
                        console.log(`[Arena Simple Header] Initial state: ${enabled ? 'ON' : 'OFF'}`);
                    } catch (error) {
                        console.error("[Arena Simple Header] Failed to get initial state:", error);
                        // Default to off state
                        buttonGroup.style.background = '#3a3a3a';
                        buttonGroup.style.borderColor = '#555';
                        mainButton.style.color = '#e0e0e0';
                        dropdownButton.style.color = '#e0e0e0';
                        mainButton.title = 'Arena AutoCache: OFF';
                    }
                }, 1000);
                
            }, 2000); // Wait 2 seconds for DOM
        }
});

console.log("[Arena Simple Header] Extension registered");
