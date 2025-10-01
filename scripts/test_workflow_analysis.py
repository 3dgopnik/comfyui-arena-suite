#!/usr/bin/env python3
"""
Test script for Arena Workflow Analyzer
Тестирует JavaScript анализ workflow и Python API
"""

import json
import requests
import time
from pathlib import Path

def test_workflow_analysis_api():
    """Tests API endpoint for workflow analysis"""
    print("Testing Arena Workflow Analyzer API")
    print("=" * 50)
    
    # Test data
    test_models = [
        {
            "name": "test_checkpoint.safetensors",
            "type": "checkpoint",
            "field": "ckpt_name",
            "nodeId": "1",
            "classType": "CheckpointLoaderSimple"
        },
        {
            "name": "test_vae.safetensors",
            "type": "vae",
            "field": "vae_name",
            "nodeId": "2",
            "classType": "VAELoader"
        },
        {
            "name": "test_lora.safetensors",
            "type": "lora",
            "field": "lora_name",
            "nodeId": "3",
            "classType": "LoraLoader"
        }
    ]
    
    # Test payload
    payload = {
        "models": test_models,
        "timestamp": int(time.time() * 1000),
        "nodeId": "test_arena_node"
    }
    
    print(f"Sending {len(test_models)} test models...")
    print(f"   Models: {[m['name'] for m in test_models]}")
    
    try:
        # Отправка запроса
        response = requests.post(
            "http://127.0.0.1:8188/arena/analyze_workflow",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"API Response: {result}")
            return True
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Connection Error: ComfyUI server not running")
        return False
    except requests.exceptions.Timeout:
        print("Timeout Error: Request timed out")
        return False
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return False

def test_workflow_models_storage():
    """Tests workflow models storage"""
    print("\nTesting Workflow Models Storage")
    print("=" * 50)
    
    try:
        # Импортируем функции из ноды
        import sys
        sys.path.append(str(Path(__file__).parent.parent))
        
        from autocache.arena_auto_cache_simple import (
            _add_workflow_models,
            _get_workflow_models,
            _clear_workflow_models
        )
        
        # Test models
        test_models = [
            {"name": "test1.safetensors", "type": "checkpoint"},
            {"name": "test2.safetensors", "type": "vae"},
            {"name": "test3.safetensors", "type": "lora"}
        ]
        
        print("Adding test models...")
        _add_workflow_models(test_models)
        
        print("Retrieving stored models...")
        stored_models = _get_workflow_models()
        print(f"   Stored models: {stored_models}")
        
        print("Clearing models...")
        _clear_workflow_models()
        
        cleared_models = _get_workflow_models()
        print(f"   Models after clear: {cleared_models}")
        
        if len(stored_models) == 3 and len(cleared_models) == 0:
            print("Storage test passed")
            return True
        else:
            print("Storage test failed")
            return False
            
    except ImportError as e:
        print(f"Import Error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return False

def test_javascript_extension():
    """Tests JavaScript extension"""
    print("\nTesting JavaScript Extension")
    print("=" * 50)
    
    # Check file exists
    js_file = Path("web/extensions/arena_workflow_analyzer.js")
    if not js_file.exists():
        print(f"JavaScript file not found: {js_file}")
        return False
    
    # Check content
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_functions = [
        "ArenaWorkflowAnalyzer",
        "analyzeCurrentWorkflow",
        "getCurrentWorkflowModels",
        "extractModelsFromNode"
    ]
    
    missing_functions = []
    for func in required_functions:
        if func not in content:
            missing_functions.append(func)
    
    if missing_functions:
        print(f"Missing functions: {missing_functions}")
        return False
    
    print("JavaScript extension structure is correct")
    return True

def main():
    """Main test function"""
    print("Arena Workflow Analyzer Test Suite")
    print("=" * 50)
    
    tests = [
        ("JavaScript Extension", test_javascript_extension),
        ("Workflow Models Storage", test_workflow_models_storage),
        ("API Endpoint", test_workflow_analysis_api)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning {test_name} test...")
        result = test_func()
        results.append((test_name, result))
    
    # Results
    print("\nTest Results:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nSummary: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("All tests passed! Arena Workflow Analyzer is ready!")
    else:
        print("Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
