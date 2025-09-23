#!/usr/bin/env python3
"""
Тест ArenaAutoCacheSmart v2.11 с реальными workflow
"""

import json
import sys
import os

# Добавляем путь к нашему модулю
sys.path.append(os.path.join(os.path.dirname(__file__), 'custom_nodes', 'ComfyUI_Arena', 'autocache'))

def test_workflow_analysis():
    """Тестируем анализ workflow с реальными данными"""
    
    # Тестовый workflow из test.json
    test_workflow = {
        "id": "d90170c5-9b54-4d88-b459-d74b89de9ce8",
        "revision": 0,
        "last_node_id": 15,
        "last_link_id": 23,
        "nodes": [
            {
                "id": 4,
                "type": "CheckpointLoaderSimple",
                "pos": [-600, 180],
                "size": [315, 98],
                "flags": {},
                "order": 1,
                "mode": 0,
                "inputs": [{"localized_name": "ckpt_name", "name": "ckpt_name", "type": "COMBO", "widget": {"name": "ckpt_name"}, "link": None}],
                "outputs": [
                    {"localized_name": "MODEL", "name": "MODEL", "type": "MODEL", "slot_index": 0, "links": [20]},
                    {"localized_name": "CLIP", "name": "CLIP", "type": "CLIP", "slot_index": 1, "links": [19]},
                    {"localized_name": "VAE", "name": "VAE", "type": "VAE", "slot_index": 2, "links": [8]}
                ],
                "properties": {"cnr_id": "comfy-core", "ver": "0.3.59", "Node name for S&R": "CheckpointLoaderSimple"},
                "widgets_values": ["Juggernaut_X_RunDiffusion_Hyper.safetensors"]
            },
            {
                "id": 15,
                "type": "Power Lora Loader (rgthree)",
                "pos": [-120, 210],
                "size": [324.8211669921875, 142],
                "flags": {},
                "order": 3,
                "mode": 0,
                "inputs": [
                    {"dir": 3, "name": "model", "type": "MODEL", "link": 20},
                    {"dir": 3, "name": "clip", "type": "CLIP", "link": 19}
                ],
                "outputs": [
                    {"dir": 4, "name": "MODEL", "shape": 3, "type": "MODEL", "links": [23]},
                    {"dir": 4, "name": "CLIP", "shape": 3, "type": "CLIP", "links": [21, 22]}
                ],
                "properties": {"cnr_id": "rgthree-comfy", "ver": "0fb1e239a903e93ef626a8c20589b38f46e39dff", "Show Strengths": "Single Strength"},
                "widgets_values": [{}, {"type": "PowerLoraLoaderHeaderWidget"}, {"on": True, "lora": "polyhedron_all_sdxl-000004.safetensors", "strength": 1, "strengthTwo": None}, {}, ""]
            }
        ],
        "links": [],
        "groups": [],
        "config": {},
        "extra": {"ds": {"scale": 1.0610764609500007, "offset": [1525.2789011416812, 6.313667150237457]}},
        "version": 0.4
    }
    
    print("🔍 Тестируем ArenaAutoCacheSmart v2.11")
    print("=" * 50)
    
    # Импортируем функцию анализа
    try:
        from arena_auto_cache import _extract_models_from_workflow_json, _get_model_category
        
        print("✅ Модуль импортирован успешно")
        
        # Тестируем извлечение моделей
        models = _extract_models_from_workflow_json(test_workflow)
        
        print(f"\n📊 Результаты анализа:")
        print(f"Найдено моделей: {len(models)}")
        
        for i, model in enumerate(models, 1):
            print(f"  {i}. {model['name']} ({model['category']})")
            
        print(f"\n🎯 Ожидаемые результаты:")
        print(f"  1. Juggernaut_X_RunDiffusion_Hyper.safetensors (checkpoints)")
        print(f"  2. polyhedron_all_sdxl-000004.safetensors (loras)")
        
        if len(models) == 2:
            print(f"\n✅ ТЕСТ ПРОЙДЕН! Все модели найдены корректно")
        else:
            print(f"\n❌ ТЕСТ НЕ ПРОЙДЕН! Ожидалось 2 модели, найдено {len(models)}")
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
    except Exception as e:
        print(f"❌ Ошибка выполнения: {e}")

if __name__ == "__main__":
    test_workflow_analysis()
