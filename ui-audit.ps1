Write-Host "========================================" -ForegroundColor Cyan
Write-Host "     PHOENIX OS UI AUDIT REPORT" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Navigate to frontend
Set-Location "D:\Rezonic_Agentic\apps\phoenix-frontend"

# 1. Check all page components
Write-Host "📁 1. PAGE COMPONENTS INVENTORY" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor DarkGray

$pages = Get-ChildItem -Path "app" -Recurse -Filter "page.tsx" | Where-Object { $_.FullName -notlike "*node_modules*" }
foreach ($page in $pages) {
    $relativePath = $page.FullName.Replace("D:\Rezonic_Agentic\apps\phoenix-frontend\", "")
    $size = [math]::Round((Get-Item $page.FullName).Length / 1KB, 2)
    Write-Host "  ✓ $relativePath ($size KB)" -ForegroundColor Green
}

# 2. Check all components
Write-Host "`n🧩 2. COMPONENTS INVENTORY" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor DarkGray

$components = Get-ChildItem -Path "components" -Filter "*.tsx" | Where-Object { $_.FullName -notlike "*node_modules*" }
foreach ($comp in $components) {
    $size = [math]::Round((Get-Item $comp.FullName).Length / 1KB, 2)
    Write-Host "  ✓ $($comp.Name) ($size KB)" -ForegroundColor Green
}

# 3. Check for imports and dependencies
Write-Host "`n📦 3. DEPENDENCY CHECK" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor DarkGray

$packageJson = Get-Content "package.json" | ConvertFrom-Json
$dependencies = $packageJson.dependencies.PSObject.Properties
Write-Host "  Total Dependencies: $($dependencies.Count)" -ForegroundColor Cyan

$keyDeps = @("react-syntax-highlighter", "framer-motion", "lucide-react", "next")
foreach ($dep in $keyDeps) {
    if ($dependencies | Where-Object { $_.Name -eq $dep }) {
        Write-Host "  ✓ $dep installed" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $dep MISSING" -ForegroundColor Red
    }
}

# 4. Check for build errors
Write-Host "`n🔧 4. BUILD VALIDATION" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor DarkGray

Write-Host "  Attempting type check..." -ForegroundColor Gray
$typeCheck = npx tsc --noEmit 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ TypeScript compilation successful" -ForegroundColor Green
} else {
    Write-Host "  ✗ TypeScript errors found:" -ForegroundColor Red
    $typeCheck | Select-Object -First 5 | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
}

# 5. Check specific UI components for issues
Write-Host "`n🎨 5. UI COMPONENT AUDIT" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor DarkGray

# Check SovereignCanvas
if (Test-Path "components\SovereignCanvas.tsx") {
    $content = Get-Content "components\SovereignCanvas.tsx" -Raw
    if ($content -match "addLog\([^'`"]") {
        Write-Host "  ✗ SovereignCanvas.tsx: Potential string issues detected" -ForegroundColor Red
    } else {
        Write-Host "  ✓ SovereignCanvas.tsx: Syntax looks good" -ForegroundColor Green
    }
} else {
    Write-Host "  ✗ SovereignCanvas.tsx: MISSING" -ForegroundColor Red
}

# Check SovereignMessage
if (Test-Path "components\SovereignMessage.tsx") {
    Write-Host "  ✓ SovereignMessage.tsx: Present" -ForegroundColor Green
} else {
    Write-Host "  ✗ SovereignMessage.tsx: MISSING" -ForegroundColor Red
}

# Check Dashboard
if (Test-Path "app\dashboard\page.tsx") {
    $dashboardContent = Get-Content "app\dashboard\page.tsx" -Raw
    if ($dashboardContent -match "SovereignMessage") {
        Write-Host "  ✓ Dashboard: Uses SovereignMessage correctly" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Dashboard: SovereignMessage not imported" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✗ Dashboard: MISSING" -ForegroundColor Red
}

# Check App Builder
if (Test-Path "app\system\appbuilder\page.tsx") {
    $appBuilder = Get-Content "app\system\appbuilder\page.tsx" -Raw
    if ($appBuilder -match "SovereignCanvas") {
        Write-Host "  ✓ App Builder: Uses SovereignCanvas correctly" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ App Builder: SovereignCanvas not integrated" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✗ App Builder: MISSING" -ForegroundColor Red
}

# Check Scanner
if (Test-Path "app\system\scanner\page.tsx") {
    Write-Host "  ✓ Scanner: Present" -ForegroundColor Green
} else {
    Write-Host "  ✗ Scanner: MISSING" -ForegroundColor Red
}

# Check Tech Debt
if (Test-Path "app\system\techdebt\page.tsx") {
    Write-Host "  ✓ Tech Debt: Present" -ForegroundColor Green
} else {
    Write-Host "  ✗ Tech Debt: MISSING" -ForegroundColor Red
}

# 6. Check for unused imports/variables
Write-Host "`n🧹 6. CODE QUALITY CHECKS" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor DarkGray

Write-Host "  Checking for console.log statements..." -ForegroundColor Gray
$consoleLogs = Get-ChildItem -Path "app","components" -Recurse -Include "*.tsx","*.ts" | Select-String "console\.log" | Where-Object { $_.Line -notmatch "//.*console\.log" }
if ($consoleLogs) {
    Write-Host "  ⚠ Found $($consoleLogs.Count) console.log statements:" -ForegroundColor Yellow
    $consoleLogs | Select-Object -First 3 | ForEach-Object { Write-Host "    $($_.Filename):$($_.LineNumber)" -ForegroundColor Yellow }
} else {
    Write-Host "  ✓ No console.log statements found" -ForegroundColor Green
}

# 7. Performance metrics
Write-Host "`n⚡ 7. PERFORMANCE METRICS" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor DarkGray

$totalSize = 0
$allFiles = Get-ChildItem -Path "app","components" -Recurse -Include "*.tsx","*.ts" | Where-Object { $_.FullName -notlike "*node_modules*" }
foreach ($file in $allFiles) {
    $totalSize += (Get-Item $file.FullName).Length
}
$totalSizeMB = [math]::Round($totalSize / 1MB, 2)

Write-Host "  Total TypeScript/TSX files: $($allFiles.Count)" -ForegroundColor Cyan
Write-Host "  Total code size: $totalSizeMB MB" -ForegroundColor Cyan

# 8. Summary
Write-Host "`n📊 8. SUMMARY" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor DarkGray

Write-Host "  Pages: $($pages.Count)" -ForegroundColor White
Write-Host "  Components: $($components.Count)" -ForegroundColor White
Write-Host "  Dependencies: $($dependencies.Count)" -ForegroundColor White

Write-Host "`n✅ UI Audit Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

