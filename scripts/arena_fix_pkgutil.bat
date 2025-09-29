@echo off
REM Arena Fix pkgutil - Исправляет ошибку pkgutil.ImpImporter в Python 3.12
REM Откатывает setuptools до совместимой версии

echo [Arena Fix pkgutil] Исправление ошибки pkgutil.ImpImporter...

cd /d "C:\ComfyUI"

echo [Arena Fix pkgutil] Текущая версия setuptools:
python -c "import setuptools; print('setuptools version:', setuptools.__version__)"

echo [Arena Fix pkgutil] Откат setuptools до совместимой версии...
pip install "setuptools<70.0.0" --force-reinstall

echo [Arena Fix pkgutil] Проверка исправления...
python -c "import pkg_resources; print('pkg_resources работает!')"

if %ERRORLEVEL% EQU 0 (
    echo [Arena Fix pkgutil] ✅ Исправление успешно!
    echo [Arena Fix pkgutil] Теперь ComfyUI-3D-Pack должен работать
) else (
    echo [Arena Fix pkgutil] ❌ Ошибка все еще присутствует
    echo [Arena Fix pkgutil] Попробуйте альтернативное решение:
    echo [Arena Fix pkgutil] 1. pip install "setuptools==69.5.1"
    echo [Arena Fix pkgutil] 2. Или отключите ComfyUI-3D-Pack
)

echo [Arena Fix pkgutil] Готово!
pause


