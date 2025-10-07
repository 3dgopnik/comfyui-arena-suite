---
title: "CLI Tools"
description: "Command line tools for ComfyUI Arena Suite"
order: 7
---

# CLI Tools

Command line utilities for managing ComfyUI Arena Suite.

## 🛠️ Available Scripts

### Installation Scripts

#### Windows Batch Scripts

##### arena_bootstrap_cache_v2.bat
**Purpose:** Complete installation and setup script

```batch
# Run the bootstrap script
arena_bootstrap_cache_v2.bat
```

**Features:**
- Downloads and installs Arena Suite
- Sets up cache directory
- Configures environment variables
- Verifies installation

##### arena_set_cache.bat
**Purpose:** Configure cache settings

```batch
# Set cache directory
arena_set_cache.bat "D:\ComfyUI\cache"

# Set cache with size limit
arena_set_cache.bat "D:\ComfyUI\cache" 50
```

#### PowerShell Scripts

##### arena_bootstrap_cache_v2.ps1
**Purpose:** PowerShell version of bootstrap script

```powershell
# Run with execution policy
powershell -ExecutionPolicy Bypass -File arena_bootstrap_cache_v2.ps1
```

##### sync_web_extension.ps1
**Purpose:** Synchronize web extensions

```powershell
# Sync JavaScript files
powershell -ExecutionPolicy Bypass -File sync_web_extension.ps1
```

### Utility Scripts

#### arena_fast_start.bat
**Purpose:** Quick ComfyUI startup with Arena

```batch
# Start ComfyUI with Arena pre-configured
arena_fast_start.bat
```

#### arena_optimize_manager.bat
**Purpose:** Cache optimization and cleanup

```batch
# Optimize cache directory
arena_optimize_manager.bat

# Clean old cache files
arena_optimize_manager.bat --cleanup
```

#### check_dev_setup.bat/ps1
**Purpose:** Verify development environment

```batch
# Check development setup
check_dev_setup.bat
```

```powershell
# PowerShell version
check_dev_setup.ps1
```

## 📋 Script Usage

### Installation Workflow

1. **Download Repository**
   ```bash
   git clone https://github.com/3dgopnik/comfyui-arena-suite.git
   cd comfyui-arena-suite
   ```

2. **Run Bootstrap Script**
   ```batch
   # Windows
   arena_bootstrap_cache_v2.bat
   
   # PowerShell
   powershell -ExecutionPolicy Bypass -File arena_bootstrap_cache_v2.ps1
   ```

3. **Verify Installation**
   ```batch
   check_dev_setup.bat
   ```

### Cache Management

#### Setting Up Cache

```batch
# Basic cache setup
arena_set_cache.bat "C:\ComfyUI\cache"

# Advanced setup with size limit
arena_set_cache.bat "D:\ComfyUI\cache" 100
```

#### Cache Optimization

```batch
# Optimize existing cache
arena_optimize_manager.bat

# Clean old files
arena_optimize_manager.bat --cleanup --older-than 30

# Analyze cache usage
arena_optimize_manager.bat --analyze
```

### Web Extension Management

#### Synchronizing Extensions

```powershell
# Sync JavaScript files to ComfyUI
sync_web_extension.ps1

# Force sync (overwrite existing)
sync_web_extension.ps1 --force
```

#### Manual Extension Setup

```batch
# Copy extensions manually
xcopy /E /I web\extensions\arena "C:\ComfyUI\web\extensions\arena\"
```

## 🔧 Configuration Scripts

### Environment Setup

#### Creating .env File

```batch
# Create .env file with default settings
echo ARENA_CACHE_DIR=C:\ComfyUI\cache > .env
echo ARENA_LOG_LEVEL=INFO >> .env
echo ARENA_AUTO_CACHE_ENABLED=true >> .env
```

#### Advanced Configuration

