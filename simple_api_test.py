import requests
import json

# Простой тест ComfyUI API
try:
    response = requests.get("http://127.0.0.1:8000/system_stats", timeout=5)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ ComfyUI доступен!")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ Ошибка: {response.text}")
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")

# Тест ArenaAutoCacheSmart
workflow = {
    "1": {
        "inputs": {
            "workflow_source": "auto",
            "auto_cache": True,
            "show_analysis": True,
            "categories": "checkpoints,loras"
        },
        "class_type": "ArenaAutoCacheSmart v2.4",
        "_meta": {"title": "Arena AutoCache: Smart v2.4"}
    }
}

try:
    response = requests.post("http://127.0.0.1:8000/prompt", json={"prompt": workflow}, timeout=10)
    print(f"\nWorkflow Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Workflow отправлен! ID: {result.get('prompt_id')}")
    else:
        print(f"❌ Ошибка workflow: {response.text}")
except Exception as e:
    print(f"❌ Ошибка workflow: {e}")
