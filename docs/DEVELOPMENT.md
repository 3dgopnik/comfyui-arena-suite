# Development Guide

## Быстрый старт

### 1. Установка зависимостей

```bash
# Клонируйте репозиторий
git clone https://github.com/3dgopnik/comfyui-arena-suite.git
cd comfyui-arena-suite

# Создайте виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate     # Windows

# Установите зависимости для разработки
pip install -r requirements-dev.txt

# Настройте pre-commit hooks
pre-commit install
```

### 2. Настройка Cursor IDE

Проект настроен для работы с Cursor IDE. Правила автоматически загружаются из `.cursor/rules/`:

- `00-process.mdc` - основной процесс разработки
- `10-comfyui-node.mdc` - стандарты для ComfyUI нод
- `20-tests-tooling.mdc` - тестирование и инструменты
- `30-release.mdc` - релизы и changelog
- `40-platform-paths.mdc` - пути ComfyUI Desktop

### 3. Проверка качества кода

```bash
# Линтинг и форматирование
ruff check .
ruff format .

# Типизация
mypy .

# Тесты
pytest

# Все проверки сразу
pre-commit run --all-files
```

## Структура проекта

```
.cursor/rules/          # Правила Cursor IDE
docs/                   # Документация
├── ru/                # Русская документация
├── en/                # Английская документация
├── tasktracker.md     # Отслеживание задач
└── DEVELOPMENT.md     # Этот файл
tests/                 # Тесты
├── conftest.py       # Конфигурация pytest
├── test_nodes/       # Тесты нод
└── fixtures/         # Тестовые данные
autocache/            # Модули автокэширования
legacy/               # Устаревшие модули
updater/              # Модули обновления
web/                  # Web расширения
```

## Стандарты разработки

### ComfyUI Node Contract

Каждая нода должна соответствовать контракту:

```python
class ExampleNode:
    """Описание ноды."""

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Dict[str, Any]]:
        return {
            "required": {
                "input_param": ("STRING", {"default": "value"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "compute"
    CATEGORY = "Arena/Example"

    def compute(self, input_param: str) -> Tuple[str]:
        """Вычислительная функция ноды."""
        return (input_param,)

# Регистрация ноды
NODE_CLASS_MAPPINGS = {"ExampleNode": ExampleNode}
NODE_DISPLAY_NAME_MAPPINGS = {"ExampleNode": "Arena — Example"}
```

### Типизация

- Все функции должны иметь type hints
- Используйте `from __future__ import annotations` для forward references
- Документируйте сложные типы

### Тестирование

```python
import pytest
from unittest.mock import Mock, patch

class TestExampleNode:
    def test_basic_functionality(self) -> None:
        """Test basic node functionality."""
        node = ExampleNode()
        result = node.compute("test")
        assert result == ("test",)

    @pytest.mark.slow
    def test_slow_operation(self) -> None:
        """Test slow operation."""
        pass

    @pytest.mark.integration
    def test_comfyui_integration(self) -> None:
        """Test ComfyUI integration."""
        pass
```

## Workflow разработки

### 1. Создание задачи

- Создайте Issue в GitHub
- Обновите `docs/tasktracker.md`
- Создайте ветку для задачи

### 2. Разработка

- Следуйте стандартам из `.cursor/rules/`
- Пишите тесты для новой функциональности
- Обновляйте документацию

### 3. Проверка качества

```bash
# Автоматические проверки при коммите
git commit -m "feat: add new feature"

# Ручные проверки
ruff check .
mypy .
pytest
```

### 4. Code Review

- Создайте Pull Request
- Привяжите к Issue (Closes #номер)
- Укажите Summary, Changes, Docs, Changelog, Test Plan

### 5. Релиз

- Обновите версию в `pyproject.toml`
- Заполните changelog
- Создайте GitHub Release

## Отладка

### Логи ComfyUI

```bash
# Windows
tail -f "c:\\Users\\acherednikov\\AppData\\Roaming\\ComfyUI\\logs\\comfyui.log"

# Linux/Mac
tail -f ~/.local/share/ComfyUI/logs/comfyui.log
```

### Тестирование в ComfyUI

1. Скопируйте файлы в ComfyUI custom_nodes
2. Перезапустите ComfyUI
3. Проверьте в UI

### Синхронизация разработки

```powershell
# Windows - скопировать из dev в production
Copy-Item "c:\\ComfyUI\\custom_nodes\\СomfyUI-Arena\\*" -Destination "c:\\Users\\acherednikov\\AppData\\Local\\Programs\\@comfyorgcomfyui-electron\\resources\\ComfyUI\\custom_nodes\\СomfyUI-Arena\\" -Recurse -Force
```

## Полезные команды

```bash
# Форматирование кода
ruff format .

# Проверка безопасности
bandit -r .

# Проверка зависимостей
safety check

# Генерация документации
sphinx-build docs/ docs/_build/

# Очистка кэша
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## Troubleshooting

### Ошибки импорта

```python
# Добавьте в начало файла для отладки
import sys
print("Python path:", sys.path)
print("Current working directory:", os.getcwd())
```

### Проблемы с путями

Проверьте `40-platform-paths.mdc` для актуальных путей ComfyUI Desktop.

### Проблемы с типизацией

```bash
# Подробный вывод mypy
mypy --show-error-codes --show-column-numbers .

# Проверка конкретного файла
mypy autocache/arena_auto_cache_simple.py
```

## Контакты

- GitHub: https://github.com/3dgopnik/comfyui-arena-suite
- Issues: https://github.com/3dgopnik/comfyui-arena-suite/issues
- Documentation: `docs/ru/` (русский) / `docs/en/` (английский)
