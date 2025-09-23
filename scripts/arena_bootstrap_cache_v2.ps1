# Arena AutoCache Bootstrap v2.0 - PowerShell GUI
# Поддерживает профили Debug/Prod и расширенные настройки

param(
    [string]$Mode = "interactive",
    [string]$CacheRoot = "",
    [int]$CacheLimit = 50,
    [switch]$RestoreDefaults,
    [switch]$Debug,
    [switch]$Prod,
    [switch]$Help
)

if ($Help) {
    Write-Host "[Arena AutoCache Bootstrap] PowerShell GUI v2.0" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\arena_bootstrap_cache_v2.ps1                    # Interactive GUI"
    Write-Host "  .\arena_bootstrap_cache_v2.ps1 -Debug            # Debug mode GUI"
    Write-Host "  .\arena_bootstrap_cache_v2.ps1 -Prod             # Production mode GUI"
    Write-Host "  .\arena_bootstrap_cache_v2.ps1 -RestoreDefaults  # Restore defaults GUI"
    Write-Host ""
    Write-Host "Modes:"
    Write-Host "  Debug:  Disabled filters, verbose logs (for troubleshooting)"
    Write-Host "  Prod:   Enabled filters, normal logs (for daily work)"
    Write-Host "  Default: Safe settings (hardcoded paths skipped, 1GB min size)"
    Write-Host ""
    exit 0
}

# Определяем режим
if ($Debug) { $Mode = "debug" }
if ($Prod) { $Mode = "prod" }
if ($RestoreDefaults) { $Mode = "default" }

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "Arena AutoCache - Bootstrap v2.0"
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.MinimizeBox = $true
$form.ClientSize = New-Object System.Drawing.Size(600, 350)

# Заголовок с режимом
$lblMode = New-Object System.Windows.Forms.Label
$lblMode.Text = "Mode: $($Mode.ToUpper())"
$lblMode.AutoSize = $true
$lblMode.Location = New-Object System.Drawing.Point(12, 15)
$lblMode.Font = New-Object System.Drawing.Font("Arial", 10, [System.Drawing.FontStyle]::Bold)

# Цвет режима
switch ($Mode) {
    "debug" { $lblMode.ForeColor = [System.Drawing.Color]::Orange }
    "prod" { $lblMode.ForeColor = [System.Drawing.Color]::Green }
    "default" { $lblMode.ForeColor = [System.Drawing.Color]::Blue }
    default { $lblMode.ForeColor = [System.Drawing.Color]::Gray }
}

# Cache folder
$lblPath = New-Object System.Windows.Forms.Label
$lblPath.Text = 'Cache folder:'
$lblPath.AutoSize = $true
$lblPath.Location = New-Object System.Drawing.Point(12, 50)

$txtPath = New-Object System.Windows.Forms.TextBox
$txtPath.Location = New-Object System.Drawing.Point(110, 47)
$txtPath.Width = 400

$btnBrowse = New-Object System.Windows.Forms.Button
$btnBrowse.Text = 'Browse...'
$btnBrowse.Location = New-Object System.Drawing.Point(520, 45)
$btnBrowse.Width = 80

# Cache limit
$lblLimit = New-Object System.Windows.Forms.Label
$lblLimit.Text = 'Cache size (GiB):'
$lblLimit.AutoSize = $true
$lblLimit.Location = New-Object System.Drawing.Point(12, 85)

$numLimit = New-Object System.Windows.Forms.NumericUpDown
$numLimit.Location = New-Object System.Drawing.Point(110, 83)
$numLimit.Minimum = 1
$numLimit.Maximum = 1048576
$numLimit.Value = $CacheLimit
$numLimit.Width = 80

# Дополнительные настройки
$lblAdvanced = New-Object System.Windows.Forms.Label
$lblAdvanced.Text = 'Advanced Settings:'
$lblAdvanced.AutoSize = $true
$lblAdvanced.Location = New-Object System.Drawing.Point(12, 120)
$lblAdvanced.Font = New-Object System.Drawing.Font("Arial", 9, [System.Drawing.FontStyle]::Bold)

