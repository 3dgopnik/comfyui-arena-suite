---
title: "Configuration"
description: "Detailed configuration guide for ComfyUI Arena Suite"
order: 4
---

# Configuration

Complete configuration guide for all Arena Suite settings and options.

## ⚙️ Basic Settings

### Environment Variables

Create a `.env` file in your ComfyUI directory for global settings:

```env
# Basic caching settings
ARENA_CACHE_DIR=C:/ComfyUI/cache
ARENA_LOG_LEVEL=INFO
ARENA_AUTO_CACHE_ENABLED=true

# Cache configuration
ARENA_CACHE_MIN_SIZE_MB=100
ARENA_CACHE_MAX_GB=50
ARENA_CACHE_MODE=ondemand

# Autopatch settings
ARENA_AUTOCACHE_AUTOPATCH=true
```

### Node Settings

All node parameters can be configured through the interface or environment variables.

#### 🆕 Automatic Parameter Loading from .env File

**New Feature:** The node automatically loads parameters from the `user/arena_autocache.env` file and pre-fills the interface with them.

**How it works:**
1. When opening the node in ComfyUI, the system checks for the existence of the `.env` file
2. If the file exists, parameters are loaded and displayed in the node fields
3. Priority: node parameters > .env file > default values

**Example .env file:**
```env
# Arena AutoCache Environment Settings
ARENA_CACHE_ROOT=C:/ComfyUI/cache
ARENA_CACHE_MIN_SIZE_MB=50.0
ARENA_CACHE_MAX_GB=100.0
ARENA_CACHE_VERBOSE=true
ARENA_CACHE_MODE=ondemand
ARENA_AUTOCACHE_AUTOPATCH=true
ARENA_AUTO_CACHE_ENABLED=true
ARENA_CACHE_CATEGORIES=checkpoints,loras,vae,clip
```

**Benefits:**
- ✅ Quick setup - no need to enter parameters every time
- ✅ Consistency - same settings for all workflows
- ✅ Convenience - settings persist between sessions
- ✅ Compatibility - works with existing .env files

## 🎯 Caching Parameters

### enable_caching

**Description:** Main caching toggle

**Type:** BOOLEAN  
**Default:** `False`  
**Environment Variable:** `ARENA_AUTO_CACHE_ENABLED`

```python
# Enable caching
enable_caching = True

# Disable caching
enable_caching = False
```

### cache_dir

**Description:** Directory for cached models

**Type:** STRING  
**Default:** `C:/ComfyUI/cache`  
**Environment Variable:** `ARENA_CACHE_DIR`

```python
# Windows
cache_dir = "C:/ComfyUI/cache"

# Linux/macOS
cache_dir = "/home/user/.cache/comfyui/arena"

# Network storage
cache_dir = "//nas/models/cache"
```

### cache_categories

**Description:** Model categories to cache

**Type:** STRING  
**Default:** `checkpoints,loras,vae`  
**Environment Variable:** `ARENA_CACHE_CATEGORIES`

```python
# Main categories
cache_categories = "checkpoints,loras,vae"

# All categories
cache_categories = "checkpoints,loras,vae,clip,controlnet,upscale_models,embeddings,hypernetworks,gguf_models,unet_models,diffusion_models"

# Large models only
cache_categories = "checkpoints,loras"
```

### min_size_mb

**Description:** Minimum file size for caching

**Type:** FLOAT  
**Default:** `100.0`  
**Environment Variable:** `ARENA_CACHE_MIN_SIZE_MB`

```python
# Cache only large files (>500MB)
min_size_mb = 500.0

# Cache all files
min_size_mb = 0.0

# Cache files larger than 50MB
min_size_mb = 50.0
```

### max_cache_gb

**Description:** Maximum cache size

**Type:** FLOAT  
**Default:** `0.0` (unlimited)  
**Environment Variable:** `ARENA_CACHE_MAX_GB`

```python
# No limit
max_cache_gb = 0.0

# 50GB limit
max_cache_gb = 50.0

# 100GB limit
max_cache_gb = 100.0
```

## 🔄 Cache Modes

### cache_mode

**Description:** Caching operation mode

**Type:** COMBO  
**Default:** `ondemand`  
**Environment Variable:** `ARENA_CACHE_MODE`

#### OnDemand (default)

```python
cache_mode = "ondemand"
```

**Characteristics:**
- Cache models on first access
- Saves disk space
- Recommended for most use cases

#### Eager

```python
cache_mode = "eager"
```

**Characteristics:**
- Bulk copy all models at startup
- All models ready for use
- Requires more disk space

#### Disabled

```python
cache_mode = "disabled"
```

**Characteristics:**
- Complete caching disable
- Use original paths
- For debugging and testing

## 🧹 Auto Cleanup

### auto_cleanup

**Description:** Automatic cleanup of old files

**Type:** BOOLEAN  
**Default:** `False`

```python
# Enable auto cleanup
auto_cleanup = True

# Disable auto cleanup
auto_cleanup = False
```

### Cleanup Strategies

1. **LRU (Least Recently Used)** - Remove oldest files
2. **By Size** - Remove largest files
3. **By Date** - Remove files older than specified age

## 📊 Logging

### log_level

