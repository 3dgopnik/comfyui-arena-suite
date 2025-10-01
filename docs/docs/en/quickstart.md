---
title: "Quick Start"
description: "Quick setup guide for ComfyUI Arena Suite"
order: 2
---

# Quick Start

This guide will help you quickly set up and start using ComfyUI Arena Suite.

## 📋 Prerequisites

- **ComfyUI** installed and running
- **Python 3.8+** 
- **Windows/Linux/macOS**

## 🚀 Installation

### Step 1: Clone the repository

```bash
git clone https://github.com/3dgopnik/comfyui-arena-suite.git
cd comfyui-arena-suite
```

### Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Copy to ComfyUI

#### Windows
```cmd
xcopy /E /I custom_nodes\ComfyUI_Arena "C:\ComfyUI\custom_nodes\ComfyUI_Arena"
xcopy /E /I web "C:\ComfyUI\web"
```

#### Linux/macOS
```bash
cp -r custom_nodes/ComfyUI_Arena /path/to/ComfyUI/custom_nodes/
cp -r web /path/to/ComfyUI/
```

### Step 4: Restart ComfyUI

Completely restart ComfyUI to load the new nodes.

## 🎯 First Usage

### 1. Adding Arena AutoCache Node

1. Open ComfyUI
2. Find in node menu: **Arena → Arena AutoCache (simple) v4.5.0**
3. Drag the node to canvas

### 2. Configuring Caching

1. **Enable caching** - set `enable_caching=True`
2. **Set cache directory** - specify path for cached models
3. **Choose model categories** - which types of models to cache
4. **Set size limit** - maximum cache size in GB

### 3. Running Workflow

1. Create or load a workflow with models
2. Run the workflow
3. On first access, models will be copied to cache
4. Subsequent runs will use cached models

## ⚙️ Basic Configuration

### Environment Variables

Create a `.env` file in ComfyUI directory:

```env
# Basic settings
ARENA_CACHE_DIR=C:/ComfyUI/cache
ARENA_LOG_LEVEL=INFO

# Cache settings
ARENA_CACHE_MIN_SIZE_MB=100
ARENA_CACHE_MAX_GB=50
ARENA_CACHE_MODE=ondemand
```

### Node Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `enable_caching` | Enable caching | `False` |
| `cache_dir` | Cache directory | `C:/ComfyUI/cache` |
| `cache_categories` | Model categories | `checkpoints,loras,vae` |
| `min_size_mb` | Minimum file size | `100` |
| `max_cache_gb` | Maximum cache size | `0` (unlimited) |

## 🔍 Verification

### 1. Installation Check

After restarting ComfyUI, verify:

- Node "Arena AutoCache (simple) v4.5.0" is available in menu
- No errors in ComfyUI console
- Node displays correctly on canvas

### 2. Testing Caching

1. Add Arena AutoCache node to workflow
2. Set `enable_caching=True`
3. Run workflow with a model
4. Check that model was copied to cache directory

### 3. Monitoring

- **ComfyUI Logs** - check console for caching messages
- **Cache Size** - monitor disk space usage
- **Performance** - measure model loading times

## 🚨 Common Issues

### Node Not Appearing

**Problem:** Node not visible in ComfyUI menu

**Solution:**
1. Check correct installation paths
2. Ensure files copied to `custom_nodes/ComfyUI_Arena/`
3. Completely restart ComfyUI
4. Check console for import errors

### Caching Not Working

**Problem:** Models not being cached

**Solution:**
1. Ensure `enable_caching=True`
2. Check cache directory permissions
3. Verify available disk space
4. Review logs for errors

### Slow Performance

**Problem:** Workflow running slowly

**Solution:**
1. Use SSD for cache
2. Configure file size filtering
3. Check disk performance
4. Monitor cache directory size

## 📚 Next Steps

After successful setup, explore:

- [Node Reference](nodes.md) - Detailed node documentation
- [Configuration](config.md) - Advanced settings
- [User Manual](manual.md) - Complete guide
- [Troubleshooting](troubleshooting.md) - Problem solving

## 🆘 Getting Help

If you encounter issues:

1. **Check Documentation** - Most questions are already covered
2. **GitHub Issues** - [Report bugs](https://github.com/3dgopnik/comfyui-arena-suite/issues)
3. **Discussions** - [Ask community](https://github.com/3dgopnik/comfyui-arena-suite/discussions)

---

**Ready! Now you can use ComfyUI Arena Suite to speed up your workflows.**