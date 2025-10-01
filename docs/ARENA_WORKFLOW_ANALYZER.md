# Arena Workflow Analyzer

## Обзор

**Arena Workflow Analyzer** - это JavaScript extension для ComfyUI, который анализирует текущий workflow на канвасе и извлекает информацию о моделях для умного кеширования.

## Функциональность

### 🎯 **Основные возможности:**
- **Анализ workflow** - автоматическое извлечение моделей из текущего workflow
- **Предварительное кеширование** - кеширование моделей до их использования
- **Умное кеширование** - кеширует только модели, используемые в workflow
- **Интеграция с Arena AutoCache** - работает с Python нодой для кеширования

### 🔧 **Технические детали:**

#### **JavaScript Extension:**
- **Файл:** `web/extensions/arena_workflow_analyzer.js`
- **Расположение:** ComfyUI Desktop: `web/extensions/arena/`
- **Функции:** Анализ workflow, извлечение моделей, отправка на сервер

#### **Python API:**
- **Endpoint:** `/arena/analyze_workflow`
- **Метод:** POST
- **Функции:** Получение моделей от JavaScript, предварительное кеширование

## Установка

### 1. **JavaScript Extension:**
```bash
# Копирование в ComfyUI Desktop
Copy-Item "web/extensions/arena_workflow_analyzer.js" -Destination "c:\Users\acherednikov\AppData\Local\Programs\@comfyorgcomfyui-electron\resources\ComfyUI\web\extensions\arena\"
```

### 2. **Python Integration:**
- Интегрировано в `autocache/arena_auto_cache_simple.py`
- API endpoint автоматически регистрируется при загрузке ноды

## Использование

### **Автоматический режим:**
1. Добавьте ноду Arena AutoCache на канвас
2. Включите `enable_caching=True`
3. JavaScript автоматически анализирует workflow
4. Модели предварительно кешируются

### **Ручной анализ:**
```javascript
// Анализ текущего workflow
const workflow = ArenaWorkflowAnalyzer.analyzeCurrentWorkflow();

// Получение моделей
const models = ArenaWorkflowAnalyzer.getCurrentWorkflowModels();
```

## API Reference

### **JavaScript API:**

#### `ArenaWorkflowAnalyzer.analyzeCurrentWorkflow()`
- **Описание:** Анализирует текущий workflow на канвасе
- **Возвращает:** Объект workflow или null
- **Пример:**
```javascript
const workflow = ArenaWorkflowAnalyzer.analyzeCurrentWorkflow();
```

#### `ArenaWorkflowAnalyzer.getCurrentWorkflowModels()`
- **Описание:** Получает все модели из текущего workflow
- **Возвращает:** Массив объектов моделей
- **Пример:**
```javascript
const models = ArenaWorkflowAnalyzer.getCurrentWorkflowModels();
console.log(models); // [{name: "model.safetensors", type: "checkpoint", ...}]
```

### **Python API:**

#### `POST /arena/analyze_workflow`
- **Описание:** Получает модели от JavaScript анализа
- **Тело запроса:**
```json
{
  "models": [
    {
      "name": "model.safetensors",
      "type": "checkpoint",
      "field": "ckpt_name",
      "nodeId": "1",
      "classType": "CheckpointLoaderSimple"
    }
  ],
  "timestamp": 1698765432000,
  "nodeId": "arena_node_id"
}
```

- **Ответ:**
```json
{
  "status": "success",
  "models_count": 5
}
```

## Поддерживаемые типы моделей

### **Checkpoint модели:**
- `CheckpointLoaderSimple`
- `CheckpointLoader`
- `Load Diffusion Model`

### **LoRA модели:**
- `LoraLoader`
- `LoraLoaderAdvanced`

### **CLIP модели:**
- `CLIPLoader`
- `DualCLIPLoader`
- `CLIPLoader GGUF`

### **VAE модели:**
- `VAELoader`
- `VAEDecode`

### **ControlNet модели:**
- `ControlNetLoader`
- `ControlNetApply`

### **Upscale модели:**
- `UpscaleModelLoader`
- `ImageUpscaleWithModel`

### **Embeddings:**
- `LoadEmbedding`
- `CLIPTextEncode`

### **Hypernetworks:**
- `HypernetworkLoader`

## Логирование

### **JavaScript:**
```javascript
console.log("[Arena Workflow Analyzer] Loading...");
console.log("[Arena Workflow Analyzer] Found 5 models:", models);
```

### **Python:**
```python
print("[ArenaAutoCache] Received 5 models from JavaScript")
print("[ArenaAutoCache] Precaching 5 workflow models...")
```

## Отладка

### **Проверка загрузки extension:**
1. Откройте Developer Tools (F12)
2. Проверьте Console на наличие сообщений:
```
[Arena Workflow Analyzer] Loading...
[Arena Workflow Analyzer] Extension loaded successfully
```

### **Проверка API:**
1. Проверьте Network tab в Developer Tools
2. Ищите запросы к `/arena/analyze_workflow`
3. Проверьте ответы сервера

### **Проверка кеширования:**
1. Проверьте логи ComfyUI на наличие сообщений:
```
[ArenaAutoCache] Received 5 models from JavaScript
[ArenaAutoCache] Precaching 5 workflow models...
```

## Ограничения

### **Поддерживаемые ноды:**
- Только стандартные ноды ComfyUI
- Ноды с полями: `ckpt_name`, `vae_name`, `lora_name`, `clip_name`, etc.

### **Не поддерживаются:**
- Кастомные ноды без стандартных полей
- Ноды с динамическими именами моделей
- Ноды с зашифрованными путями

## Устранение неполадок

### **Extension не загружается:**
1. Проверьте путь к файлу
2. Проверьте синтаксис JavaScript
3. Перезапустите ComfyUI

### **API не работает:**
1. Проверьте, что нода Arena AutoCache загружена
2. Проверьте логи Python
3. Проверьте Network tab

### **Модели не кешируются:**
1. Проверьте настройки кеширования
2. Проверьте права доступа к папкам
3. Проверьте логи кеширования

## Разработка

### **Добавление новых типов моделей:**
1. Обновите `modelFields` в JavaScript
2. Обновите `typeMap` в JavaScript
3. Обновите `DEFAULT_WHITELIST` в Python

### **Добавление новых нод:**
1. Добавьте `class_type` в `extractModelsFromNode`
2. Добавьте поля модели в `modelFields`
3. Протестируйте с реальными workflow

## Changelog

### **v1.0.0 (2025-10-01):**
- ✅ Создан JavaScript extension для анализа workflow
- ✅ Добавлен API endpoint для получения моделей
- ✅ Интеграция с OnDemand режимом
- ✅ Поддержка основных типов моделей
- ✅ Предварительное кеширование моделей
- ✅ Логирование и отладка
