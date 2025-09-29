@echo off
REM Arena Fast Start - ComfyUI без тяжелых модулей
REM Ускоряет старт ComfyUI, отключая проблемные custom nodes

echo [Arena Fast Start] Настройка быстрого старта ComfyUI...

REM Создаем временную папку для отключенных модулей
if not exist "C:\ComfyUI\custom_nodes\DISABLED" mkdir "C:\ComfyUI\custom_nodes\DISABLED"

REM Отключаем тяжелые модули
echo [Arena Fast Start] Отключаем тяжелые модули...

REM ComfyUI-3D-Pack (проблемный)
if exist "C:\ComfyUI\custom_nodes\ComfyUI-3D-Pack" (
    move "C:\ComfyUI\custom_nodes\ComfyUI-3D-Pack" "C:\ComfyUI\custom_nodes\DISABLED\ComfyUI-3D-Pack"
    echo [Arena Fast Start] Отключен ComfyUI-3D-Pack
)

REM ComfyUI-Copilot (медленный)
if exist "C:\ComfyUI\custom_nodes\ComfyUI-Copilot" (
    move "C:\ComfyUI\custom_nodes\ComfyUI-Copilot" "C:\ComfyUI\custom_nodes\DISABLED\ComfyUI-Copilot"
    echo [Arena Fast Start] Отключен ComfyUI-Copilot
)

REM was-node-suite-comfyui (медленный)
if exist "C:\ComfyUI\custom_nodes\was-node-suite-comfyui" (
    move "C:\ComfyUI\custom_nodes\was-node-suite-comfyui" "C:\ComfyUI\custom_nodes\DISABLED\was-node-suite-comfyui"
    echo [Arena Fast Start] Отключен was-node-suite-comfyui
)

REM comfyui-mixlab-nodes (медленный)
if exist "C:\ComfyUI\custom_nodes\comfyui-mixlab-nodes" (
    move "C:\ComfyUI\custom_nodes\comfyui-mixlab-nodes" "C:\ComfyUI\custom_nodes\DISABLED\comfyui-mixlab-nodes"
    echo [Arena Fast Start] Отключен comfyui-mixlab-nodes
)

echo [Arena Fast Start] Запуск ComfyUI...
cd /d "C:\ComfyUI"
python main.py

echo [Arena Fast Start] Восстановление модулей...

REM Восстанавливаем модули
if exist "C:\ComfyUI\custom_nodes\DISABLED\ComfyUI-3D-Pack" (
    move "C:\ComfyUI\custom_nodes\DISABLED\ComfyUI-3D-Pack" "C:\ComfyUI\custom_nodes\ComfyUI-3D-Pack"
)

if exist "C:\ComfyUI\custom_nodes\DISABLED\ComfyUI-Copilot" (
    move "C:\ComfyUI\custom_nodes\DISABLED\ComfyUI-Copilot" "C:\ComfyUI\custom_nodes\ComfyUI-Copilot"
)

if exist "C:\ComfyUI\custom_nodes\DISABLED\was-node-suite-comfyui" (
    move "C:\ComfyUI\custom_nodes\DISABLED\was-node-suite-comfyui" "C:\ComfyUI\custom_nodes\was-node-suite-comfyui"
)

if exist "C:\ComfyUI\custom_nodes\DISABLED\comfyui-mixlab-nodes" (
    move "C:\ComfyUI\custom_nodes\DISABLED\comfyui-mixlab-nodes" "C:\ComfyUI\custom_nodes\comfyui-mixlab-nodes"
)

echo [Arena Fast Start] Готово!
pause


