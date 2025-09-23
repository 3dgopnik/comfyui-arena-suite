#!/usr/bin/env python3
"""
Тест прямого подключения к ComfyUI API на порту 8000
"""
import requests
import json
import time

def test_comfyui_api():
    """Тестирует прямое подключение к ComfyUI API"""
    base_url = "http://127.0.0.1:8000"
    
    print("🔍 Тестирование ComfyUI API на порту 8000...")
    
    # 1. Проверяем системную статистику
    try:
        response = requests.get(f"{base_url}/system_stats", timeout=5)
        if response.status_code == 200:
            print("✅ ComfyUI API доступен!")
            stats = response.json()
            print(f"📊 Статистика: {stats}")
        else:
            print(f"❌ Ошибка API. Статус: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Не удается подключиться к ComfyUI: {e}")
        return False
    
    return True

def test_arena_workflow():
    """Тестирует запуск ArenaAutoCacheSmart workflow"""
    base_url = "http://127.0.0.1:8000"
    
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
    
    print("\n🚀 Запуск ArenaAutoCacheSmart v2.4 workflow...")
    
    try:
        # Отправляем workflow на выполнение
        response = requests.post(
            f"{base_url}/prompt",
            json={"prompt": workflow},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            prompt_id = result.get("prompt_id")
            print(f"✅ Workflow отправлен! ID: {prompt_id}")
            
            # Ждем выполнения
            print("⏳ Ожидание выполнения...")
            time.sleep(2)
            
            # Проверяем статус
            status_response = requests.get(f"{base_url}/history/{prompt_id}")
            if status_response.status_code == 200:
                history = status_response.json()
                print(f"📋 История выполнения: {json.dumps(history, indent=2)}")
                return True
            else:
                print(f"❌ Не удалось получить историю. Статус: {status_response.status_code}")
                return False
                
        else:
            print(f"❌ Ошибка отправки workflow. Статус: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при отправке workflow: {e}")
        return False

def test_queue_status():
    """Проверяет статус очереди ComfyUI"""
    base_url = "http://127.0.0.1:8000"
    
    try:
        response = requests.get(f"{base_url}/queue", timeout=5)
        if response.status_code == 200:
            queue_data = response.json()
            print(f"📋 Очередь: {json.dumps(queue_data, indent=2)}")
            return True
        else:
            print(f"❌ Ошибка получения очереди. Статус: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при получении очереди: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 ТЕСТ ПРЯМОГО ПОДКЛЮЧЕНИЯ К COMFYUI API")
    print("=" * 60)
    
    # Тест подключения
    if test_comfyui_api():
        print("\n" + "-" * 40)
        
        # Тест очереди
        print("📋 Проверка очереди:")
        test_queue_status()
        
        print("\n" + "-" * 40)
        
        # Тест ArenaAutoCacheSmart
        if test_arena_workflow():
            print("\n🎉 ArenaAutoCacheSmart v2.4 успешно протестирован!")
        else:
            print("\n❌ Ошибка при тестировании ArenaAutoCacheSmart")
    else:
        print("\n❌ ComfyUI недоступен. Убедитесь, что ComfyUI запущен на порту 8000")
    
    print("\n" + "=" * 60)
    print("Тест завершен!")
