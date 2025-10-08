# Arena AutoCache Settings UI

## Overview

The Arena AutoCache Settings UI provides an intuitive interface for configuring automatic model caching in ComfyUI. The settings are organized with visual indicators and user-friendly names for better user experience.

## Settings Organization

### Visual Grouping
Settings are organized using color-coded circles to group related functionality:

- **🔴 Red Circles**: Main toggle switches (Enable Auto Cache, Verbose Logging)
- **🟡 Yellow Circles**: Cache configuration settings (Mode, Directory, Sizes)
- **🟢 Green Circles**: Action buttons (Save Settings)

### Settings List

1. **Enable Auto Cache** (🔴)
   - Type: Boolean toggle
   - Purpose: Enable/disable automatic caching
   - Default: False

2. **Verbose Logging** (🔴)
   - Type: Boolean toggle
   - Purpose: Enable detailed cache logging
   - Default: False

3. **Cache Mode** (🟡)
   - Type: Dropdown
   - Options: "ondemand", "disabled"
   - Purpose: Configure caching behavior
   - Default: "ondemand"

4. **Cache Directory** (🟡)
   - Type: Text input
   - Purpose: Set cache storage location
   - Default: Empty

5. **Min File Size (MB)** (🟡)
   - Type: Number input
   - Purpose: Minimum file size for caching
   - Default: 10

6. **Max Cache Size (GB)** (🟡)
   - Type: Number input
   - Purpose: Maximum cache size limit
   - Default: 0 (unlimited)

7. **Save Settings** (🟢)
   - Type: Button
   - Purpose: Save all settings to .env file
   - Action: Creates/updates `user/arena_autocache.env`

## Technical Implementation

### ID Structure
Settings use emoji-prefixed IDs to bypass ComfyUI's alphabetical sorting:

```javascript
// Examples
"Arena.🔴 Enable Auto Cache"
"Arena.🟡 Cache Directory"
"Arena.🟢 Save Settings"
```

### User-Friendly Names
Technical IDs are mapped to human-readable labels:

```javascript
const labelMap = {
    'Arena.🔴 Enable Auto Cache': 'Enable Auto Cache',
    'Arena.🔴 Verbose Logging': 'Verbose Logging',
    'Arena.🟡 Cache Mode': 'Cache Mode',
    // ... etc
};
```

## Usage

1. Open ComfyUI Settings
2. Navigate to "Arena" section
3. Configure desired settings
4. Click "Save Settings" to apply changes
5. Settings are saved to `user/arena_autocache.env`

## Benefits

- **Intuitive Organization**: Related settings grouped together
- **Visual Clarity**: Color-coded indicators for different setting types
- **User-Friendly Names**: Clear, descriptive setting names
- **Logical Flow**: Settings ordered from main toggles → configuration → actions
- **Bypass Sorting**: Emoji prefixes ensure proper ordering regardless of ComfyUI's alphabetical sorting

## Version History

- **v4.18.0**: Initial implementation with emoji-prefixed IDs and user-friendly names
- **Previous**: Technical IDs with alphabetical sorting issues