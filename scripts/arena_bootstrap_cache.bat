@echo off
set "SCRIPT_NAME=%~nx0"
set "RECOMMENDED_MIN_GB=50"

if "%~1"=="/h" goto :help
if "%~1"=="-h" goto :help
if "%~1"=="/?" goto :help

set "CACHE_ROOT=%~1"
set "CACHE_LIMIT=%~2"

if not defined CACHE_ROOT (
    call :prompt_cache_root
)

if not defined CACHE_ROOT (
    echo.
    echo [Arena AutoCache Bootstrap]
    echo   No cache directory selected. Aborting.
    goto :fail
)

for %%I in ("%CACHE_ROOT%") do set "CACHE_ROOT=%%~fI"

if not exist "%CACHE_ROOT%" (
    echo.
    echo Creating cache directory: "%CACHE_ROOT%"
    mkdir "%CACHE_ROOT%" >nul 2>&1
    if errorlevel 1 (
        echo Failed to create directory "%CACHE_ROOT%".
        goto :fail
    )
)

if not defined CACHE_LIMIT (
    call :prompt_cache_limit
)

if not defined CACHE_LIMIT (
    echo.
    echo [Arena AutoCache Bootstrap]
    echo   Cache size limit not provided. Aborting.
    goto :fail
)

call :sanitize_limit CACHE_LIMIT "%CACHE_LIMIT%"
if errorlevel 1 goto :fail

set "ARENA_CACHE_ROOT=%CACHE_ROOT%"
set "ARENA_CACHE_MAX_GB=%CACHE_LIMIT%"
set "ARENA_CACHE_ENABLE=1"
set "ARENA_CACHE_VERBOSE=0"

set "PERSIST_SUCCESS="
call :persist_variable ARENA_CACHE_ROOT "%ARENA_CACHE_ROOT%"
call :persist_variable ARENA_CACHE_MAX_GB "%ARENA_CACHE_MAX_GB%"
call :persist_variable ARENA_CACHE_ENABLE "%ARENA_CACHE_ENABLE%"
call :persist_variable ARENA_CACHE_VERBOSE "%ARENA_CACHE_VERBOSE%"

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

echo.
echo You can now start ComfyUI in this window or open a new terminal.
echo This bootstrap script only needs to run once after installation.

goto :eof

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
set /a LIMIT_TEST=%LIMIT_VALUE% >nul 2>&1
if errorlevel 1 (
    echo.
    echo Invalid cache size value: %LIMIT_VALUE%
    echo Please enter a positive integer (GiB).
    exit /b 1
)
if %LIMIT_TEST% LEQ 0 (
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
setx "%VAR_NAME%" "%VAR_VALUE%" >nul
if errorlevel 1 (
    echo Failed to persist %VAR_NAME% with SETX.
) else (
    set "PERSIST_SUCCESS=1"
)
exit /b 0

:help
echo [Arena AutoCache Bootstrap]
echo.
echo One-time configuration helper for Arena AutoCache on Windows.
echo It stores ARENA_CACHE_* variables as persistent user values.
echo.
echo Usage:
echo   %SCRIPT_NAME% ^<cache_dir^> ^<max_gib^>
echo.
echo If arguments are omitted the script will prompt for them.
echo Recommended minimum limit: %RECOMMENDED_MIN_GB% GiB.
echo.
echo After running, launch ComfyUI from the same window or any new terminal.
goto :eof

:fail
exit /b 1
