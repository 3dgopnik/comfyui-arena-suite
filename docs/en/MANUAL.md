# Arena AutoCache Manual

## Overview

Arena AutoCache is a comprehensive caching system for ComfyUI that automatically manages model storage, providing intelligent caching, real-time monitoring, and smart filtering capabilities.

## Quick Start

1. **Setup**: Configure cache directory and limits using `ArenaAutoCache Config`
2. **Monitor**: Use `ArenaAutoCache Copy Status` to watch copy operations
3. **Analyze**: Use `ArenaAutoCache Analyze` to see what models are needed
4. **Execute**: Use `ArenaAutoCache Ops` to perform cache operations

## Node Reference

### 🅰️ ArenaAutoCache Config

**Purpose**: Configure cache settings and filters

**Inputs**:
- `cache_root` (string): Cache directory path
- `max_size_gb` (float): Maximum cache size in GB
- `min_size_gb` (float): Minimum model size to cache (default: 1.0)
- `skip_hardcoded_paths` (boolean): Skip models with fixed paths (default: true)

**Outputs**:
- `config_json` (string): Configuration summary

**Example**:
```json
{
  "cache_root": "F:\\ComfyUIModelCache",
  "max_size_gb": 512.0,
  "min_size_gb": 1.0,
  "skip_hardcoded_paths": true
}
```

**Use Cases**:
- Initial setup
- Changing cache limits
- Enabling/disabling filters

---

### 🅰️ ArenaAutoCache Copy Status

**Purpose**: Real-time monitoring of copy operations

**Inputs**: None (reads global status)

**Outputs**:
- `status_json` (string): Current copy status
- `show_any` (string): Human-readable status

**Status Information**:
- Current copy progress
- Copy speed (MB/s)
- Estimated time remaining
- Active filter settings
- Queue status

**Example Output**:
```json
{
  "active": true,
  "current_file": "model.safetensors",
  "progress_percent": 45.2,
  "speed_mbps": 125.5,
  "eta_seconds": 180,
  "filters": {
    "min_size_gb": 1.0,
    "skip_hardcoded": true
  }
}
```

**Use Cases**:
- Monitoring long copy operations
- Verifying filter settings
- Debugging copy issues

---

### 🅰️ ArenaAutoCache Analyze

**Purpose**: Analyze workflow and identify models to cache

**Inputs**:
- `workflow_json` (string, optional): Workflow JSON (auto-detected if empty)
- `category` (string): Model category to analyze

**Outputs**:
- `summary_json` (string): Analysis results
- `show_any` (string): Human-readable summary

**Analysis Results**:
- Total models found
- Cached vs missing models
- Estimated total size
- Copy plan with priorities

**Example Output**:
```json
{
  "ok": true,
  "ui": {
    "headline": "Analyze plan",
    "details": [
      "Items: 3",
      "Cached/Missing: 1/2",
      "Estimated size: 12.5 GiB"
    ]
  },
  "plan": [
    {
      "category": "checkpoints",
      "name": "model1.safetensors",
      "source": "\\\\nas\\models\\model1.safetensors",
      "dest": "F:\\Cache\\model1.safetensors",
      "cached": false,
      "size": 6938042042
    }
  ]
}
```

**Use Cases**:
- Planning cache operations
- Understanding workflow requirements
- Size estimation

---

### 🅰️ ArenaAutoCache Ops

**Purpose**: Execute cache operations (audit, warmup, trim)

**Inputs**:
- `mode` (string): Operation mode
  - `audit_only`: Check cache status
  - `warmup_only`: Copy missing models
  - `audit_then_warmup`: Full operation
  - `trim_only`: Remove old models
- `category` (string): Model category
- `workflow_json` (string, optional): Workflow JSON

**Outputs**:
- `summary_json` (string): Operation results
- `show_any` (string): Human-readable summary

**Operation Modes**:

1. **Audit Only**: Check which models are cached
2. **Warmup Only**: Copy missing models to cache
3. **Audit Then Warmup**: Complete cache preparation
4. **Trim Only**: Remove old models to free space

**Example Output**:
```json
{
  "ok": true,
  "ui": {
    "headline": "Arena Ops report",
    "details": [
      "Mode: audit_then_warmup",
      "Category: checkpoints",
      "Audit cached/missing: 2/1",
      "Warmup warmed: 1/1"
    ]
  },
  "stats": {
    "items": 3,
    "total_gb": 12.5,
    "max_size_gb": 512
  }
}
```

**Use Cases**:
- Automated cache management
- Manual cache operations
- Cache maintenance

---

### 🅰️ ArenaAutoCache Stats

**Purpose**: Display cache statistics and health

**Inputs**:
- `category` (string): Model category

**Outputs**:
- `stats_json` (string): Statistics data
- `show_any` (string): Human-readable stats

