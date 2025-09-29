@echo off
REM Check development setup for ComfyUI Arena Suite
REM Run this script to verify all development tools are properly configured

echo ========================================
echo ComfyUI Arena Suite - Development Setup Check
echo ========================================
echo.

REM Check Python version
echo [1/8] Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    exit /b 1
)
echo.

REM Check virtual environment
echo [2/8] Checking virtual environment...
if exist ".venv\Scripts\activate.bat" (
    echo Virtual environment found: .venv
) else (
    echo WARNING: Virtual environment not found. Run: python -m venv .venv
)
echo.

REM Check development dependencies
echo [3/8] Checking development dependencies...
python -c "import ruff, mypy, pytest, pre_commit" 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Some development dependencies missing. Run: pip install -r requirements-dev.txt
) else (
    echo Development dependencies OK
)
echo.

REM Check Cursor rules
echo [4/8] Checking Cursor rules...
if exist ".cursor\rules\00-process.mdc" (
    echo Cursor rules found: .cursor\rules\
) else (
    echo ERROR: Cursor rules not found!
    exit /b 1
)
echo.

REM Check ruff configuration
echo [5/8] Checking ruff configuration...
ruff check --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Ruff not found!
    exit /b 1
) else (
    echo Ruff configuration OK
)
echo.

REM Check mypy configuration
echo [6/8] Checking mypy configuration...
mypy --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: MyPy not found!
    exit /b 1
) else (
    echo MyPy configuration OK
)
echo.

REM Check pytest configuration
echo [7/8] Checking pytest configuration...
pytest --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Pytest not found!
    exit /b 1
) else (
    echo Pytest configuration OK
)
echo.

REM Check pre-commit configuration
echo [8/8] Checking pre-commit configuration...
if exist ".pre-commit-config.yaml" (
    echo Pre-commit configuration found
    pre-commit --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo WARNING: Pre-commit not installed. Run: pre-commit install
    ) else (
        echo Pre-commit hooks OK
    )
) else (
    echo ERROR: Pre-commit configuration not found!
    exit /b 1
)
echo.

echo ========================================
echo Development setup check completed!
echo ========================================
echo.
echo Next steps:
echo 1. Activate virtual environment: .venv\Scripts\activate
echo 2. Install dependencies: pip install -r requirements-dev.txt
echo 3. Install pre-commit hooks: pre-commit install
echo 4. Run tests: pytest
echo 5. Check code quality: ruff check . && mypy .
echo.
pause
