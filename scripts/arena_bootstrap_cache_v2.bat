@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "SCRIPT_NAME=%~nx0"
set "RECOMMENDED_MIN_GB=50"
set "EXIT_CODE=0"

REM Проверяем аргументы командной строки
if "%~1"=="/h" goto :help
if "%~1"=="-h" goto :help
if "%~1"=="/?" goto :help
if "%~1"=="--restore-defaults" goto :restore_defaults
if "%~1"=="--debug" goto :debug_mode
if "%~1"=="--prod" goto :prod_mode

REM Если аргументы не указаны, пробуем GUI
if "%~1"=="" if "%~2"=="" (
    call :try_gui
    if defined GUI_SUCCESS goto :after_gui
)

REM Обычный режим (совместимость)
set "CACHE_ROOT=%~1"
set "CACHE_LIMIT=%~2"
goto :normal_mode

:debug_mode
echo.
echo [Arena AutoCache Bootstrap] DEBUG MODE
echo   Настройки для диагностики: отключены фильтры, подробные логи
echo.
call :setup_debug_profile
goto :apply_settings

:prod_mode
echo.
echo [Arena AutoCache Bootstrap] PRODUCTION MODE
echo   Настройки для повседневной работы: включены фильтры
echo.
call :setup_prod_profile
goto :apply_settings

:restore_defaults
echo.
echo [Arena AutoCache Bootstrap] RESTORING DEFAULTS
echo   Возврат к безопасным настройкам по умолчанию
echo.
call :setup_default_profile
goto :apply_settings

:normal_mode
if not defined CACHE_ROOT (
    call :prompt_cache_root
)

if not defined CACHE_ROOT (
    echo.
    echo [Arena AutoCache Bootstrap]
    echo   No cache directory selected. Aborting.
    set "EXIT_CODE=1"
    goto :finish
)

for %%I in ("%CACHE_ROOT%") do set "CACHE_ROOT=%%~fI"

if not exist "%CACHE_ROOT%" (
    echo.
    echo Creating cache directory: "%CACHE_ROOT%"
    mkdir "%CACHE_ROOT%" >nul 2>&1
    if errorlevel 1 (
        echo Failed to create directory "%CACHE_ROOT%".
        set "EXIT_CODE=1"
        goto :finish
    )
)

if not defined CACHE_LIMIT (
    call :prompt_cache_limit
)

if not defined CACHE_LIMIT (
    echo.
    echo [Arena AutoCache Bootstrap]
    echo   Cache size limit not provided. Aborting.
    set "EXIT_CODE=1"
    goto :finish
)

call :sanitize_limit CACHE_LIMIT "%CACHE_LIMIT%"
if errorlevel 1 (
    set "EXIT_CODE=1"
    goto :finish
)

REM Настройки для обычного режима (совместимость)
set ARENA_CACHE_ROOT=%CACHE_ROOT%
set ARENA_CACHE_MAX_GB=%CACHE_LIMIT%
set "ARENA_CACHE_ENABLE=1"
set "ARENA_CACHE_VERBOSE=0"
set "ARENA_CACHE_MIN_SIZE_GB=1.0"
set "ARENA_CACHE_SKIP_HARDCODED=1"

goto :apply_settings

:setup_debug_profile
REM Debug профиль: отключены фильтры, подробные логи
if not defined CACHE_ROOT (
    call :prompt_cache_root
)
if not defined CACHE_LIMIT (
    call :prompt_cache_limit
)

set ARENA_CACHE_ROOT=%CACHE_ROOT%
set ARENA_CACHE_MAX_GB=%CACHE_LIMIT%
set "ARENA_CACHE_ENABLE=1"
set "ARENA_CACHE_VERBOSE=1"
set "ARENA_CACHE_MIN_SIZE_GB=0.0"
set "ARENA_CACHE_SKIP_HARDCODED=0"
goto :eof

:setup_prod_profile
REM Prod профиль: включены фильтры, обычные логи
if not defined CACHE_ROOT (
    call :prompt_cache_root
)
if not defined CACHE_LIMIT (
    call :prompt_cache_limit
)

set ARENA_CACHE_ROOT=%CACHE_ROOT%
set ARENA_CACHE_MAX_GB=%CACHE_LIMIT%
set "ARENA_CACHE_ENABLE=1"
set "ARENA_CACHE_VERBOSE=0"
set "ARENA_CACHE_MIN_SIZE_GB=1.0"
set "ARENA_CACHE_SKIP_HARDCODED=0"
goto :eof

