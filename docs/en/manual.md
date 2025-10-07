---
title: "User Manual"
description: "Complete user guide for ComfyUI Arena Suite"
order: 5
---

# User Manual

Complete guide to using ComfyUI Arena Suite effectively.

## 📖 Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Advanced Features](#advanced-features)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

## 🎯 Introduction

ComfyUI Arena Suite is a modern custom node collection for ComfyUI that provides:

- **Automatic Model Caching** - Speed up your workflows with intelligent caching
- **Workflow Analysis** - JavaScript extensions for workflow optimization
- **Modern Architecture** - Clean, maintainable codebase
- **Production Ready** - Robust error handling and logging

### Key Benefits

- **Faster Workflows** - Cached models load significantly faster
- **Smart Caching** - Only cache models you actually use
- **Easy Setup** - Simple installation and configuration
- **Flexible Configuration** - Extensive customization options

## 🚀 Installation

Follow the instructions from [Quick Start Guide](quickstart.md) for initial setup.

### System Requirements

- **ComfyUI** installed and working
- **Python 3.8+**
- **Sufficient disk space** for cache (recommend 50GB+)
- **Fast storage** (SSD recommended for cache)

### Installation Steps

1. **Clone repository**
2. **Install dependencies**
3. **Copy files to ComfyUI**
4. **Restart ComfyUI**
5. **Verify installation**

## 🎮 Basic Usage

### Adding Arena AutoCache Node

1. Open ComfyUI
2. Find **Arena → Arena AutoCache (simple) v0.2.1** in node menu
3. Drag node to canvas
4. Configure basic settings

### Basic Configuration

```python
# Minimal configuration
enable_caching = True
cache_dir = "C:/ComfyUI/cache"
cache_categories = "checkpoints,loras"
```

### Running Your First Workflow

1. Create a workflow with model nodes
2. Add Arena AutoCache node
3. Set `enable_caching=True`
4. Run workflow
5. Check cache directory for copied models

## 🔧 Advanced Features

### Workflow Analyzer

The JavaScript extension automatically analyzes your workflow and precaches models:

1. **Automatic Detection** - Finds models in current workflow
2. **Precaching** - Copies models before they're needed
3. **Smart Filtering** - Only caches relevant models

### Multiple Cache Modes

#### OnDemand Mode (Recommended)

```python
cache_mode = "ondemand"
```

- Cache models when first accessed
- Optimal disk usage
- Best for most users

#### Eager Mode

```python
cache_mode = "eager"
```

- Cache all models at startup
- Maximum performance
- Requires more disk space

#### Disabled Mode

```python
cache_mode = "disabled"
```

- No caching
- Use for debugging
- Original file paths

### Advanced Configuration

#### Size-Based Filtering

```python
# Cache only large models (>1GB)
min_size_mb = 1000.0
cache_categories = "checkpoints,loras"
```

#### Cache Size Management

```python
# Limit cache to 100GB
max_cache_gb = 100.0
auto_cleanup = True
```

#### Detailed Logging

```python
# Enable debug logging
log_level = "DEBUG"
```

## ⚙️ Configuration

### Environment Variables

Create `.env` file in ComfyUI directory:

```env
# Basic settings
ARENA_CACHE_DIR=C:/ComfyUI/cache
ARENA_LOG_LEVEL=INFO
ARENA_AUTO_CACHE_ENABLED=true

# Advanced settings
ARENA_CACHE_MIN_SIZE_MB=100
ARENA_CACHE_MAX_GB=50
ARENA_CACHE_MODE=ondemand
ARENA_CACHE_CATEGORIES=checkpoints,loras,vae,clip
```

### Node Parameters

All settings can be configured through the node interface:

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `enable_caching` | BOOLEAN | Enable caching | `False` |
| `cache_dir` | STRING | Cache directory | `C:/ComfyUI/cache` |
| `cache_categories` | STRING | Model categories | `checkpoints,loras,vae` |
| `min_size_mb` | FLOAT | Min file size | `100.0` |
| `max_cache_gb` | FLOAT | Max cache size | `0.0` |
| `cache_mode` | COMBO | Cache mode | `ondemand` |
| `auto_cleanup` | BOOLEAN | Auto cleanup | `False` |
| `log_level` | COMBO | Log level | `INFO` |

## 🔍 Troubleshooting

### Common Issues

#### Node Not Appearing

**Problem:** Arena AutoCache node not visible in menu

**Solutions:**
1. Check installation paths
2. Restart ComfyUI completely
3. Verify files in `custom_nodes/ComfyUI-Arena/`
4. Check console for errors

#### Caching Not Working

**Problem:** Models not being cached

**Solutions:**
1. Ensure `enable_caching=True`
2. Check cache directory permissions
3. Verify available disk space
4. Review log messages

#### Performance Issues

**Problem:** Slow workflow execution

**Solutions:**
1. Use SSD for cache directory
2. Check disk I/O performance
3. Monitor cache directory size
4. Configure size filtering

### Debug Mode

Enable debug logging for detailed diagnostics:

```python
log_level = "DEBUG"
```

Check ComfyUI console for detailed messages.

### Log Files

Monitor log files for issues:

**Windows:**
```
C:\Users\username\AppData\Roaming\ComfyUI\logs\comfyui.log
```

**Linux/macOS:**
```
~/.local/share/ComfyUI/logs/comfyui.log
```

## 🏆 Best Practices

### Performance Optimization

1. **Use SSD Storage** - Fast drives for cache directory
2. **Size Filtering** - Cache only large models
3. **Cache Limits** - Set reasonable size limits
4. **Regular Cleanup** - Enable auto cleanup

### Storage Management

1. **Monitor Usage** - Check cache directory size regularly
2. **Plan Space** - Allocate sufficient disk space
3. **Backup Strategy** - Consider cache backup needs
4. **Cleanup Schedule** - Regular cache maintenance

### Workflow Design

1. **Single Cache Node** - Use one Arena AutoCache node per workflow
2. **Early Placement** - Place cache node early in workflow
3. **Category Selection** - Choose relevant model categories
4. **Testing** - Test caching with small workflows first

### Configuration Management

1. **Environment Variables** - Use .env for global settings
2. **Node Parameters** - Override settings per workflow
3. **Documentation** - Document your configuration
4. **Version Control** - Track configuration changes

## 📚 Additional Resources

- [Quick Start Guide](quickstart.md) - Initial setup
- [Node Reference](nodes.md) - Detailed node documentation
- [Configuration Guide](config.md) - Advanced configuration
- [Troubleshooting Guide](troubleshooting.md) - Problem solving
- [Workflow Analyzer](../ARENA_WORKFLOW_ANALYZER.md) - JavaScript extension

## 🆘 Getting Help

### Documentation

- Check this manual first
- Review [Configuration Guide](config.md)
- See [Troubleshooting Guide](troubleshooting.md)

### Community Support

- **GitHub Issues:** [Report bugs and request features](https://github.com/3dgopnik/comfyui-arena-suite/issues)
- **Discussions:** [Community discussions](https://github.com/3dgopnik/comfyui-arena-suite/discussions)

### Reporting Issues

When reporting issues, include:

- **ComfyUI version**
- **Python version**
- **Error messages** (if any)
- **Steps to reproduce**
- **Configuration details**
- **Log files** (if relevant)

---

**Happy caching! Arena Suite makes your ComfyUI workflows faster and more efficient.**



