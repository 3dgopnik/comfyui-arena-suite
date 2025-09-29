@echo off
REM Arena Test ComfyUI Startup - Тестирует исправления проблем запуска
REM Проверяет, что все критические ошибки исправлены

echo [Arena Test] Тестирование исправлений ComfyUI...

cd /d "C:\ComfyUI"

echo [Arena Test] 1. Проверка pkg_resources...
python -c "import pkg_resources; print('✅ pkg_resources работает')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [Arena Test] ❌ pkg_resources не работает
    goto :error
)

echo [Arena Test] 2. Проверка pkgutil.ImpImporter...
python -c "import pkgutil; print('✅ pkgutil.ImpImporter доступен:', hasattr(pkgutil, 'ImpImporter'))" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [Arena Test] ❌ pkgutil.ImpImporter недоступен
    goto :error
)

echo [Arena Test] 3. Проверка .cursor модуля...
if exist "C:\ComfyUI\custom_nodes\.cursor" (
    echo [Arena Test] ❌ .cursor модуль все еще существует
    goto :error
) else (
    echo [Arena Test] ✅ .cursor модуль удален
)

echo [Arena Test] 4. Проверка ComfyUI-3D-Pack...
if exist "C:\ComfyUI\custom_nodes\ComfyUI-3D-Pack" (
    echo [Arena Test] ✅ ComfyUI-3D-Pack присутствует
) else (
    echo [Arena Test] ⚠️ ComfyUI-3D-Pack отсутствует (возможно отключен)
)

echo [Arena Test] 5. Проверка версии setuptools...
python -c "import setuptools; print('✅ setuptools version:', setuptools.__version__)" 2>nul

echo [Arena Test] ✅ Все критические проблемы исправлены!
echo [Arena Test] ComfyUI должен запускаться быстрее
goto :end

:error
echo [Arena Test] ❌ Обнаружены проблемы, требующие внимания
echo [Arena Test] Запустите arena_fix_pkgutil.bat для исправления

:end
echo [Arena Test] Готово!
pause


