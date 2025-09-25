#!/usr/bin/env python3
"""
Simple API test for ComfyUI Arena Suite
"""

import json
import requests
import time
from pathlib import Path

def test_comfyui_connection():
    """Test basic ComfyUI connection"""
    try:
        response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
        if response.status_code == 200:
            print("✅ ComfyUI connection successful")
            return True
        else:
            print(f"❌ ComfyUI connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ComfyUI connection error: {e}")
        return False

def test_arena_nodes():
    """Test if Arena nodes are available"""
    try:
        response = requests.get("http://127.0.0.1:8188/object_info", timeout=5)
        if response.status_code == 200:
            data = response.json()
            arena_nodes = [node for node in data if 'arena' in node.lower()]
            if arena_nodes:
                print(f"✅ Found Arena nodes: {arena_nodes}")
                return True
            else:
                print("❌ No Arena nodes found")
                return False
        else:
            print(f"❌ Failed to get node info: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Arena nodes test error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing ComfyUI Arena Suite...")
    
    # Test connection
    if test_comfyui_connection():
        # Test Arena nodes
        test_arena_nodes()
    
    print("🏁 Test completed")