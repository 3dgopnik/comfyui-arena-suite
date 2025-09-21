@echo off
set "SCRIPT_NAME=%~nx0"

if "%~1"=="/h" goto :help
if "%~1"=="-h" goto :help
if "%~1"=="/?" goto :help

set "CACHE_ROOT=%~1"
if not defined CACHE_ROOT (
    call :select_cache_root
)
if not defined CACHE_ROOT (
    if defined ARENA_CACHE_ROOT (
        set "CACHE_ROOT=%ARENA_CACHE_ROOT%"
    ) else if defined LOCALAPPDATA (
        set "CACHE_ROOT=%LOCALAPPDATA%\ArenaAutoCache"
    ) else (
        for %%I in ("%~dp0..\ArenaAutoCache") do set "CACHE_ROOT=%%~fI"
    )
)

for %%I in ("%CACHE_ROOT%") do set "CACHE_ROOT=%%~fI"
set "ARENA_CACHE_ROOT=%CACHE_ROOT%"

if "%~2"=="" (
    if not defined ARENA_CACHE_ENABLE set "ARENA_CACHE_ENABLE=1"
) else (
    set "ARENA_CACHE_ENABLE=%~2"
)

if "%~3"=="" (
    if not defined ARENA_CACHE_VERBOSE set "ARENA_CACHE_VERBOSE=0"
) else (
    set "ARENA_CACHE_VERBOSE=%~3"
)

echo.
echo [Arena AutoCache]
echo   ARENA_CACHE_ROOT=%ARENA_CACHE_ROOT%
if defined ARENA_CACHE_ENABLE echo   ARENA_CACHE_ENABLE=%ARENA_CACHE_ENABLE%
if defined ARENA_CACHE_VERBOSE echo   ARENA_CACHE_VERBOSE=%ARENA_CACHE_VERBOSE%
echo.
echo Use "call %SCRIPT_NAME% <cache_dir> [enable] [verbose]" from CMD to persist variables.

goto :eof

:select_cache_root
for /f "delims=" %%I in ('powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $dialog.Description = 'Select Arena AutoCache folder'; $dialog.ShowNewFolderButton = $true; if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $dialog.SelectedPath }"') do (
    set "CACHE_ROOT=%%~I"
    goto :select_cache_root_done
)
goto :eof

:select_cache_root_done
goto :eof

:help
echo Sets Arena AutoCache environment variables in the current CMD session.
echo.
echo Usage:
echo   call %SCRIPT_NAME% ^<cache_dir^> [enable] [verbose]
echo.
echo Examples:
echo   call %SCRIPT_NAME% D:\ComfyCache

echo Notes:
echo   - Invoke with CALL so the parent shell captures variables.
echo   - The default path falls back to %%LOCALAPPDATA%%\ArenaAutoCache if no argument is provided.
echo   - Existing ARENA_CACHE_* variables remain untouched unless new values are supplied.

goto :eof
