Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = 'Arena AutoCache - Bootstrap'
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.MinimizeBox = $true
$form.ClientSize = New-Object System.Drawing.Size(540, 190)

$lblPath = New-Object System.Windows.Forms.Label
$lblPath.Text = 'Cache folder:'
$lblPath.AutoSize = $true
$lblPath.Location = New-Object System.Drawing.Point(12, 15)

$txtPath = New-Object System.Windows.Forms.TextBox
$txtPath.Location = New-Object System.Drawing.Point(110, 12)
$txtPath.Width = 340

$btnBrowse = New-Object System.Windows.Forms.Button
$btnBrowse.Text = 'Browse...'
$btnBrowse.Location = New-Object System.Drawing.Point(460, 10)
$btnBrowse.Width = 80

$lblLimit = New-Object System.Windows.Forms.Label
$lblLimit.Text = 'Cache size (GiB):'
$lblLimit.AutoSize = $true
$lblLimit.Location = New-Object System.Drawing.Point(12, 60)

$numLimit = New-Object System.Windows.Forms.NumericUpDown
$numLimit.Location = New-Object System.Drawing.Point(110, 58)
$numLimit.Minimum = 1
$numLimit.Maximum = 1048576
$numLimit.Value = 50
$numLimit.Width = 80

$btnApply = New-Object System.Windows.Forms.Button
$btnApply.Text = 'Apply'
$btnApply.Location = New-Object System.Drawing.Point(360, 140)
$btnApply.Width = 80

$btnClose = New-Object System.Windows.Forms.Button
$btnClose.Text = 'Close'
$btnClose.Location = New-Object System.Drawing.Point(460, 140)
$btnClose.Width = 80

$lblStatus = New-Object System.Windows.Forms.Label
$lblStatus.AutoSize = $true
$lblStatus.Location = New-Object System.Drawing.Point(12, 110)
$lblStatus.ForeColor = [System.Drawing.Color]::Gray
$lblStatus.Text = 'Select the cache folder and limit, then press Apply.'

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
        $path = $txtPath.Text
        if ($null -eq $path) {
            $path = ''
        }
        $path = $path.Trim()

        if ([string]::IsNullOrWhiteSpace($path)) {
            throw [System.ArgumentException]::new('Cache folder is required.')
        }

        $absolutePath = [System.IO.Path]::GetFullPath($path)
        [System.IO.Directory]::CreateDirectory($absolutePath) | Out-Null

        $limit = [int]$numLimit.Value
        if ($limit -le 0) {
            throw [System.ArgumentOutOfRangeException]::new('Cache size must be greater than zero.')
        }

        $pairs = @(
            @{ Key = 'ARENA_CACHE_ROOT';    Value = $absolutePath },
            @{ Key = 'ARENA_CACHE_MAX_GB';  Value = [string]$limit },
            @{ Key = 'ARENA_CACHE_ENABLE';  Value = '1' },
            @{ Key = 'ARENA_CACHE_VERBOSE'; Value = '0' }
        )

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
            Set-Status -Success $true -Message ([string]::Format('Success. Root: {0}, Limit: {1} GiB. Restart terminal windows.', $absolutePath, $limit))
            Write-Output "EXPORT ARENA_CACHE_ROOT=$absolutePath"
            Write-Output "EXPORT ARENA_CACHE_MAX_GB=$limit"
            Write-Output 'EXPORT ARENA_CACHE_ENABLE=1'
            Write-Output 'EXPORT ARENA_CACHE_VERBOSE=0'
        } else {
            Set-Status -Success $false -Message ("Applied with warnings:`r`n{0}" -f ($errors -join "`r`n"))
        }
    } catch {
        Set-Status -Success $false -Message ('Failure: ' + $_.Exception.Message)
    }
})

$btnClose.Add_Click({
    $form.Close()
})

$existingRoot = [Environment]::GetEnvironmentVariable('ARENA_CACHE_ROOT', 'User')
if ([string]::IsNullOrWhiteSpace($existingRoot)) {
    $existingRoot = [Environment]::GetEnvironmentVariable('ARENA_CACHE_ROOT', 'Process')
}
if (-not [string]::IsNullOrWhiteSpace($existingRoot)) {
    $txtPath.Text = $existingRoot
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

$form.Controls.AddRange(@(
    $lblPath,
    $txtPath,
    $btnBrowse,
    $lblLimit,
    $numLimit,
    $btnApply,
    $btnClose,
    $lblStatus
))

[void]$form.ShowDialog()
exit 0