# Verbose logs
$chkVerbose = New-Object System.Windows.Forms.CheckBox
$chkVerbose.Text = 'Verbose logs'
$chkVerbose.AutoSize = $true
$chkVerbose.Location = New-Object System.Drawing.Point(12, 145)

# Skip hardcoded paths
$chkSkipHardcoded = New-Object System.Windows.Forms.CheckBox
$chkSkipHardcoded.Text = 'Skip hardcoded paths (NAS, etc.)'
$chkSkipHardcoded.AutoSize = $true
$chkSkipHardcoded.Location = New-Object System.Drawing.Point(12, 170)

# Min size filter
$lblMinSize = New-Object System.Windows.Forms.Label
$lblMinSize.Text = 'Min size filter (GB):'
$lblMinSize.AutoSize = $true
$lblMinSize.Location = New-Object System.Drawing.Point(12, 200)

$numMinSize = New-Object System.Windows.Forms.NumericUpDown
$numMinSize.Location = New-Object System.Drawing.Point(110, 198)
$numMinSize.Minimum = 0
$numMinSize.Maximum = 1000
$numMinSize.DecimalPlaces = 1
$numMinSize.Increment = 0.1
$numMinSize.Width = 80

# Кнопки
$btnApply = New-Object System.Windows.Forms.Button
$btnApply.Text = 'Apply'
$btnApply.Location = New-Object System.Drawing.Point(420, 300)
$btnApply.Width = 80

$btnClose = New-Object System.Windows.Forms.Button
$btnClose.Text = 'Close'
$btnClose.Location = New-Object System.Drawing.Point(520, 300)
$btnClose.Width = 80

# Статус
$lblStatus = New-Object System.Windows.Forms.Label
$lblStatus.AutoSize = $true
$lblStatus.Location = New-Object System.Drawing.Point(12, 250)
$lblStatus.ForeColor = [System.Drawing.Color]::Gray
$lblStatus.Text = 'Configure settings and press Apply.'

# Настройки по режимам
switch ($Mode) {
    "debug" {
        $chkVerbose.Checked = $true
        $chkSkipHardcoded.Checked = $false
        $numMinSize.Value = 0.0
        $lblStatus.Text = 'Debug mode: Disabled filters, verbose logs for troubleshooting'
    }
    "prod" {
        $chkVerbose.Checked = $false
        $chkSkipHardcoded.Checked = $false
        $numMinSize.Value = 1.0
        $lblStatus.Text = 'Production mode: Enabled filters, normal logs for daily work'
    }
    "default" {
        $chkVerbose.Checked = $false
        $chkSkipHardcoded.Checked = $true
        $numMinSize.Value = 1.0
        $lblStatus.Text = 'Default mode: Safe settings, hardcoded paths skipped'
    }
}

$form.AcceptButton = $btnApply
$form.CancelButton = $btnClose

function Set-Status {
    param(
        [bool]$Success,
        [string]$Message
    )

    if ($Success) {
        $lblStatus.ForeColor = [System.Drawing.Color]::ForestGreen
    } else {
        $lblStatus.ForeColor = [System.Drawing.Color]::IndianRed
    }

    $lblStatus.Text = $Message
}

function Test-NASAccess {
    try {
        $result = Test-NetConnection -ComputerName "nas-3d" -Port 445 -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($result) {
            return "✅ NAS is accessible"
        } else {
            return "⚠️ NAS offline - caching will use local sources only"
        }
    } catch {
        return "⚠️ NAS check failed - caching will use local sources only"
    }
}

function Test-CachePermissions {
    param([string]$Path)
    
    try {
        if (-not (Test-Path $Path)) {
            New-Item -ItemType Directory -Path $Path -Force | Out-Null
        }
        
        $testFile = Join-Path $Path "test_write.tmp"
        "test" | Out-File -FilePath $testFile -Force
        Remove-Item $testFile -Force
        
        return "✅ Cache directory is writable"
    } catch {
        return "❌ No write permission to cache directory"
    }
}

