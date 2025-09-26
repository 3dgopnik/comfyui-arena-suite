#!/usr/bin/env python3
"""Test script to check imports and node registration."""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=== Testing Arena Suite Imports ===")

try:
    from __init__ import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS, WEB_DIRECTORY
    print("✓ Main __init__.py imported successfully")
    print(f"  NODE_CLASS_MAPPINGS: {len(NODE_CLASS_MAPPINGS)} nodes")
    print(f"  NODE_DISPLAY_NAME_MAPPINGS: {len(NODE_DISPLAY_NAME_MAPPINGS)} nodes")
    print(f"  WEB_DIRECTORY: {WEB_DIRECTORY}")
    
    for node_id, node_class in NODE_CLASS_MAPPINGS.items():
        print(f"  - {node_id}: {node_class}")
        
except Exception as e:
    print(f"✗ Error importing main __init__.py: {e}")

print("\n=== Testing folder_paths availability ===")
try:
    import folder_paths
    print("✓ folder_paths available")
    print(f"  folder_paths module: {folder_paths}")
except Exception as e:
    print(f"✗ folder_paths not available: {e}")

print("\n=== Testing ComfyUI environment ===")
try:
    # Check if we're in ComfyUI environment
    import comfy
    print("✓ ComfyUI environment detected")
except Exception as e:
    print(f"✗ Not in ComfyUI environment: {e}")

print("\n=== Testing individual modules ===")

# Test autocache
try:
    from custom_nodes.ComfyUI_Arena.autocache.arena_auto_cache_simple import ArenaAutoCache
    print("✓ ArenaAutoCache imported successfully")
except Exception as e:
    print(f"✗ ArenaAutoCache import failed: {e}")

# Test updater
try:
    from custom_nodes.ComfyUI_Arena.updater.arena_model_updater import ArenaModelUpdater
    print("✓ ArenaModelUpdater imported successfully")
except Exception as e:
    print(f"✗ ArenaModelUpdater import failed: {e}")

# Test legacy
try:
    from custom_nodes.ComfyUI_Arena.legacy.arena_make_tiles_segs import Arena_MakeTilesSegs
    print("✓ Arena_MakeTilesSegs imported successfully")
except Exception as e:
    print(f"✗ Arena_MakeTilesSegs import failed: {e}")

print("\n=== Test completed ===")
