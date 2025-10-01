# Professional Cursor Setup for ComfyUI Node Development

## ✅ Что было настроено

### 1. Структура правил Cursor (`.cursor/rules/`)

- **`00-process.mdc`** - Основные правила процесса и документации (Always)
- **`10-comfyui-node.mdc`** - Контракт и стиль для ComfyUI нод (Auto Attached)
- **`20-tests-tooling.mdc`** - Правила тестирования и инструментов (Agent Requested)
- **`30-release.mdc`** - Шаблоны для релизных заметок (Manual)
- **`40-platform-paths.mdc`** - Справочник путей ComfyUI Desktop (Always)
- **`50-context.mdc`** - Управление context.md и концепция ноды (Always)
- **`60-mcp-tools.mdc`** - Правила использования MCP инструментов (Always)

### 2. Инструменты качества кода

- **Ruff** - быстрый линтер и форматтер
- **MyPy** - статическая проверка типов
- **Pytest** - фреймворк тестирования
- **Pre-commit hooks** - автоматические проверки при коммитах

### 3. Конфигурационные файлы

- **`pyproject.toml`** - настройки ruff, mypy, pytest
- **`.pre-commit-config.yaml`** - хуки для git
- **`requirements-dev.txt`** - зависимости для разработки
- **`tests/`** - структура тестов

### 4. Документация

- **`docs/tasktracker.md`** - отслеживание задач
- **`docs/DEVELOPMENT.md`** - руководство разработчика
- **`CHANGELOG.md`** - обновлен с новой записью

### 5. MCP инструменты

- **MCP docs-manager** - управление документацией
- **MCP changelog** - автоматический changelog
- **MCP GitHub** - интеграция с GitHub
- **MCP filesystem** - работа с файлами
- **MCP memory** - управление контекстом

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
# Создайте виртуальное окружение
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # Linux/Mac

# Установите зависимости для разработки
pip install -r requirements-dev.txt

# Настройте pre-commit hooks
pre-commit install
```

### 2. Проверка настройки

```bash
# Windows
scripts\check_dev_setup.bat

# PowerShell
scripts\check_dev_setup.ps1
```

### 3. Первые команды

```bash
# Проверка качества кода
ruff check .
ruff format .

# Проверка типов
mypy .

# Запуск тестов
pytest

# Все проверки сразу
pre-commit run --all-files
```

## 📋 Как использовать правила Cursor

### Автоматические правила (Always)
- Загружаются автоматически при открытии проекта
- Включают основные процессы, справочник путей и управление context.md

### Правила для ComfyUI нод (Auto Attached)
- Активируются при работе с файлами нод (`**/nodes/**/*.py`)
- Содержат контракт и стандарты для ComfyUI нод

### Правила тестирования (Agent Requested)
- Запрашивайте агента: "Apply tests and tooling rules"
- Содержат настройки pytest, ruff, mypy

### Правила релизов (Manual)
- Запускайте вручную для генерации changelog
- Содержат шаблоны для релизных заметок

## 🎯 Workflow разработки

### 1. Создание задачи
- Создайте Issue в GitHub
- Обновите `docs/tasktracker.md`
- Создайте ветку

### 2. Разработка
- Cursor автоматически применяет правила для ComfyUI нод
- Следуйте стандартам из правил
- **ОБЯЗАТЕЛЬНО** используйте MCP инструменты для документации
- Пишите тесты

### 3. Проверка качества
- Pre-commit hooks запускаются автоматически
- Ручная проверка: `ruff check . && mypy . && pytest`

### 4. Code Review
- Создайте Pull Request
- Привяжите к Issue
- Укажите все требуемые поля

### 5. Релиз
- Используйте правила из `30-release.mdc`
- Обновите версию и changelog
- Создайте GitHub Release

## 🔧 Настройка Cursor IDE

### 1. Открытие проекта
```bash
cursor .
```

### 2. Проверка правил
- Откройте любой Python файл
- Cursor должен автоматически загрузить правила
- Проверьте статус правил в интерфейсе

### 3. Тестирование правил
- Создайте тестовый файл `test_node.py` в папке с нодами
- Cursor должен предложить шаблон ComfyUI ноды
- Проверьте автодополнение и подсказки

## 📁 Структура проекта

```
.cursor/rules/              # Правила Cursor IDE
├── 00-process.mdc         # Процесс и документация
├── 10-comfyui-node.mdc    # Контракт ComfyUI нод
├── 20-tests-tooling.mdc   # Тестирование и инструменты
├── 30-release.mdc         # Релизы и changelog
├── 40-platform-paths.mdc  # Пути ComfyUI Desktop
├── 50-context.mdc         # Управление context.md
└── 60-mcp-tools.mdc       # Правила MCP инструментов

docs/                       # Документация
├── tasktracker.md         # Отслеживание задач
├── DEVELOPMENT.md         # Руководство разработчика
└── ru/                    # Русская документация

tests/                      # Тесты
├── conftest.py           # Конфигурация pytest
├── test_nodes/           # Тесты нод
└── fixtures/             # Тестовые данные

scripts/                    # Скрипты
├── check_dev_setup.bat   # Проверка настройки (Windows)
└── check_dev_setup.ps1   # Проверка настройки (PowerShell)
```

## 🐛 Troubleshooting

### Проблемы с Cursor
1. Перезапустите Cursor IDE
2. Проверьте, что файлы правил находятся в `.cursor/rules/`
3. Убедитесь, что расширение `.mdc` поддерживается

### Проблемы с инструментами
```bash
# Проверка установки
python -c "import ruff, mypy, pytest, pre_commit"

# Переустановка зависимостей
pip install --upgrade -r requirements-dev.txt

# Очистка кэша
ruff clean
mypy --clear-cache
```

### Проблемы с путями
- Проверьте `40-platform-paths.mdc` для актуальных путей
- Обновите пути в правилах при изменении установки ComfyUI

### Проблемы с MCP инструментами
```bash
# Проверка доступности MCP docs-manager
mcp_docs-manager_list_documents(path="docs", recursive=true)

# Проверка здоровья документации
mcp_docs-manager_check_documentation_health(path="docs")

# Проверка статуса changelog
mcp_changelog_changelog-status()
```

## 📞 Поддержка

- **GitHub Issues**: https://github.com/3dgopnik/comfyui-arena-suite/issues
- **Документация**: `docs/ru/` (русский) / `docs/en/` (английский)
- **Development Guide**: `docs/DEVELOPMENT.md`

---

**Готово!** Теперь у вас есть профессиональная настройка Cursor IDE для разработки ComfyUI нод с полным набором инструментов качества кода и автоматизированным процессом разработки.