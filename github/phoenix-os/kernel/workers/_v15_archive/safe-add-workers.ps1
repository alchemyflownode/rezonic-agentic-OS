# safe-add-workers.ps1 - Safely add workers to registry (with backup)
param(
    [switch]$DryRun = $true
)

$registryPath = "D:\Rezonic_Agentic\apps\phoenix-kernel\registry.py"
$patchFile = "registry-patch.txt"

if (-not (Test-Path $patchFile)) {
    Write-Host "❌ No patch file found. Run generate-registry-entries.ps1 first." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $registryPath)) {
    Write-Host "❌ registry.py not found!" -ForegroundColor Red
    exit 1
}

$linesToAdd = Get-Content $patchFile | Where-Object { $_ -match "register_worker" }

if ($DryRun) {
    Write-Host "🔍 DRY RUN - No changes will be made" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Would add these $($linesToAdd.Count) lines:" -ForegroundColor Cyan
    $linesToAdd | ForEach-Object { Write-Host "   $_" -ForegroundColor Green }
    Write-Host ""
    Write-Host "To actually add them, run: .\safe-add-workers.ps1 -DryRun:`$false" -ForegroundColor Yellow
} else {
    Write-Host "⚠️  PROCEEDING WITH ACTUAL CHANGES" -ForegroundColor Red
    Write-Host ""
    
    # Backup
    $backupPath = "$registryPath.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $registryPath $backupPath
    Write-Host "✅ Backed up to: $backupPath" -ForegroundColor Green
    
    # Add to registry
    $registryContent = Get-Content $registryPath -Raw
    $newContent = $registryContent + "`n# Auto-added workers`n" + ($linesToAdd -join "`n") + "`n"
    $newContent | Out-File $registryPath -Encoding UTF8
    
    Write-Host "✅ Added $($linesToAdd.Count) workers to registry.py" -ForegroundColor Green
    Write-Host "🔄 Restart kernel to load: python kernel.py" -ForegroundColor Yellow
}
