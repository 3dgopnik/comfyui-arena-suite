# 🛠️ Arena Suite - Development Guide

## 📁 Структура проекта

```
ComfyUI-Arena/
├── __init__.py                    # Точка входа с WEB_DIRECTORY = "web"
├── autocache/                     # Python модули кеширования
│   └── arena_auto_cache_simple.py
├── web/                          # JavaScript файлы для ComfyUI
│   ├── arena_settings_save_button.js # Settings UI с кнопкой Save
│   ├── arena_simple_header.js    # Floating Arena button
│   ├── arena_autocache.js        # AutoCache extension
│   └── arena_workflow_analyzer.js # Workflow analysis
├── scripts/                      # Утилиты разработки
│   ├── sync_js_files.ps1         # Синхронизация JS файлов
│   └── sync_js_files.bat         # Bat-файл для запуска
└── docs/                         # Документация
```

## 🔄 Синхронизация JavaScript файлов

### Проблема
ComfyUI Desktop загружает JavaScript файлы из внутренней установки, а не из папки разработки:

- **Папка разработки**: `C:\ComfyUI\custom_nodes\ComfyUI-Arena\web\`
- **Папка ComfyUI Desktop**: `C:\Users\[USER]\AppData\Local\Programs\@comfyorgcomfyui-electron\resources\ComfyUI\custom_nodes\ComfyUI-Arena\web\`

### Решение
Используйте скрипт синхронизации после каждого изменения JavaScript файлов:

```powershell
# Обычная синхронизация (только измененные файлы)
.\scripts\sync_js_files.ps1

# Принудительная синхронизация всех файлов
.\scripts\sync_js_files.ps1 -Force

# Подробный вывод
.\scripts\sync_js_files.ps1 -Verbose

# Или используйте bat-файл
.\scripts\sync_js_files.bat
```

### Функции скрипта
- ✅ Проверка существования папок
- ✅ Сравнение MD5 хешей файлов
- ✅ Копирование только измененных файлов
- ✅ Цветовой вывод с эмодзи
- ✅ Обработка ошибок
- ✅ Статистика синхронизации

## 🎯 Workflow разработки

### 1. Изменение JavaScript файлов
```bash
# Редактируйте файлы в папке web/
code web/arena_settings_panel.js
```

### 2. Синхронизация
```powershell
.\scripts\sync_js_files.ps1 -Verbose
```

### 3. Тестирование
```bash
# Перезапустите ComfyUI Desktop
# Проверьте работу Settings Panel
# Убедитесь в корректности поведения
```

## 🔧 Настройка окружения

### ComfyUI Desktop
- Установлен в: `C:\Users\[USER]\AppData\Local\Programs\@comfyorgcomfyui-electron\`
- Кастомные ноды в: `resources\ComfyUI\custom_nodes\`

### Права доступа
Убедитесь, что у вас есть права на запись в папку ComfyUI Desktop:
```powershell
# Проверка прав
Test-Path "C:\Users\[USER]\AppData\Local\Programs\@comfyorgcomfyui-electron\resources\ComfyUI\custom_nodes\ComfyUI-Arena\web\"
```

## 🐛 Troubleshooting

### Проблема: Скрипт не находит папку разработки
**Решение**: Запускайте скрипт из корня проекта `ComfyUI-Arena/`

### Проблема: Ошибка доступа к файлам
**Решение**: Запустите PowerShell от имени администратора

### Проблема: JavaScript изменения не применяются
**Решение**: 
1. Убедитесь, что файлы синхронизированы
2. Перезапустите ComfyUI Desktop
3. Проверьте консоль браузера на ошибки

## 📋 Чек-лист разработки

- [ ] Изменены JavaScript файлы в `web/`
- [ ] Запущен скрипт синхронизации `sync_js_files.ps1`
- [ ] ComfyUI Desktop перезапущен
- [ ] Settings → arena работает корректно
- [ ] Кнопка **💾 Save to .env** создает файл
- [ ] .env файл содержит все настройки
- [ ] Кнопка ARENA в header работает
- [ ] Нет ошибок в DevTools Console

## 🚀 Автоматизация

### Pre-commit hook
Можно добавить автоматическую синхронизацию в git hooks:

```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "🔄 Синхронизация JavaScript файлов..."
powershell.exe -ExecutionPolicy Bypass -File "scripts/sync_js_files.ps1"
```

### VS Code Task
Создайте `.vscode/tasks.json`:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Sync JS Files",
            "type": "shell",
            "command": "powershell.exe",
            "args": ["-ExecutionPolicy", "Bypass", "-File", "scripts/sync_js_files.ps1"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        }
    ]
}
```

## 📚 Дополнительные ресурсы

- [ComfyUI Custom Node Development](https://github.com/comfyanonymous/comfyui)
- [ComfyUI Manager Documentation](https://github.com/comfy-org/comfyui-manager)
- [Arena Suite Documentation](./docs/)