#!/usr/bin/env python3
"""
Тест статуса MCP подключения к ComfyUI
"""
import requests
import json

def test_mcp_endpoints():
    """Тестирует различные эндпоинты MCP ComfyUI"""
    base_url = "http://127.0.0.1:8003"
    
    endpoints = [
        "/sse",
        "/system_stats", 
        "/history",
        "/queue",
        "/prompt"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            if endpoint == "/sse":
                # SSE endpoint может требовать специальной обработки
                response = requests.get(f"{base_url}{endpoint}", timeout=5, stream=True)
            else:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            results[endpoint] = {
                "status_code": response.status_code,
                "accessible": response.status_code in [200, 201],
                "content_type": response.headers.get('content-type', 'unknown')
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    results[endpoint]["data_preview"] = str(data)[:100] + "..." if len(str(data)) > 100 else str(data)
                except:
                    results[endpoint]["data_preview"] = "Non-JSON response"
                    
        except requests.exceptions.ConnectionError:
            results[endpoint] = {"error": "Connection refused"}
        except requests.exceptions.Timeout:
            results[endpoint] = {"error": "Timeout"}
        except Exception as e:
            results[endpoint] = {"error": str(e)}
    
    return results

def test_arena_workflow_direct():
    """Тестирует прямой запуск ArenaAutoCacheSmart workflow"""
    base_url = "http://127.0.0.1:8003"
    
    # Workflow с ArenaAutoCacheSmart v2.4
    workflow = {
        "1": {
            "inputs": {
                "workflow_source": "auto",
                "auto_cache": True,
                "show_analysis": True,
                "categories": "checkpoints,loras,controlnet,upscale_models"
            },
            "class_type": "ArenaAutoCacheSmart v2.4",
            "_meta": {
                "title": "Arena AutoCache: Smart v2.4"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/prompt",
            json={"prompt": workflow},
            timeout=10
        )
        
        return {
            "status_code": response.status_code,
            "response": response.text,
            "success": response.status_code == 200
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("🔍 Тестирование MCP ComfyUI подключения...")
    print("=" * 50)
    
    # Тест эндпоинтов
    print("\n📡 Тестирование эндпоинтов:")
    endpoints_results = test_mcp_endpoints()
    
    for endpoint, result in endpoints_results.items():
        if "error" in result:
            print(f"❌ {endpoint}: {result['error']}")
        else:
            status = "✅" if result["accessible"] else "❌"
            print(f"{status} {endpoint}: {result['status_code']} ({result['content_type']})")
            if "data_preview" in result:
                print(f"   Preview: {result['data_preview']}")
    
    # Тест ArenaAutoCacheSmart
    print("\n🚀 Тестирование ArenaAutoCacheSmart v2.4:")
    arena_result = test_arena_workflow_direct()
    
    if "error" in arena_result:
        print(f"❌ Ошибка: {arena_result['error']}")
    else:
        status = "✅" if arena_result["success"] else "❌"
        print(f"{status} Статус: {arena_result['status_code']}")
        print(f"Ответ: {arena_result['response']}")
    
    print("\n" + "=" * 50)
    print("Тест завершен!")