```batch
# Create advanced .env configuration
(
echo ARENA_CACHE_DIR=D:\ComfyUI\cache
echo ARENA_LOG_LEVEL=DEBUG
echo ARENA_AUTO_CACHE_ENABLED=true
echo ARENA_CACHE_MIN_SIZE_MB=100
echo ARENA_CACHE_MAX_GB=50
echo ARENA_CACHE_MODE=ondemand
echo ARENA_CACHE_CATEGORIES=checkpoints,loras,vae
) > .env
```

### Path Configuration

#### Setting Environment Variables

```batch
# Set temporary environment variables
set ARENA_CACHE_DIR=C:\ComfyUI\cache
set ARENA_LOG_LEVEL=INFO

# Set permanent environment variables (requires admin)
setx ARENA_CACHE_DIR "C:\ComfyUI\cache"
setx ARENA_LOG_LEVEL "INFO"
```

## 🚀 Quick Start Scripts

### Fast Development Setup

```batch
# Complete development setup
arena_fast_start.bat --dev

# Production setup
arena_fast_start.bat --prod
```

### Testing Scripts

#### arena_test_comfyui_startup.bat
**Purpose:** Test ComfyUI startup with Arena

```batch
# Test startup
arena_test_comfyui_startup.bat

# Test with specific configuration
arena_test_comfyui_startup.bat --config test.env
```

#### test_workflow_analysis.py
**Purpose:** Test workflow analysis functionality

```python
# Run workflow analysis test
python scripts/test_workflow_analysis.py

# Test with specific workflow
python scripts/test_workflow_analysis.py --workflow test_workflow.json
```

## 📊 Monitoring Scripts

### Cache Monitoring

```batch
# Monitor cache usage
arena_optimize_manager.bat --monitor

# Generate cache report
arena_optimize_manager.bat --report > cache_report.txt
```

### Performance Testing

```batch
# Test cache performance
arena_test_comfyui_startup.bat --benchmark

# Test with different configurations
arena_test_comfyui_startup.bat --benchmark --config ssd.env
arena_test_comfyui_startup.bat --benchmark --config hdd.env
```

## 🔍 Diagnostic Scripts

### System Check

```batch
# Check system requirements
check_dev_setup.bat --system

# Check Python environment
check_dev_setup.bat --python

# Check ComfyUI installation
check_dev_setup.bat --comfyui
```

### Troubleshooting

```batch
# Diagnose common issues
check_dev_setup.bat --diagnose

# Check file permissions
check_dev_setup.bat --permissions

# Verify installation
check_dev_setup.bat --verify
```

## 📁 Script Configuration

### Script Parameters

Most scripts support common parameters:

```batch
# Help
script.bat --help

# Verbose output
script.bat --verbose

# Dry run (no changes)
script.bat --dry-run

# Configuration file
script.bat --config custom.env
```

### Environment Variables

Scripts respect these environment variables:

```batch
# ComfyUI installation path
set COMFYUI_ROOT=C:\ComfyUI

# Arena cache directory
set ARENA_CACHE_DIR=C:\ComfyUI\cache

# Log level
set ARENA_LOG_LEVEL=INFO
```

## 🛡️ Security Considerations

### Script Safety

1. **Verify Scripts** - Check script contents before running
2. **Backup Data** - Backup important data before running scripts
3. **Test First** - Test scripts in non-production environment
4. **Monitor Output** - Watch script output for errors

### Permission Requirements

Some scripts require elevated permissions:

```batch
# Run as administrator for system-wide changes
# Right-click -> Run as administrator
arena_bootstrap_cache_v2.bat
```

## 📚 Additional Resources

- [Quick Start Guide](quickstart.md) - Initial setup
- [Configuration Guide](config.md) - Advanced configuration
- [Troubleshooting Guide](troubleshooting.md) - Problem solving
- [User Manual](manual.md) - Complete guide

---

**CLI tools make Arena Suite management easy and automated!**



