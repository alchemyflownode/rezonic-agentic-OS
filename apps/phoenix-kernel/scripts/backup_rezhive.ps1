# backup_rezhive.ps1
# Backup Rezhive memory

param(
    [string]$BackupPath
)

$KernelRoot = "D:\Rezonic_Agentic\apps\phoenix-kernel"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = if ($BackupPath) { $BackupPath } else { "$KernelRoot\data\rezhive_backups\rezhive_$Timestamp" }

Write-Host "💾 Backing up Rezhive memory..." -ForegroundColor Cyan

# Create backup directory
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

# Backup database
$DbPath = "$KernelRoot\data\memory\rezhive_memory.db"
if (Test-Path $DbPath) {
    Copy-Item $DbPath "$BackupDir\" -Force
    Write-Host "  ✓ Backed up database" -ForegroundColor Green
}

# Backup JSON files
$JsonPath = "$KernelRoot\data\memory\*.json"
if (Get-ChildItem $JsonPath -ErrorAction SilentlyContinue) {
    Copy-Item $JsonPath "$BackupDir\" -Force
    Write-Host "  ✓ Backed up JSON files" -ForegroundColor Green
}

# Create manifest
$Manifest = @{
    timestamp = $Timestamp
    backup_path = $BackupDir
    files = Get-ChildItem $BackupDir | Select-Object Name, Length
}
$Manifest | ConvertTo-Json | Out-File "$BackupDir\manifest.json"

Write-Host "✅ Backup saved to: $BackupDir" -ForegroundColor Green
