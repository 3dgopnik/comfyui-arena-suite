# Скрипт синхронизации JavaScript файлов для ComfyUI Desktop
# Запускать после каждого изменения JavaScript файлов

param(
    [switch]$Force,
    [switch]$Verbose
)

$sourceDir = "C:\ComfyUI\custom_nodes\ComfyUI-Arena\web\"
$targetDir = "C:\Users\acherednikov\AppData\Local\Programs\@comfyorgcomfyui-electron\resources\ComfyUI\custom_nodes\ComfyUI-Arena\web\"
$extDir    = "C:\Users\acherednikov\AppData\Local\Programs\@comfyorgcomfyui-electron\resources\ComfyUI\web\extensions\ComfyUI-Arena\"

Write-Host "🔄 Синхронизация JavaScript файлов для ComfyUI Desktop..." -ForegroundColor Cyan

# Проверяем существование папки разработки
if (!(Test-Path $sourceDir)) {
    Write-Host "❌ Папка разработки не найдена: $sourceDir" -ForegroundColor Red
    Write-Host "Убедитесь, что вы находитесь в правильной директории проекта." -ForegroundColor Yellow
    exit 1
}

# Создаем папку назначения если не существует
if (!(Test-Path $targetDir)) {
    Write-Host "📁 Создаем папку назначения: $targetDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Write-Host "✅ Папка назначения создана" -ForegroundColor Green
}

# Создаем папку расширений Electron если не существует (молчаливо)
if (!(Test-Path $extDir)) {
    Write-Host "📁 Создаем папку Electron extensions: $extDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $extDir -Force | Out-Null
    Write-Host "✅ Папка Electron extensions создана" -ForegroundColor Green
}

# Получаем список JavaScript файлов в папке разработки
$jsFiles = Get-ChildItem $sourceDir -Filter "*.js" -File
if ($jsFiles.Count -eq 0) {
    Write-Host "❌ JavaScript файлы не найдены в папке разработки" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Найдено JavaScript файлов: $($jsFiles.Count)" -ForegroundColor Green

# Синхронизируем каждый файл
$syncedCount = 0
$skippedCount = 0

foreach ($file in $jsFiles) {
    $sourcePath = $file.FullName
    $targetPath = Join-Path $targetDir $file.Name
    
    $shouldCopy = $Force
    
    if (!$Force) {
        # Проверяем нужно ли копировать файл
        if (!(Test-Path $targetPath)) {
            $shouldCopy = $true
        } else {
            $sourceHash = (Get-FileHash $sourcePath -Algorithm MD5).Hash
            $targetHash = (Get-FileHash $targetPath -Algorithm MD5).Hash
            $shouldCopy = ($sourceHash -ne $targetHash)
        }
    }
    
    if ($shouldCopy) {
        try {
            Copy-Item $sourcePath $targetPath -Force
            $syncedCount++
            if ($Verbose) {
                Write-Host "  ✅ Синхронизирован: $($file.Name)" -ForegroundColor Green
            }
        } catch {
            Write-Host "  ❌ Ошибка при копировании $($file.Name): $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        $skippedCount++
        if ($Verbose) {
            Write-Host "  ⏭️ Пропущен (без изменений): $($file.Name)" -ForegroundColor Gray
        }
    }
}

Write-Host ""
Write-Host "📊 Результаты синхронизации (custom_nodes/web):" -ForegroundColor Cyan
Write-Host "  ✅ Синхронизировано: $syncedCount файлов" -ForegroundColor Green
Write-Host "  ⏭️ Пропущено: $skippedCount файлов" -ForegroundColor Gray

# Дополнительно: чистим старые arena_settings_* в Electron custom_nodes и extensions, копируем актуальный save_button
try {
    # 1) ComfyUI/custom_nodes/ComfyUI-Arena/web
    if (Test-Path $targetDir) {
        Write-Host "\n🧹 Чистка Electron custom_nodes: $targetDir" -ForegroundColor Cyan
        $disabledDir1 = Join-Path $targetDir "_disabled"
        if (!(Test-Path $disabledDir1)) { New-Item -ItemType Directory -Path $disabledDir1 -Force | Out-Null }

        $tgtFiles = Get-ChildItem $targetDir -Filter "arena_settings_*.js" -File
        foreach ($f in $tgtFiles) {
            if ($f.Name -ne "arena_settings_save_button.js") {
                Move-Item $f.FullName (Join-Path $disabledDir1 $f.Name) -Force
                Write-Host "  ↪️ Перемещён в _disabled: $($f.Name)" -ForegroundColor Yellow
            }
        }
        $srcSave = Join-Path $sourceDir "arena_settings_save_button.js"
        if (Test-Path $srcSave) {
            Copy-Item $srcSave (Join-Path $targetDir "arena_settings_save_button.js") -Force
            Write-Host "  ✅ Обновлён (custom_nodes): arena_settings_save_button.js" -ForegroundColor Green
        }
    }

    # 2) ComfyUI/web/extensions/ComfyUI-Arena
    if (Test-Path $extDir) {
        Write-Host "\n🧹 Чистка Electron extensions: $extDir" -ForegroundColor Cyan
        $disabledDir2 = Join-Path $extDir "_disabled"
        if (!(Test-Path $disabledDir2)) { New-Item -ItemType Directory -Path $disabledDir2 -Force | Out-Null }

        $extFiles = Get-ChildItem $extDir -Filter "arena_settings_*.js" -File
        foreach ($f in $extFiles) {
            if ($f.Name -ne "arena_settings_save_button.js") {
                Move-Item $f.FullName (Join-Path $disabledDir2 $f.Name) -Force
                Write-Host "  ↪️ Перемещён в _disabled: $($f.Name)" -ForegroundColor Yellow
            }
        }

        $srcSave = Join-Path $sourceDir "arena_settings_save_button.js"
        if (Test-Path $srcSave) {
            Copy-Item $srcSave (Join-Path $extDir "arena_settings_save_button.js") -Force
            Write-Host "  ✅ Обновлён (extensions): arena_settings_save_button.js" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️ Не найден исходник arena_settings_save_button.js: $srcSave" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "  ❌ Ошибка при обновлении Electron путей: $($_.Exception.Message)" -ForegroundColor Red
}

if ($syncedCount -gt 0) {
    Write-Host ""
    Write-Host "🎉 Синхронизация завершена!" -ForegroundColor Green
    Write-Host "🔄 Перезапустите ComfyUI Desktop для применения изменений" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "ℹ️ Все файлы уже синхронизированы" -ForegroundColor Blue
}

Write-Host ""
Write-Host "💡 Использование:" -ForegroundColor Cyan
Write-Host "  .\scripts\sync_js_files.ps1 -Force    # Принудительная синхронизация всех файлов"
Write-Host "  .\scripts\sync_js_files.ps1 -Verbose  # Подробный вывод"