:setup_default_profile
REM Дефолтный профиль: безопасные настройки
if not defined CACHE_ROOT (
    call :prompt_cache_root
)
if not defined CACHE_LIMIT (
    call :prompt_cache_limit
)

set ARENA_CACHE_ROOT=%CACHE_ROOT%
set ARENA_CACHE_MAX_GB=%CACHE_LIMIT%
set "ARENA_CACHE_ENABLE=1"
set "ARENA_CACHE_VERBOSE=0"
set "ARENA_CACHE_MIN_SIZE_GB=1.0"
set "ARENA_CACHE_SKIP_HARDCODED=1"
goto :eof

:apply_settings
REM Проверяем доступность NAS
call :check_nas_availability

REM Проверяем права на папку кеша
call :check_cache_permissions

REM Показываем текущие настройки
call :show_current_settings

REM Применяем настройки
set "PERSIST_SUCCESS="
call :persist_variable ARENA_CACHE_ROOT "%ARENA_CACHE_ROOT%"
call :persist_variable ARENA_CACHE_MAX_GB "%ARENA_CACHE_MAX_GB%"
call :persist_variable ARENA_CACHE_ENABLE "%ARENA_CACHE_ENABLE%"
call :persist_variable ARENA_CACHE_VERBOSE "%ARENA_CACHE_VERBOSE%"
call :persist_variable ARENA_CACHE_MIN_SIZE_GB "%ARENA_CACHE_MIN_SIZE_GB%"
call :persist_variable ARENA_CACHE_SKIP_HARDCODED "%ARENA_CACHE_SKIP_HARDCODED%"

if not defined PERSIST_SUCCESS (
    echo.
    echo [Arena AutoCache Bootstrap]
    echo   Failed to persist one or more variables with SETX.
    echo   Check the output above and rerun the script if needed.
) else (
    echo.
    echo [Arena AutoCache Bootstrap]
    echo   Persistent user variables updated via SETX.
)

echo.
echo Current session variables:
echo   ARENA_CACHE_ROOT=%ARENA_CACHE_ROOT%
echo   ARENA_CACHE_MAX_GB=%ARENA_CACHE_MAX_GB% GiB
echo   ARENA_CACHE_ENABLE=%ARENA_CACHE_ENABLE%
echo   ARENA_CACHE_VERBOSE=%ARENA_CACHE_VERBOSE%
echo   ARENA_CACHE_MIN_SIZE_GB=%ARENA_CACHE_MIN_SIZE_GB% GB
echo   ARENA_CACHE_SKIP_HARDCODED=%ARENA_CACHE_SKIP_HARDCODED%

echo.
echo You can now start ComfyUI in this window or open a new terminal.
echo This bootstrap script only needs to run once after installation.

REM Показываем быстрые подсказки
call :show_quick_tips

goto :finish

:check_nas_availability
echo.
echo [Arena AutoCache Bootstrap] Checking NAS availability...
ping -n 1 nas-3d >nul 2>&1
if errorlevel 1 (
    echo   ⚠️  NAS offline - caching will use local sources only
    echo   This is normal if you're not connected to the network.
) else (
    echo   ✅ NAS is accessible
)
goto :eof

:check_cache_permissions
echo.
echo [Arena AutoCache Bootstrap] Checking cache directory permissions...
if not exist "%ARENA_CACHE_ROOT%" (
    echo   Creating cache directory: "%ARENA_CACHE_ROOT%"
    mkdir "%ARENA_CACHE_ROOT%" >nul 2>&1
    if errorlevel 1 (
        echo   ❌ Failed to create directory "%ARENA_CACHE_ROOT%"
        echo   Please check permissions or choose a different location.
        set "EXIT_CODE=1"
        goto :finish
    )
)

REM Проверяем права на запись
echo test > "%ARENA_CACHE_ROOT%\test_write.tmp" 2>nul
if errorlevel 1 (
    echo   ❌ No write permission to "%ARENA_CACHE_ROOT%"
    echo   Please check permissions or choose a different location.
    set "EXIT_CODE=1"
    goto :finish
) else (
    del "%ARENA_CACHE_ROOT%\test_write.tmp" >nul 2>&1
    echo   ✅ Cache directory is writable
)
goto :eof

:show_current_settings
echo.
echo [Arena AutoCache Bootstrap] Current settings:
echo   📁 Cache directory: %ARENA_CACHE_ROOT%
echo   📏 Cache limit: %ARENA_CACHE_MAX_GB% GiB
echo   🔧 Enable cache: %ARENA_CACHE_ENABLE%
echo   📝 Verbose logs: %ARENA_CACHE_VERBOSE%
echo   📏 Min size filter: %ARENA_CACHE_MIN_SIZE_GB% GB
echo   🚫 Skip hardcoded paths: %ARENA_CACHE_SKIP_HARDCODED%
goto :eof

