# Define paths
$compDir = "D:\okiru-os\RezHive V12\frontend\components"
$searchDir = "D:\okiru-os\RezHive V12\frontend\app" # Adjust to 'pages' if not using App Router

# Get all component names (stripping .tsx)
$components = Get-ChildItem -Path $compDir -Filter "*.tsx" | Select-Object -ExpandProperty BaseName

Write-Host "--- FRONTEND COMPONENT AUDIT ---" -ForegroundColor Cyan

foreach ($comp in $components) {
    # Skip backups and copies explicitly
    if ($comp -like "*- Copy*" -or $comp -like "*.bak*") {
        Write-Host "[🗑️] Skipping Backup: $comp" -ForegroundColor Gray
        continue
    }

    # Search for the component name in the app directory (looking for imports)
    $occurrences = Get-ChildItem -Path $searchDir -Recurse -Include *.tsx, *.ts, *.js | 
                   Select-String -Pattern "from .*$comp" -SimpleMatch

    if ($occurrences) {
        $count = $occurrences.Count
        Write-Host "[✅] USED ($count): $comp" -ForegroundColor Green
    } else {
        Write-Host "[❌] UNUSED: $comp" -ForegroundColor Red
    }
}