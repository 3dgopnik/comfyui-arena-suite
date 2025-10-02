---
title: "Troubleshooting"
description: "Common issues and solutions for ComfyUI Arena Suite"
order: 6
---

# Troubleshooting

Common issues and solutions for ComfyUI Arena Suite.

## 🚨 Installation Issues

### Node Not Appearing in Menu

**Problem:** Arena AutoCache node not visible in ComfyUI menu

**Symptoms:**
- No "Arena" category in node menu
- Node not found when searching
- ComfyUI loads without errors

**Solutions:**

1. **Check Installation Path**
   ```bash
   # Verify files are in correct location
   ls "C:\ComfyUI\custom_nodes\ComfyUI-Arena\"
   ```

2. **Verify File Structure**
   ```
   ComfyUI-Arena/
   ├── __init__.py
   ├── autocache/
   │   └── arena_auto_cache_simple.py
   └── web/
       └── extensions/
           ├── arena_autocache.js
           └── arena_workflow_analyzer.js
   ```

3. **Restart ComfyUI**
   - Completely close ComfyUI
   - Wait 10 seconds
   - Restart ComfyUI
   - Check console for loading messages

4. **Check Console Output**
   ```
   [Arena Suite] Loaded Arena AutoCache Base
   [Arena Suite] Successfully loaded X Arena nodes
   ```

### Import Errors

**Problem:** Python import errors in console

**Common Errors:**
```
ImportError: No module named 'autocache'
ModuleNotFoundError: No module named 'arena_auto_cache_simple'
```

**Solutions:**

1. **Check Python Path**
   ```python
   # Verify Python can find the module
   import sys
   print(sys.path)
   ```

2. **Verify File Permissions**
   ```bash
   # Check file permissions (Linux/macOS)
   ls -la custom_nodes/ComfyUI-Arena/
   ```

3. **Reinstall Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🔧 Configuration Issues

### Caching Not Working

**Problem:** Models not being cached despite enabled settings

**Symptoms:**
- `enable_caching=True` but no cache files
- Models still loading from original location
- No cache messages in logs

**Solutions:**

1. **Verify Configuration**
   ```python
   # Check these settings
   enable_caching = True  # Must be True
   cache_dir = "C:/ComfyUI/cache"  # Valid path
   cache_categories = "checkpoints,loras"  # Valid categories
   ```

2. **Check Cache Directory**
   ```bash
   # Verify directory exists and is writable
   mkdir -p "C:/ComfyUI/cache"
   echo "test" > "C:/ComfyUI/cache/test.txt"
   ```

3. **Check Disk Space**
   ```bash
   # Ensure sufficient free space
   df -h "C:/ComfyUI/cache"
   ```

4. **Review Logs**
   ```python
   # Enable debug logging
   log_level = "DEBUG"
   ```

### Permission Errors

**Problem:** Access denied when writing to cache directory

**Solutions:**

1. **Windows Permissions**
   ```cmd
   # Grant full access to cache directory
   icacls "C:\ComfyUI\cache" /grant Users:F /T
   ```

2. **Linux/macOS Permissions**
   ```bash
   # Fix directory permissions
   chmod 755 /path/to/cache
   chown $USER:$USER /path/to/cache
   ```

3. **Run as Administrator** (Windows)
   - Right-click ComfyUI
   - Select "Run as administrator"

### Cache Directory Issues

**Problem:** Cache directory not accessible or corrupted

**Solutions:**

1. **Create New Directory**
   ```python
   # Use a different cache directory
   cache_dir = "D:/ComfyUI/cache"
   ```

2. **Clear Corrupted Cache**
   ```bash
   # Remove corrupted cache
   rm -rf "C:/ComfyUI/cache"
   mkdir "C:/ComfyUI/cache"
   ```

3. **Use Absolute Paths**
   ```python
   # Use absolute path instead of relative
   cache_dir = "C:/Users/username/ComfyUI/cache"
   ```

## ⚡ Performance Issues

### Slow Cache Operations

**Problem:** Caching operations are very slow

**Solutions:**

1. **Use SSD Storage**
   ```python
   # Move cache to SSD
   cache_dir = "D:/ComfyUI/cache"  # SSD drive
   ```

2. **Check Disk Performance**
   ```bash
   # Test disk speed (Windows)
   winsat disk -drive D
   ```

3. **Optimize Cache Settings**
   ```python
   # Cache only large files
   min_size_mb = 500.0
   cache_categories = "checkpoints"  # Only main models
   ```

### High Memory Usage

**Problem:** Arena Suite using too much memory

**Solutions:**

