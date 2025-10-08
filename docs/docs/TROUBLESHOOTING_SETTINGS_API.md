# ComfyUI Settings API - Решение проблем с PrimeVue InputNumber

## Проблема
PrimeVue InputNumber компоненты в ComfyUI Settings UI не коммитят значения до blur/Enter события. Это приводит к тому, что DOM парсинг всегда возвращает 0 или старое значение.

## Решение
Использовать официальный ComfyUI Settings API вместо парсинга DOM.

### Код решения
```javascript
// ❌ НЕПРАВИЛЬНО - DOM парсинг
const value = document.querySelector('input.p-inputnumber-input').value; // всегда 0

// ✅ ПРАВИЛЬНО - ComfyUI API
const value = await app.extensionManager.setting.get("arena.max_cache_gb");
```

### Полная реализация
```javascript
async function getSettingValue(settingId) {
    try {
        // 1) Try ComfyUI's official settings API (most reliable)
        if (app?.extensionManager?.setting?.get) {
            const apiValue = await app.extensionManager.setting.get(settingId);
            if (apiValue !== undefined && apiValue !== null) {
                return apiValue;
            }
        }
        
        // 2) Force commit DOM values before reading (fallback)
        if (settingId.includes('max_cache_gb') || settingId.includes('min_size_mb')) {
            document.activeElement?.blur(); // Force commit in-flight value
            await new Promise(resolve => setTimeout(resolve, 50));
        }
        
        // 3) DOM fallback with committed values
        // ... DOM parsing logic
        
    } catch (e) {
        console.error(`Failed to get ${settingId}:`, e);
    }
    return null;
}
```

## Порядок приоритета
1. **ComfyUI Settings API** - `app.extensionManager.setting.get()`
2. **Internal Store** - `app.ui.settings.get()`
3. **localStorage** - Comfy.Settings keys
4. **DOM parsing** - с принудительным blur()

## Проверка работы
DevTools.log должен показывать:
```
arena.max_cache_gb (API): 522
Response data: {status: 'success', message: 'Updated 12 environment variables and saved to .env file'}
```

## Когда использовать
- Все числовые поля PrimeVue InputNumber
- Поля с задержкой коммита (blur/Enter)
- Критичные настройки где нужна точность

## Техническая информация
- **PrimeVue InputNumber**: не обновляет modelValue мгновенно
- **ComfyUI API**: всегда возвращает актуальное значение
- **Timing issue**: DOM читает до коммита, API читает после
- **Fallback strategy**: принудительный blur() + задержка 50ms

---
*Документ создан после успешного решения проблемы с arena.max_cache_gb*