function Persist-Env {
    param(
        [string]$Name,
        [string]$Value
    )

    if ([string]::IsNullOrEmpty($Name)) {
        return @{ Exit = 1; Out = ''; Err = 'Missing variable name.' }
    }

    $data = if ($null -eq $Value) { '' } else { [string]$Value }
    if ($data.EndsWith('\')) {
        $data += '\'
    }

    try {
        $output = & setx.exe $Name $data 2>&1
        $exitCode = $LASTEXITCODE
    } catch {
        return @{ Exit = 1; Out = ''; Err = $_.Exception.Message }
    }

    $message = if ($output) { ($output | Out-String).TrimEnd() } else { '' }

    if ($exitCode -ne 0) {
        return @{ Exit = $exitCode; Out = ''; Err = $message }
    }

    return @{ Exit = $exitCode; Out = $message; Err = '' }
}

$btnBrowse.Add_Click({
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = 'Select Arena AutoCache folder'
    $dialog.ShowNewFolderButton = $true

    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $txtPath.Text = $dialog.SelectedPath
    }
})

$btnApply.Add_Click({
    try {
        $path = $txtPath.Text.Trim()

        if ([string]::IsNullOrWhiteSpace($path)) {
            throw [System.ArgumentException]::new('Cache folder is required.')
        }

        $absolutePath = [System.IO.Path]::GetFullPath($path)
        [System.IO.Directory]::CreateDirectory($absolutePath) | Out-Null

        $limit = [int]$numLimit.Value
        if ($limit -le 0) {
            throw [System.ArgumentOutOfRangeException]::new('Cache size must be greater than zero.')
        }

        # Проверяем доступность NAS
        $nasStatus = Test-NASAccess
        Write-Host $nasStatus

        # Проверяем права на папку кеша
        $permStatus = Test-CachePermissions -Path $absolutePath
        Write-Host $permStatus

        if ($permStatus -like "❌*") {
            throw [System.UnauthorizedAccessException]::new('No write permission to cache directory')
        }

        # Настройки
        $pairs = @(
            @{ Key = 'ARENA_CACHE_ROOT'; Value = $absolutePath },
            @{ Key = 'ARENA_CACHE_MAX_GB'; Value = [string]$limit },
            @{ Key = 'ARENA_CACHE_ENABLE'; Value = '1' },
            @{ Key = 'ARENA_CACHE_VERBOSE'; Value = if ($chkVerbose.Checked) { '1' } else { '0' } },
            @{ Key = 'ARENA_CACHE_MIN_SIZE_GB'; Value = [string]$numMinSize.Value },
            @{ Key = 'ARENA_CACHE_SKIP_HARDCODED'; Value = if ($chkSkipHardcoded.Checked) { '1' } else { '0' } }
        )

        # Показываем текущие настройки
        Write-Host ""
        Write-Host "[Arena AutoCache Bootstrap] Current settings:" -ForegroundColor Cyan
        Write-Host "  📁 Cache directory: $absolutePath"
        Write-Host "  📏 Cache limit: $limit GiB"
        Write-Host "  🔧 Enable cache: 1"
        Write-Host "  📝 Verbose logs: $($pairs[3].Value)"
        Write-Host "  📏 Min size filter: $($pairs[4].Value) GB"
        Write-Host "  🚫 Skip hardcoded paths: $($pairs[5].Value)"

        foreach ($item in $pairs) {
            [Environment]::SetEnvironmentVariable($item.Key, $item.Value, 'Process')
            [Environment]::SetEnvironmentVariable($item.Key, $item.Value, 'User')
        }

        $errors = @()

        foreach ($item in $pairs) {
            $result = Persist-Env -Name $item.Key -Value $item.Value
            if ($result.Exit -ne 0) {
                $errors += "${($item.Key)}: $($result.Err.Trim())"
            }
        }

        if ($errors.Count -eq 0) {
            Set-Status -Success $true -Message "Success! Settings applied. Restart terminal windows to load variables."
            Write-Output "EXPORT ARENA_CACHE_ROOT=$absolutePath"
            Write-Output "EXPORT ARENA_CACHE_MAX_GB=$limit"
            Write-Output "EXPORT ARENA_CACHE_ENABLE=1"
            Write-Output "EXPORT ARENA_CACHE_VERBOSE=$($pairs[3].Value)"
            Write-Output "EXPORT ARENA_CACHE_MIN_SIZE_GB=$($pairs[4].Value)"
            Write-Output "EXPORT ARENA_CACHE_SKIP_HARDCODED=$($pairs[5].Value)"
            
            # Показываем быстрые подсказки
            Write-Host ""
            Write-Host "[Arena AutoCache Bootstrap] Quick tips:" -ForegroundColor Yellow
            Write-Host "  • If you see 'copy_skipped (hardcoded path detected)' in Smart node:"
            Write-Host "    Check ARENA_CACHE_SKIP_HARDCODED=0 and restart ComfyUI"
            Write-Host "  • For cache testing use Smart/OPS in audit_then_warmup mode"
            Write-Host "  • Monitor progress in Copy Status node"
            Write-Host "  • Check comfyui.log for detailed information"
        } else {
            Set-Status -Success $false -Message "Applied with warnings:`r`n$($errors -join "`r`n")"
        }
    } catch {
        Set-Status -Success $false -Message ('Failure: ' + $_.Exception.Message)
    }
})