1. **Limit Cache Size**
   ```python
   # Set cache size limit
   max_cache_gb = 20.0
   auto_cleanup = True
   ```

2. **Filter by Size**
   ```python
   # Only cache large models
   min_size_mb = 1000.0
   ```

3. **Disable Debug Logging**
   ```python
   # Reduce logging overhead
   log_level = "INFO"
   ```

### Workflow Slowdown

**Problem:** Workflows running slower with caching enabled

**Solutions:**

1. **Check Cache Mode**
   ```python
   # Use OnDemand for better performance
   cache_mode = "ondemand"
   ```

2. **Monitor Cache Directory**
   ```bash
   # Check if cache is on slow storage
   ls -la "C:/ComfyUI/cache/"
   ```

3. **Disable Unnecessary Categories**
   ```python
   # Cache only essential models
   cache_categories = "checkpoints,loras"
   ```

## 🌐 Web Extension Issues

### JavaScript Extensions Not Loading

**Problem:** Web extensions not working

**Symptoms:**
- No cache status indicators
- Workflow analyzer not functioning
- Console errors in browser

**Solutions:**

1. **Check File Placement**
   ```bash
   # Verify JavaScript files are in correct location
   ls "C:/ComfyUI/web/extensions/arena/"
   ```

2. **Check Browser Console**
   ```
   # Look for JavaScript errors
   F12 -> Console -> Look for Arena messages
   ```

3. **Clear Browser Cache**
   - Clear ComfyUI browser cache
   - Hard refresh (Ctrl+F5)

4. **Check File Permissions**
   ```bash
   # Ensure JavaScript files are readable
   chmod 644 web/extensions/arena/*.js
   ```

### Workflow Analyzer Not Working

**Problem:** Workflow analysis not functioning

**Solutions:**

1. **Check Extension Loading**
   ```
   # Look for this message in browser console
   [Arena Workflow Analyzer] Loading...
   [Arena Workflow Analyzer] Extension loaded successfully
   ```

2. **Verify API Endpoint**
   ```python
   # Check if Python API is registered
   # Look for: [ArenaAutoCache] API endpoint registered
   ```

3. **Check Network Requests**
   ```
   # In browser DevTools -> Network
   # Look for requests to /arena/analyze_workflow
   ```

## 🔍 Debugging

### Enable Debug Logging

```python
# Enable detailed logging
log_level = "DEBUG"
```

### Check Log Files

**Windows:**
```
C:\Users\username\AppData\Roaming\ComfyUI\logs\comfyui.log
```

**Linux/macOS:**
```
~/.local/share/ComfyUI/logs/comfyui.log
```

### Common Log Messages

```
# Successful loading
[Arena Suite] Loaded Arena AutoCache Base
[Arena Suite] Successfully loaded 2 Arena nodes

# Caching operations
[ArenaAutoCache] Caching model: model.safetensors
[ArenaAutoCache] Cache hit for: model.safetensors

# Errors
[ArenaAutoCache] ERROR: Permission denied
[ArenaAutoCache] ERROR: Insufficient disk space
```

## 🆘 Getting Help

### Before Asking for Help

1. **Check Documentation**
   - Review this troubleshooting guide
   - Check [Configuration Guide](config.md)
   - See [User Manual](manual.md)

2. **Enable Debug Logging**
   ```python
   log_level = "DEBUG"
   ```

3. **Collect Information**
   - ComfyUI version
   - Python version
   - Operating system
   - Error messages
   - Log files

### Reporting Issues

When reporting issues, include:

1. **System Information**
   ```
   - OS: Windows 11 / Linux / macOS
   - Python: 3.9.7
   - ComfyUI: latest
   ```

2. **Configuration**
   ```python
   # Your node settings
   enable_caching = True
   cache_dir = "C:/ComfyUI/cache"
   cache_categories = "checkpoints,loras"
   ```

3. **Error Details**
   - Full error message
   - Steps to reproduce
   - Log file excerpts

4. **Troubleshooting Attempts**
   - What you've already tried
   - What worked/didn't work

### Community Support

- **GitHub Issues:** [Report bugs](https://github.com/3dgopnik/comfyui-arena-suite/issues)
- **Discussions:** [Ask questions](https://github.com/3dgopnik/comfyui-arena-suite/discussions)

## 📚 Additional Resources

- [Quick Start Guide](quickstart.md) - Initial setup
- [Node Reference](nodes.md) - Node documentation
- [Configuration Guide](config.md) - Advanced configuration
- [User Manual](manual.md) - Complete guide

---

**Most issues can be resolved by checking configuration, permissions, and disk space.**



