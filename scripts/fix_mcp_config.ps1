param()
$ErrorActionPreference = 'Stop'
$cfg = "$env:USERPROFILE\.cursor\mcp.json"
if (!(Test-Path $cfg)) { throw "Config not found: $cfg" }
$timestamp = Get-Date -Format yyyyMMddHHmmss
$bk = "$cfg.bak_$timestamp"
Copy-Item -Path $cfg -Destination $bk -Force
$docsSrv = 'c:\mcp-servers\docs-manager\dist\server.js'
$chgSrv  = 'c:\mcp-servers\changelog\dist\server.js'
Write-Host ("docs-manager server.js exists: " + (Test-Path $docsSrv))
Write-Host ("changelog server.js exists: " + (Test-Path $chgSrv))
$json = Get-Content $cfg -Raw | ConvertFrom-Json
if (-not $json.mcpServers) { $json | Add-Member -NotePropertyName mcpServers -NotePropertyValue (@{}) }
$repoPath = 'C:\ComfyUI\custom_nodes\ComfyUI-Arena'
$docsBlock = [ordered]@{
  command = 'node'
  args    = @($docsSrv,'--basePath',$repoPath,'--docsPath','docs','--includeGlobs','docs/*.md','--includeGlobs','docs/en/*.md','--includeGlobs','docs/ru/*.md')
  env     = @{ DOCS_BASE=$repoPath; DOCS_PATH='docs' }
}
$chgBlock = [ordered]@{
  command = 'node'
  args    = @($chgSrv,'--repoPath',$repoPath,'--changelogFile','CHANGELOG.md')
}
$json.mcpServers.'docs-manager' = $docsBlock
$json.mcpServers.'changelog'    = $chgBlock
($json | ConvertTo-Json -Depth 10) | Set-Content -Path $cfg -Encoding UTF8
Write-Host "Updated: $cfg"
Write-Host "Backup:  $bk"