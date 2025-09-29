# Check development setup for ComfyUI Arena Suite
# Run this script to verify all development tools are properly configured

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ComfyUI Arena Suite - Development Setup Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$checks = @(
    @{Name="Python version"; Command="python --version"; ErrorMsg="Python not found!"},
    @{Name="Virtual environment"; Check=".venv\Scripts\activate.bat"; WarningMsg="Virtual environment not found. Run: python -m venv .venv"},
    @{Name="Development dependencies"; Command="python -c `"import ruff, mypy, pytest, pre_commit`""; WarningMsg="Some development dependencies missing. Run: pip install -r requirements-dev.txt"},
    @{Name="Cursor rules"; Check=".cursor\rules\00-process.mdc"; ErrorMsg="Cursor rules not found!"},
    @{Name="Ruff configuration"; Command="ruff check --version"; ErrorMsg="Ruff not found!"},
    @{Name="MyPy configuration"; Command="mypy --version"; ErrorMsg="MyPy not found!"},
    @{Name="Pytest configuration"; Command="pytest --version"; ErrorMsg="Pytest not found!"},
    @{Name="Pre-commit configuration"; Check=".pre-commit-config.yaml"; ErrorMsg="Pre-commit configuration not found!"}
)

$successCount = 0
$totalChecks = $checks.Count

foreach ($i in 0..($checks.Count - 1)) {
    $check = $checks[$i]
    $stepNum = $i + 1
    
    Write-Host "[$stepNum/$totalChecks] Checking $($check.Name)..." -ForegroundColor Yellow
    
    if ($check.Check) {
        # File/directory check
        if (Test-Path $check.Check) {
            Write-Host "✓ $($check.Name) found" -ForegroundColor Green
            $successCount++
        } else {
            if ($check.WarningMsg) {
                Write-Host "⚠ WARNING: $($check.WarningMsg)" -ForegroundColor Yellow
                $successCount++
            } else {
                Write-Host "✗ ERROR: $($check.ErrorMsg)" -ForegroundColor Red
            }
        }
    } else {
        # Command check
        try {
            $null = Invoke-Expression $check.Command 2>$null
            Write-Host "✓ $($check.Name) OK" -ForegroundColor Green
            $successCount++
        } catch {
            if ($check.WarningMsg) {
                Write-Host "⚠ WARNING: $($check.WarningMsg)" -ForegroundColor Yellow
                $successCount++
            } else {
                Write-Host "✗ ERROR: $($check.ErrorMsg)" -ForegroundColor Red
            }
        }
    }
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Development setup check completed!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Results: $successCount/$totalChecks checks passed" -ForegroundColor $(if ($successCount -eq $totalChecks) { "Green" } else { "Yellow" })
Write-Host ""

if ($successCount -eq $totalChecks) {
    Write-Host "✓ All checks passed! Development environment is ready." -ForegroundColor Green
} else {
    Write-Host "⚠ Some checks failed. Please review the warnings above." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Activate virtual environment: .venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "2. Install dependencies: pip install -r requirements-dev.txt" -ForegroundColor White
Write-Host "3. Install pre-commit hooks: pre-commit install" -ForegroundColor White
Write-Host "4. Run tests: pytest" -ForegroundColor White
Write-Host "5. Check code quality: ruff check . && mypy ." -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to continue"