**Statistics Include**:
- Total cached models
- Cache size and usage
- Hit/miss ratios
- Last operation details

**Use Cases**:
- Cache health monitoring
- Performance analysis
- Troubleshooting

---

### 🅰️ ArenaAutoCache Trim

**Purpose**: Remove old models to free cache space

**Inputs**:
- `category` (string): Model category
- `target_size_gb` (float): Target cache size

**Outputs**:
- `trim_json` (string): Trim results
- `show_any` (string): Human-readable summary

**Use Cases**:
- Freeing cache space
- Cache maintenance
- Storage optimization

---

### 🅰️ ArenaAutoCache Warmup

**Purpose**: Pre-copy models to cache

**Inputs**:
- `category` (string): Model category
- `workflow_json` (string, optional): Workflow JSON

**Outputs**:
- `warmup_json` (string): Warmup results
- `show_any` (string): Human-readable summary

**Use Cases**:
- Preparing models for use
- Batch copying
- Cache preloading

---

### 🅰️ ArenaAutoCache Audit

**Purpose**: Audit cache contents and status

**Inputs**:
- `category` (string): Model category
- `workflow_json` (string, optional): Workflow JSON

**Outputs**:
- `audit_json` (string): Audit results
- `summary_json` (string): Summary data
- `show_any` (string): Human-readable summary

**Use Cases**:
- Cache verification
- Status checking
- Debugging

---

### 🅰️ ArenaAutoCache Refresh Workflow

**Purpose**: Force refresh active workflow

**Inputs**: None

**Outputs**:
- `workflow_json` (string): Updated workflow JSON
- `show_any` (string): Refresh status

**Functions**:
- Clears internal workflow cache
- Resets allowed models list
- Forces loading of current workflow
- Shows refresh result

**Use Cases**:
- Fixing stale data issues
- Force refresh after workflow changes
- Diagnosing workflow detection problems

---

## Common Workflows

### 1. Initial Setup

```
ArenaAutoCache Config → ArenaAutoCache Stats
```

1. Configure cache directory and limits
2. Check initial cache status

### 2. Workflow Analysis

```
ArenaAutoCache Analyze → ArenaAutoCache Copy Status
```

1. Analyze current workflow
2. Monitor copy progress

### 3. Cache Preparation

```
ArenaAutoCache Ops (audit_then_warmup)
```

1. Check cache status
2. Copy missing models
3. View results

### 4. Cache Maintenance

```
ArenaAutoCache Stats → ArenaAutoCache Trim
```

1. Check cache usage
2. Trim if needed

### 5. Fixing Workflow Issues

```
ArenaAutoCache Refresh Workflow → ArenaAutoCache Analyze
```

1. Force refresh workflow
2. Analyze updated workflow

## Environment Variables

- `ARENA_CACHE_ENABLE`: Enable/disable caching (default: 1)
- `ARENA_CACHE_ROOT`: Cache directory path
- `ARENA_CACHE_MAX_SIZE_GB`: Maximum cache size
- `ARENA_CACHE_MIN_SIZE_GB`: Minimum model size to cache
- `ARENA_CACHE_SKIP_HARDCODED`: Skip hardcoded path models
- `ARENA_CACHE_VERBOSE`: Enable verbose logging

## Tips and Best Practices

1. **Use Copy Status**: Always monitor copy operations for long-running tasks
2. **Configure Filters**: Set appropriate size and path filters for your setup
3. **Regular Maintenance**: Use Trim to keep cache size manageable
4. **Workflow Analysis**: Analyze workflows before running to understand requirements
5. **Environment Variables**: Use environment variables for consistent configuration

## Troubleshooting

### Common Issues

1. **Copy Status Shows No Progress**: Check if models are being filtered out
2. **Cache Not Working**: Verify `ARENA_CACHE_ENABLE=1`
3. **Slow Copy Speed**: Check network/storage performance
4. **Models Not Found**: Verify source paths are accessible
5. **Nodes Show Stale Information**: Use `ArenaAutoCache Refresh Workflow`
6. **New Workflow Not Detected**: Run Refresh Workflow before Analyze

### Debug Steps

1. Check environment variables
2. Verify cache directory permissions
3. Use Copy Status to monitor operations
4. Check ComfyUI logs for errors

## Advanced Features

### Smart Filtering

- **Size Filter**: Automatically skip small models (< 1GB)
- **Path Filter**: Skip models with hardcoded paths
- **Configurable**: All filters can be adjusted via Config node

### Real-time Monitoring

- **Progress Tracking**: See copy progress in real-time
- **Speed Monitoring**: Track copy speed and ETA
- **Queue Status**: Monitor background copy queue

### Integration

- **Workflow Detection**: Automatically detect active workflows
- **PromptServer Integration**: Seamless ComfyUI integration
- **JSON Outputs**: Machine-readable outputs for automation
