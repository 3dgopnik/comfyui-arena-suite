# Sync JavaScript files from development to production
# Usage: powershell -ExecutionPolicy Bypass -File sync_js_files.ps1

$devPath = "C:\ComfyUI\custom_nodes\ComfyUI-Arena\web\extensions\"
$prodPath = "C:\Users\acherednikov\AppData\Local\Programs\@comfyorgcomfyui-electron\resources\ComfyUI\web\extensions\arena\"

Write-Host "Syncing JavaScript files from development to production..."
Write-Host "Source: $devPath"
Write-Host "Destination: $prodPath"

# Create destination directory if it doesn't exist
if (!(Test-Path $prodPath)) {
    New-Item -ItemType Directory -Path $prodPath -Force
    Write-Host "Created destination directory: $prodPath"
}

# Copy JavaScript files
$jsFiles = @("arena_autocache.js", "arena_workflow_analyzer.js", "arena_simple_header.js", "arena_settings_panel.js")

foreach ($file in $jsFiles) {
    $sourceFile = Join-Path $devPath $file
    $destFile = Join-Path $prodPath $file
    
    if (Test-Path $sourceFile) {
        Copy-Item $sourceFile -Destination $destFile -Force
        Write-Host "Copied $file"
    } else {
        Write-Host "Source file not found: $sourceFile"
    }
}

Write-Host "JavaScript files sync completed!"
Write-Host "Restart ComfyUI to load updated files."