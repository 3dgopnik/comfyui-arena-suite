#!/usr/bin/env python3
"""
Тестовый скрипт для проверки анализа JSON workflow
"""

import json
import sys
import os

# Добавляем путь к нашему модулю
sys.path.append(os.path.join(os.path.dirname(__file__), 'custom_nodes', 'ComfyUI_Arena', 'autocache'))

def _extract_models_from_workflow_json(workflow: dict) -> list[dict]:
    """Extract model information from workflow JSON structure."""
    models = []
    
    if not isinstance(workflow, dict) or 'nodes' not in workflow:
        return models
    
    # Node types that contain model information
    model_node_types = [
        'UNETLoader', 'UnetLoaderGGUF', 'VAELoader', 'CLIPLoader', 
        'LoraLoaderModelOnly', 'ControlNetLoader', 'UpscaleModelLoader',
        'IPAdapterModelLoader', 'InsightFaceLoader'
    ]
    
    for node in workflow.get('nodes', []):
        if not isinstance(node, dict):
            continue
            
        class_type = node.get('class_type', '')
        if class_type not in model_node_types:
            continue
            
        # Extract model information from widgets_values
        widgets_values = node.get('widgets_values', [])
        if not widgets_values:
            continue
            
        # Extract model name (usually first widget)
        model_name = widgets_values[0] if widgets_values else None
        if not model_name or not isinstance(model_name, str):
            continue
            
        # Extract additional information from properties
        properties = node.get('properties', {})
        directory = properties.get('directory', '')
        url = properties.get('url', '')
        
        # Determine category based on class_type
        category = _get_model_category(class_type)
        
        model_info = {
            'name': model_name,
            'class_type': class_type,
            'category': category,
            'directory': directory,
            'url': url,
            'node_id': node.get('id', '')
        }
        
        models.append(model_info)
        print(f"[Test] Found model: {model_name} ({category}) in {class_type}")
    
    return models


def _get_model_category(class_type: str) -> str:
    """Map ComfyUI node class types to model categories."""
    category_mapping = {
        'UNETLoader': 'checkpoints',
        'UnetLoaderGGUF': 'checkpoints',
        'VAELoader': 'vae',
        'CLIPLoader': 'clip',
        'LoraLoaderModelOnly': 'loras',
        'ControlNetLoader': 'controlnet',
        'UpscaleModelLoader': 'upscale_models',
        'IPAdapterModelLoader': 'ipadapter',
        'InsightFaceLoader': 'insightface'
    }
    return category_mapping.get(class_type, 'unknown')


def main():
    """Тестируем анализ JSON workflow"""
    print("=== Тест анализа JSON workflow ===")
    
    # Загружаем тестовый workflow
    try:
        with open('test_workflow.json', 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        print(f"✅ Загружен тестовый workflow: {len(workflow.get('nodes', []))} нод")
    except Exception as e:
        print(f"❌ Ошибка загрузки workflow: {e}")
        return
    
    # Анализируем workflow
    models = _extract_models_from_workflow_json(workflow)
    
    print(f"\n=== Результаты анализа ===")
    print(f"Найдено моделей: {len(models)}")
    
    for i, model in enumerate(models, 1):
        print(f"\n{i}. {model['name']}")
        print(f"   Тип ноды: {model['class_type']}")
        print(f"   Категория: {model['category']}")
        print(f"   ID ноды: {model['node_id']}")
        if model['directory']:
            print(f"   Директория: {model['directory']}")
        if model['url']:
            print(f"   URL: {model['url']}")
    
    print(f"\n=== Сводка ===")
    categories = {}
    for model in models:
        cat = model['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in categories.items():
        print(f"{cat}: {count} моделей")


if __name__ == "__main__":
    main()
