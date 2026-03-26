# validate-assets.ps1
param(
    [string]$Path = "app"
)

$errors = @()
$cssFiles = Get-ChildItem -Path $Path -Filter "*.css" -Recurse

foreach ($file in $cssFiles) {
    $content = Get-Content $file.FullName -Raw
    $forbidden = @("Out-File", "Get-Content", '@"', '"@', "# Verify", "`$")
    
    foreach ($pattern in $forbidden) {
        if ($content -match $pattern) {
            $errors += "$($file.FullName) contains PowerShell artifact: $pattern"
        }
    }
}

if ($errors.Count -gt 0) {
    Write-Host "❌ Validation failed:" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    exit 1
} else {
    Write-Host "✅ All assets clean" -ForegroundColor Green
    exit 0
}
