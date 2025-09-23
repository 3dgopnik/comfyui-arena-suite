#!/usr/bin/env python3
"""
Тест подключения к ComfyUI через MCP
"""
import requests
import json

def test_comfyui_connection():
    """Тестирует подключение к ComfyUI"""
    base_url = "http://127.0.0.1:8003"
    
    try:
        # Проверяем системную статистику
        response = requests.get(f"{base_url}/system_stats", timeout=5)
        if response.status_code == 200:
            print("✅ ComfyUI доступен!")
            print(f"Статистика: {response.json()}")
            return True
        else:
            print(f"❌ ComfyUI недоступен. Статус: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к ComfyUI (порт 8188)")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_arena_workflow():
    """Тестирует запуск ArenaAutoCacheSmart workflow"""
    base_url = "http://127.0.0.1:8003"
    
    # Простой workflow с ArenaAutoCacheSmart
    workflow = {
        "1": {
            "inputs": {
                "workflow_source": "auto",
                "auto_cache": True,
                "show_analysis": True,
                "categories": "checkpoints,loras,controlnet,upscale_models"
            },
            "class_type": "ArenaAutoCacheSmart",
            "_meta": {
                "title": "Arena AutoCache: Smart"
            }
        }
    }
    
    try:
        # Отправляем workflow на выполнение
        response = requests.post(
            f"{base_url}/prompt",
            json={"prompt": workflow},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Workflow отправлен на выполнение!")
            print(f"Результат: {result}")
            return result.get("prompt_id")
        else:
            print(f"❌ Ошибка отправки workflow. Статус: {response.status_code}")
            print(f"Ответ: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка при отправке workflow: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Тестирование подключения к ComfyUI...")
    
    if test_comfyui_connection():
        print("\n🚀 Тестирование ArenaAutoCacheSmart workflow...")
        prompt_id = test_arena_workflow()
        
        if prompt_id:
            print(f"\n✅ Workflow выполняется с ID: {prompt_id}")
        else:
            print("\n❌ Не удалось запустить workflow")
    else:
        print("\n❌ ComfyUI недоступен. Убедитесь, что ComfyUI запущен на порту 8003")