$btnClose.Add_Click({
    $form.Close()
})

# Загружаем существующие настройки
$existingRoot = [Environment]::GetEnvironmentVariable('ARENA_CACHE_ROOT', 'User')
if ([string]::IsNullOrWhiteSpace($existingRoot)) {
    $existingRoot = [Environment]::GetEnvironmentVariable('ARENA_CACHE_ROOT', 'Process')
}
if (-not [string]::IsNullOrWhiteSpace($existingRoot)) {
    $txtPath.Text = $existingRoot
} elseif (-not [string]::IsNullOrWhiteSpace($CacheRoot)) {
    $txtPath.Text = $CacheRoot
}

$existingLimit = [Environment]::GetEnvironmentVariable('ARENA_CACHE_MAX_GB', 'User')
if ([string]::IsNullOrWhiteSpace($existingLimit)) {
    $existingLimit = [Environment]::GetEnvironmentVariable('ARENA_CACHE_MAX_GB', 'Process')
}
$parsedLimit = 0
if ([int]::TryParse($existingLimit, [ref]$parsedLimit)) {
    if ($parsedLimit -ge $numLimit.Minimum -and $parsedLimit -le $numLimit.Maximum) {
        $numLimit.Value = $parsedLimit
    }
}

# Загружаем существующие настройки фильтров
$existingVerbose = [Environment]::GetEnvironmentVariable('ARENA_CACHE_VERBOSE', 'User')
if ([string]::IsNullOrWhiteSpace($existingVerbose)) {
    $existingVerbose = [Environment]::GetEnvironmentVariable('ARENA_CACHE_VERBOSE', 'Process')
}
if ($existingVerbose -eq '1') {
    $chkVerbose.Checked = $true
}

$existingSkipHardcoded = [Environment]::GetEnvironmentVariable('ARENA_CACHE_SKIP_HARDCODED', 'User')
if ([string]::IsNullOrWhiteSpace($existingSkipHardcoded)) {
    $existingSkipHardcoded = [Environment]::GetEnvironmentVariable('ARENA_CACHE_SKIP_HARDCODED', 'Process')
}
if ($existingSkipHardcoded -eq '1') {
    $chkSkipHardcoded.Checked = $true
}

$existingMinSize = [Environment]::GetEnvironmentVariable('ARENA_CACHE_MIN_SIZE_GB', 'User')
if ([string]::IsNullOrWhiteSpace($existingMinSize)) {
    $existingMinSize = [Environment]::GetEnvironmentVariable('ARENA_CACHE_MIN_SIZE_GB', 'Process')
}
$parsedMinSize = 0
if ([decimal]::TryParse($existingMinSize, [ref]$parsedMinSize)) {
    if ($parsedMinSize -ge $numMinSize.Minimum -and $parsedMinSize -le $numMinSize.Maximum) {
        $numMinSize.Value = $parsedMinSize
    }
}

$form.Controls.AddRange(@(
    $lblMode,
    $lblPath,
    $txtPath,
    $btnBrowse,
    $lblLimit,
    $numLimit,
    $lblAdvanced,
    $chkVerbose,
    $chkSkipHardcoded,
    $lblMinSize,
    $numMinSize,
    $btnApply,
    $btnClose,
    $lblStatus
))

[void]$form.ShowDialog()
exit 0
