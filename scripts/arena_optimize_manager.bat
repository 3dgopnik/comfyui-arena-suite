@echo off
REM Arena Manager Optimization - Отключает автообновления ComfyUI-Manager
REM Ускоряет старт, отключая медленную загрузку реестра

echo [Arena Manager Optimization] Оптимизация ComfyUI-Manager...

REM Создаем конфигурацию для отключения автообновлений
set CONFIG_DIR=C:\ComfyUI\user\default\ComfyUI-Manager
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"

REM Создаем конфигурацию
echo [ComfyUI-Manager] > "%CONFIG_DIR%\config.ini"
echo network_mode = offline >> "%CONFIG_DIR%\config.ini"
echo auto_update = false >> "%CONFIG_DIR%\config.ini"
echo cache_update_interval = 0 >> "%CONFIG_DIR%\config.ini"
echo disable_auto_install = true >> "%CONFIG_DIR%\config.ini"

echo [Arena Manager Optimization] Конфигурация создана:
echo - network_mode = offline
echo - auto_update = false  
echo - cache_update_interval = 0
echo - disable_auto_install = true

echo [Arena Manager Optimization] Готово! Перезапустите ComfyUI для применения изменений.
pause


