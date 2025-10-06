// Arena Settings Panel Extension - TEST VERSION
// Simple test to check if Settings Panel loads
import { app } from "../../../scripts/app.js";

console.log("[Arena Settings Panel TEST] Loading...");

app.registerExtension({
    name: "Arena.SettingsPanel.Test",
    
    setup() {
        console.log("[Arena Settings Panel TEST] Setting up...");
        
        // Test if we can access settings
        setTimeout(() => {
            console.log("[Arena Settings Panel TEST] Testing settings access...");
            
            try {
                // Test basic settings access
                console.log("[Arena Settings Panel TEST] app.ui.settings exists:", !!app.ui.settings);
                console.log("[Arena Settings Panel TEST] app.ui.settings.addSetting exists:", !!app.ui.settings.addSetting);
                
                // Add a simple test setting
                app.ui.settings.addSetting({
                    id: "arena.test_setting",
                    name: "Test Setting",
                    type: "boolean",
                    defaultValue: false,
                    section: "arena",
                    tooltip: "Test setting to verify Settings Panel works",
                    onChange: async (value) => {
                        console.log(`[Arena Settings Panel TEST] Test setting changed: ${value}`);
                    }
                });
                
                console.log("[Arena Settings Panel TEST] Test setting added successfully");
                
            } catch (error) {
                console.error("[Arena Settings Panel TEST] Error:", error);
            }
            
        }, 1000);
    }
});

console.log("[Arena Settings Panel TEST] Extension registered");