:show_quick_tips
echo.
echo [Arena AutoCache Bootstrap] Quick tips:
echo   • If you see "copy_skipped (hardcoded path detected)" in Smart node:
echo     Check ARENA_CACHE_SKIP_HARDCODED=0 and restart ComfyUI
echo   • For cache testing use Smart/OPS in audit_then_warmup mode
echo   • Monitor progress in Copy Status node
echo   • Check comfyui.log for detailed information
echo   • Use --debug mode for troubleshooting
echo   • Use --prod mode for daily work
echo   • Use --restore-defaults to reset to safe settings
goto :eof

:after_gui
echo.
echo [Arena AutoCache Bootstrap]
echo   Settings applied via the WinForms helper.
echo   Restart terminal windows to load the persisted variables.
set "EXIT_CODE=0"
goto :finish

:prompt_cache_root
echo.
echo [Arena AutoCache Bootstrap]
echo   Choose the SSD directory where Arena AutoCache will store data.
echo   Enter a path manually or leave empty to use the Windows folder picker.
set "CACHE_ROOT_INPUT="
set /p "CACHE_ROOT_INPUT=Cache directory: "
if defined CACHE_ROOT_INPUT (
    set "CACHE_ROOT=%CACHE_ROOT_INPUT%"
    goto :eof
)
for /f "delims=" %%I in ('powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description = 'Select Arena AutoCache folder'; $dialog.ShowNewFolderButton = $true; if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $dialog.SelectedPath }"') do (
    set "CACHE_ROOT=%%~I"
    goto :eof
)
echo.
echo No directory selected. Please try again.
goto :prompt_cache_root

:prompt_cache_limit
echo.
echo [Arena AutoCache Bootstrap]
echo   Specify the desired cache size limit in GiB.
echo   Minimum recommended value: %RECOMMENDED_MIN_GB% GiB.
set "CACHE_LIMIT=%RECOMMENDED_MIN_GB%"
set "CACHE_LIMIT_INPUT="
set /p "CACHE_LIMIT_INPUT=Cache limit [GiB, Enter for %RECOMMENDED_MIN_GB%]: "
if defined CACHE_LIMIT_INPUT set "CACHE_LIMIT=%CACHE_LIMIT_INPUT%"
goto :eof

:sanitize_limit
set "LIMIT_VAR=%~1"
set "LIMIT_VALUE="
for /f "tokens=*" %%I in ("%~2") do set "LIMIT_VALUE=%%~I"
set "LIMIT_VALUE=%LIMIT_VALUE: =%"
set "LIMIT_VALUE=%LIMIT_VALUE:"=%"
set "LIMIT_TEST="
set /a LIMIT_TEST=%LIMIT_VALUE% >nul 2>&1
if errorlevel 1 (
    echo.
    echo Invalid cache size value: %LIMIT_VALUE%
    echo Please enter a positive integer (GiB).
    exit /b 1
)
if not defined LIMIT_TEST (
    echo.
    echo Invalid cache size value: %LIMIT_VALUE%
    exit /b 1
)
if !LIMIT_TEST! LEQ 0 (
    echo.
    echo Cache limit must be greater than zero.
    exit /b 1
)
set "%LIMIT_VAR%=%LIMIT_TEST%"
exit /b 0

:persist_variable
set "VAR_NAME=%~1"
set "VAR_VALUE=%~2"
if not defined VAR_NAME exit /b 0
set "VAR_ESCAPED=%VAR_VALUE%"
if defined VAR_ESCAPED (
    if "%VAR_ESCAPED:~-1%"=="\" set "VAR_ESCAPED=%VAR_ESCAPED%\"
)
setx "%VAR_NAME%" "%VAR_ESCAPED%" >nul
if errorlevel 1 (
    echo Failed to persist %VAR_NAME% with SETX.
) else (
    set "PERSIST_SUCCESS=1"
)
exit /b 0

