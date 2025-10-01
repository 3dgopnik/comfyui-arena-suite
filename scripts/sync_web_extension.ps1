# Arena AutoCache - Sync Web Extension to ComfyUI Desktop
# Синхронизация JavaScript расширения в ComfyUI Desktop

param(
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

# Пути из правил 40-platform-paths
$SourceDir = "c:\ComfyUI\custom_nodes\ComfyUI-Arena\web\extensions\"
$TargetDir = "c:\Users\acherednikov\AppData\Local\Programs\@comfyorgcomfyui-electron\resources\ComfyUI\web\extensions\arena\"
$AlternativeTargetDir = "c:\Users\acherednikov\AppData\Local\Programs\@comfyorgcomfyui-electron\resources\ComfyUI\web_custom_versions\desktop_app\extensions\arena\"

Write-Host "[Arena AutoCache] Синхронизация web extension..." -ForegroundColor Green

# Проверяем существование исходной папки
if (-not (Test-Path $SourceDir)) {
    Write-Error "Исходная папка не найдена: $SourceDir"
    exit 1
}

# Создаем целевую папку если не существует
if (-not (Test-Path $TargetDir)) {
    Write-Host "Создание целевой папки: $TargetDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

# Создаем альтернативную целевую папку если не существует
if (-not (Test-Path $AlternativeTargetDir)) {
    Write-Host "Создание альтернативной целевой папки: $AlternativeTargetDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $AlternativeTargetDir -Force | Out-Null
}

# Копируем файлы
try {
    # Основной путь
    Write-Host "Копирование в основной путь: $TargetDir" -ForegroundColor Cyan
    Copy-Item "$SourceDir\*" -Destination $TargetDir -Recurse -Force
    
    # Альтернативный путь
    Write-Host "Копирование в альтернативный путь: $AlternativeTargetDir" -ForegroundColor Cyan
    Copy-Item "$SourceDir\*" -Destination $AlternativeTargetDir -Recurse -Force
    
    Write-Host "✓ Синхронизация завершена успешно!" -ForegroundColor Green
    
    # Показываем что скопировалось
    Write-Host "`nСкопированные файлы:" -ForegroundColor Yellow
    Get-ChildItem $TargetDir -Recurse | ForEach-Object {
        Write-Host "  $($_.FullName.Replace($TargetDir, ''))" -ForegroundColor Gray
    }
    
} catch {
    Write-Error "Ошибка при копировании: $($_.Exception.Message)"
    exit 1
}

# Проверяем результат
Write-Host "`nПроверка результата:" -ForegroundColor Yellow
$mainFile = "$TargetDir\arena_autocache.js"
$altFile = "$AlternativeTargetDir\arena_autocache.js"

if (Test-Path $mainFile) {
    Write-Host "✓ Основной файл: $mainFile" -ForegroundColor Green
} else {
    Write-Host "✗ Основной файл не найден: $mainFile" -ForegroundColor Red
}

if (Test-Path $altFile) {
    Write-Host "✓ Альтернативный файл: $altFile" -ForegroundColor Green
} else {
    Write-Host "✗ Альтернативный файл не найден: $altFile" -ForegroundColor Red
}

Write-Host "`n[Arena AutoCache] Синхронизация завершена. Перезапустите ComfyUI Desktop для применения изменений." -ForegroundColor Green
