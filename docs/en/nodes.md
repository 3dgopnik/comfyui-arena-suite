---
title: "Node Reference"
description: "Detailed documentation for all Arena nodes"
order: 3
---

# Node Reference

Complete documentation for all Arena Suite nodes.

## 🎯 Arena AutoCache Simple v0.2.1

**Category:** Arena  
**Class:** `ArenaAutoCacheSimple`  
**Display Name:** `Arena AutoCache (simple) v0.2.1`

### Description

Production-ready automatic model caching node with OnDemand mode. Automatically copies frequently used models to a local cache for faster loading.

### Inputs

| Name | Type | Description | Default |
|------|------|-------------|---------|
| `enable_caching` | BOOLEAN | Enable/disable caching | `False` |
| `cache_dir` | STRING | Cache directory path | `C:/ComfyUI/cache` |
| `cache_categories` | STRING | Comma-separated model categories | `checkpoints,loras,vae` |
| `min_size_mb` | FLOAT | Minimum file size for caching | `100.0` |
| `max_cache_gb` | FLOAT | Maximum cache size (0 = unlimited) | `0.0` |
| `cache_mode` | COMBO | Caching mode | `ondemand` |
| `auto_cleanup` | BOOLEAN | Enable automatic cleanup | `False` |
| `log_level` | COMBO | Logging level | `INFO` |

### Outputs

| Name | Type | Description |
|------|------|-------------|
| `cache_status` | STRING | Current cache status |
| `models_cached` | INT | Number of cached models |
| `cache_size_gb` | FLOAT | Current cache size |

### Configuration Options

#### Cache Modes

- **`ondemand`** - Cache models when first accessed
- **`eager`** - Pre-cache all models at startup
- **`disabled`** - Disable caching completely

#### Model Categories

Supported categories:
- `checkpoints` - Main model files
- `loras` - LoRA models
- `vae` - VAE models
- `clip` - CLIP models
- `controlnet` - ControlNet models
- `upscale_models` - Upscaling models
- `embeddings` - Text embeddings
- `hypernetworks` - Hypernetwork models

#### Logging Levels

- **`ERROR`** - Only error messages
- **`WARNING`** - Warnings and errors
- **`INFO`** - General information (recommended)
- **`DEBUG`** - Detailed debugging information

### Usage Examples

#### Basic Caching

```python
# Enable caching for main models
enable_caching = True
cache_categories = "checkpoints,loras"
cache_mode = "ondemand"
```

#### Advanced Configuration

```python
# Large cache with cleanup
enable_caching = True
cache_categories = "checkpoints,loras,vae,controlnet"
max_cache_gb = 100.0
auto_cleanup = True
min_size_mb = 500.0  # Only cache large files
```

#### Debug Mode

```python
# Enable detailed logging
log_level = "DEBUG"
enable_caching = True
```

### Performance Tips

1. **Use SSD storage** for cache directory
2. **Set reasonable size limits** to prevent disk space issues
3. **Filter by file size** to cache only large models
4. **Monitor cache usage** regularly

### Troubleshooting

#### Common Issues

1. **Cache not working:**
   - Check `enable_caching=True`
   - Verify cache directory permissions
   - Ensure sufficient disk space

2. **Slow performance:**
   - Use SSD for cache
   - Check disk I/O performance
   - Monitor cache directory size

3. **Models not cached:**
   - Verify model categories are correct
   - Check minimum file size setting
   - Review log messages

## 🔧 Legacy Nodes

### Arena Make Tiles Segments

**Category:** Arena  
**Class:** `ArenaMakeTilesSegments`  
**Display Name:** `Arena Make Tiles Segments`

Legacy compatibility node for tile-based segmentation.

## 📊 Web Extensions

### Arena AutoCache Extension

**File:** `web/extensions/arena_autocache.js`

JavaScript extension providing:
- Real-time cache status
- Visual progress indicators
- Cache management UI

### Arena Workflow Analyzer

**File:** `web/extensions/arena_workflow_analyzer.js`

JavaScript extension for:
- Workflow analysis
- Model extraction
- Precaching integration

## 🔗 Integration

### ComfyUI Integration

Arena nodes integrate seamlessly with ComfyUI:
- Automatic node discovery
- Standard ComfyUI API compliance
- Web extension support

### Workflow Integration

Nodes work with standard ComfyUI workflows:
- No special workflow requirements
- Compatible with all ComfyUI nodes
- Supports batch processing

## 📚 Additional Resources

- [Configuration Guide](config.md) - Detailed configuration options
- [User Manual](manual.md) - Complete usage guide
- [Troubleshooting](troubleshooting.md) - Problem solving
- [Workflow Analyzer](../ARENA_WORKFLOW_ANALYZER.md) - JavaScript extension docs

---

**For more detailed information, see the complete [User Manual](manual.md).**