**Description:** Logging detail level

**Type:** COMBO  
**Default:** `INFO`  
**Environment Variable:** `ARENA_LOG_LEVEL`

```python
# Minimal logging
log_level = "ERROR"

# Standard logging
log_level = "INFO"

# Detailed logging
log_level = "DEBUG"
```

### Log Levels

| Level | Description | Usage |
|-------|-------------|-------|
| `ERROR` | Errors only | Production |
| `WARNING` | Warnings and errors | Debugging |
| `INFO` | Main operations | Recommended |
| `DEBUG` | Detailed diagnostics | Development |

## 🔧 Advanced Settings

### Autopatch

**Environment Variable:** `ARENA_AUTOCACHE_AUTOPATCH`

```env
# Enable autopatch on load
ARENA_AUTOCACHE_AUTOPATCH=true

# Disable autopatch
ARENA_AUTOCACHE_AUTOPATCH=false
```

### Security

#### Path Validation

```python
# Safe paths
cache_dir = "C:/ComfyUI/cache"           # ✅ Safe
cache_dir = "/home/user/.cache/arena"   # ✅ Safe

# Unsafe paths
cache_dir = "C:/"                        # ❌ Disk root
cache_dir = "/"                          # ❌ System root
cache_dir = "//server/share"             # ❌ Too shallow UNC path
```

#### Setting Validation

All settings are validated for:
- **Type checking** - Correct data types
- **Range validation** - Values within acceptable ranges
- **Path safety** - Safe file system paths

## 📁 Model Paths Configuration

### extra_model_paths.yaml

Arena AutoCache supports additional model paths via `extra_model_paths.yaml` file.

**File location:**
- ComfyUI Desktop: `C:\Users\<username>\AppData\Local\Programs\@comfyorgcomfyui-electron\resources\ComfyUI\extra_model_paths.yaml`
- Local installation: `C:\ComfyUI\extra_model_paths.yaml`

**Setup via Arena:**

1. **Automatic setup (recommended):**
   - Use Settings UI → Arena → fill "NAS Root Path" and "Cache Directory"
   - Click "Save Settings" - Arena will create `.env` file with settings
   - Enable "Auto-scan NAS" for automatic model discovery

2. **Manual setup via YAML:**
   - Copy your `extra_model_paths.yaml` to `<ComfyUI-Arena>/config/extra_model_paths.yaml`
   - Arena will use this file as template
   - "Restore YAML" button in Settings will restore file in ComfyUI from template

**Example extra_model_paths.yaml:**

```yaml
# Path to models on NAS
models:
  checkpoints: Y:\SDModels\CheckPoints\
  loras: Y:\SDModels\Lora\
  vae: Y:\SDModels\VAE\
  upscale_models: Y:\SDModels\SDXL\SUPIR\
  clip: Y:\SDModels\CLIP\
  controlnet: Y:\SDModels\ControlNet\
```

**Important:**
- Arena automatically scans subfolders (up to 3 levels by default)
- You can configure scan depth via "NAS Scan Max Depth" in Settings
- Models are detected by size (default >= 1MB), independent of file extensions

## 📁 Configuration Structure

### .env File

```env
# Basic settings
ARENA_CACHE_DIR=C:/ComfyUI/cache
ARENA_LOG_LEVEL=INFO
ARENA_AUTO_CACHE_ENABLED=true

# Cache settings
ARENA_CACHE_MIN_SIZE_MB=100
ARENA_CACHE_MAX_GB=50
ARENA_CACHE_MODE=ondemand

# Autopatch
ARENA_AUTOCACHE_AUTOPATCH=true

# Model categories
ARENA_CACHE_CATEGORIES=checkpoints,loras,vae,clip,controlnet
```

### Setting Priority

1. **Node parameters** - Highest priority
2. **Environment variables** - Medium priority
3. **Default values** - Lowest priority

## 🚀 Performance Optimization

### Configuration Recommendations

1. **SSD for cache** - Use fast drives
2. **Sufficient space** - Keep 20-30% free space
3. **Size filtering** - Configure `min_size_mb`
4. **Cache limits** - Set reasonable `max_cache_gb`

### Monitoring

```python
# Enable detailed logging for monitoring
log_level = "DEBUG"

# Configure auto cleanup for size management
auto_cleanup = True
max_cache_gb = 50.0
```

## 🔍 Diagnostics

### Configuration Check

```python
# Check all settings
print(f"Cache directory: {cache_dir}")
print(f"Cache categories: {cache_categories}")
print(f"Min size: {min_size_mb} MB")
print(f"Max cache: {max_cache_gb} GB")
print(f"Cache mode: {cache_mode}")
```

### Log Monitoring

```bash
# Windows
tail -f "C:\Users\username\AppData\Roaming\ComfyUI\logs\comfyui.log"

# Linux/macOS
tail -f ~/.local/share/ComfyUI/logs/comfyui.log
```

## 📚 Additional Resources

- [Quick Start Guide](quickstart.md) - Initial setup
- [Node Reference](nodes.md) - Node descriptions
- [User Manual](manual.md) - Complete guide
- [Troubleshooting](troubleshooting.md) - Problem solving

---

**Proper configuration is the key to efficient Arena AutoCache operation!**