:try_gui
set "GUI_SUCCESS="
set "POWERSHELL_PATH="
for %%P in (powershell.exe) do set "POWERSHELL_PATH=%%~$PATH:P"
if not defined POWERSHELL_PATH exit /b 0
set "PS1=%~dp0arena_bootstrap_cache.ps1"
if not exist "%PS1%" exit /b 0
set "GUI_EXPORTS=%TEMP%\arena_bootstrap_cache_%RANDOM%%RANDOM%.tmp"
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%" > "%GUI_EXPORTS%"
set "PS_EXIT=%ERRORLEVEL%"
if not "%PS_EXIT%"=="0" (
    del "%GUI_EXPORTS%" >nul 2>&1
    exit /b 0
)
for /f "usebackq tokens=1* delims= " %%A in ("%GUI_EXPORTS%") do (
    if /I "%%A"=="EXPORT" (
        for /f "tokens=1* delims==" %%B in ("%%B") do (
            if not "%%B"=="" (
                set "VAR_NAME=%%B"
                set "VAR_VALUE=%%C"
                set %%B=%%C
                if /I "%%B"=="ARENA_CACHE_ROOT" set "CACHE_ROOT=%%C"
                if /I "%%B"=="ARENA_CACHE_MAX_GB" set "CACHE_LIMIT=%%C"
                set "GUI_SUCCESS=1"
            )
        )
    )
)
del "%GUI_EXPORTS%" >nul 2>&1
exit /b 0

:help
echo [Arena AutoCache Bootstrap]
echo.
echo One-time configuration helper for Arena AutoCache on Windows.
echo It stores ARENA_CACHE_* variables as persistent user values.
echo.
echo Usage:
echo   %SCRIPT_NAME% [mode] [cache_dir] [max_gib]
echo.
echo Modes:
echo   --debug           Debug mode: disabled filters, verbose logs
echo   --prod            Production mode: enabled filters, normal logs
echo   --restore-defaults Restore safe default settings
echo   (no mode)         Interactive mode with prompts
echo.
echo Examples:
echo   %SCRIPT_NAME% --debug
echo   %SCRIPT_NAME% --prod
echo   %SCRIPT_NAME% --restore-defaults
echo   %SCRIPT_NAME% C:\Cache 100
echo.
echo Recommended minimum limit: %RECOMMENDED_MIN_GB% GiB.
echo.
echo After running, launch ComfyUI from the same window or any new terminal.
goto :finish

:finish
set "FINAL_EXIT=%EXIT_CODE%"
if defined ARENA_CACHE_ROOT (set "FINAL_ROOT=%ARENA_CACHE_ROOT%") else set "FINAL_ROOT=__ARENA_UNDEFINED__"
if defined ARENA_CACHE_MAX_GB (set "FINAL_MAX=%ARENA_CACHE_MAX_GB%") else set "FINAL_MAX=__ARENA_UNDEFINED__"
if defined ARENA_CACHE_ENABLE (set "FINAL_ENABLE=%ARENA_CACHE_ENABLE%") else set "FINAL_ENABLE=__ARENA_UNDEFINED__"
if defined ARENA_CACHE_VERBOSE (set "FINAL_VERBOSE=%ARENA_CACHE_VERBOSE%") else set "FINAL_VERBOSE=__ARENA_UNDEFINED__"
if defined ARENA_CACHE_MIN_SIZE_GB (set "FINAL_MIN_SIZE=%ARENA_CACHE_MIN_SIZE_GB%") else set "FINAL_MIN_SIZE=__ARENA_UNDEFINED__"
if defined ARENA_CACHE_SKIP_HARDCODED (set "FINAL_SKIP_HARDCODED=%ARENA_CACHE_SKIP_HARDCODED%") else set "FINAL_SKIP_HARDCODED=__ARENA_UNDEFINED__"
endlocal & (
    if not "%FINAL_ROOT%"=="__ARENA_UNDEFINED__" set "ARENA_CACHE_ROOT=%FINAL_ROOT%"
    if not "%FINAL_MAX%"=="__ARENA_UNDEFINED__" set "ARENA_CACHE_MAX_GB=%FINAL_MAX%"
    if not "%FINAL_ENABLE%"=="__ARENA_UNDEFINED__" set "ARENA_CACHE_ENABLE=%FINAL_ENABLE%"
    if not "%FINAL_VERBOSE%"=="__ARENA_UNDEFINED__" set "ARENA_CACHE_VERBOSE=%FINAL_VERBOSE%"
    if not "%FINAL_MIN_SIZE%"=="__ARENA_UNDEFINED__" set "ARENA_CACHE_MIN_SIZE_GB=%FINAL_MIN_SIZE%"
    if not "%FINAL_SKIP_HARDCODED%"=="__ARENA_UNDEFINED__" set "ARENA_CACHE_SKIP_HARDCODED=%FINAL_SKIP_HARDCODED%"
)
exit /b %FINAL_EXIT%
