# Arena Workflow Analyzer Sync Script
# Synchronizes JavaScript extension with ComfyUI Desktop

Write-Host "Arena Workflow Analyzer Sync Script" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Paths
$sourceDir = "web\extensions"
$targetDir = "c:\Users\acherednikov\AppData\Local\Programs\@comfyorgcomfyui-electron\resources\ComfyUI\web\extensions\arena"

# Check source directory exists
if (-not (Test-Path $sourceDir)) {
    Write-Host "Source directory not found: $sourceDir" -ForegroundColor Red
    exit 1
}

# Create target directory if not exists
if (-not (Test-Path $targetDir)) {
    Write-Host "Creating target directory: $targetDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
}

# Sync files
Write-Host "Syncing JavaScript extensions..." -ForegroundColor Cyan

# arena_workflow_analyzer.js
$sourceFile = "$sourceDir\arena_workflow_analyzer.js"
$targetFile = "$targetDir\arena_workflow_analyzer.js"

if (Test-Path $sourceFile) {
    Copy-Item $sourceFile $targetFile -Force
    Write-Host "Copied arena_workflow_analyzer.js" -ForegroundColor Green
} else {
    Write-Host "Source file not found: $sourceFile" -ForegroundColor Red
}

# arena_autocache.js (existing)
$sourceFile2 = "$sourceDir\arena_autocache.js"
$targetFile2 = "$targetDir\arena_autocache.js"

if (Test-Path $sourceFile2) {
    Copy-Item $sourceFile2 $targetFile2 -Force
    Write-Host "Copied arena_autocache.js" -ForegroundColor Green
} else {
    Write-Host "Source file not found: $sourceFile2" -ForegroundColor Red
}

# Check result
Write-Host "`nTarget directory contents:" -ForegroundColor Cyan
Get-ChildItem $targetDir | ForEach-Object {
    Write-Host "  $($_.Name) ($($_.Length) bytes)" -ForegroundColor White
}

Write-Host "`nSync completed!" -ForegroundColor Green
Write-Host "Restart ComfyUI Desktop to load the new extensions" -ForegroundColor Yellow
