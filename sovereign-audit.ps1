Write-Host @"
╔════════════════════════════════════════════════════════════╗
║         SOVEREIGN OS COMPLETE AUDIT REPORT                ║
║                    v13.3.0                                 ║
╚════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

Write-Host "`n📊 1. SYSTEM STATUS" -ForegroundColor Yellow
Write-Host "────────────────────────────────────────" -ForegroundColor DarkGray

# Kernel Status
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8002/health" -Method Get -TimeoutSec 3
    Write-Host "  ✅ Kernel: ONLINE" -ForegroundColor Green
    Write-Host "     Workers: $($health.workers)" -ForegroundColor Gray
    Write-Host "     SCE Score: $($health.integrity_score)%" -ForegroundColor Gray
    Write-Host "     Status: $($health.status)" -ForegroundColor Gray
} catch {
    Write-Host "  ❌ Kernel: OFFLINE" -ForegroundColor Red
}

# Frontend Status
try {
    $frontend = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 3
    Write-Host "  ✅ Frontend: ONLINE" -ForegroundColor Green
    Write-Host "     Status: $($frontend.StatusCode)" -ForegroundColor Gray
} catch {
    Write-Host "  ❌ Frontend: OFFLINE" -ForegroundColor Red
}

Write-Host "`n📁 2. PAGE INVENTORY" -ForegroundColor Yellow
Write-Host "────────────────────────────────────────" -ForegroundColor DarkGray

$pages = @(
    "/dashboard",
    "/system/appbuilder", 
    "/system/scanner",
    "/system/techdebt",
    "/gallery",
    "/trading",
    "/workers"
)

foreach ($page in $pages) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000$page" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        Write-Host "  ✅ $page - OK" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ $page - FAILED" -ForegroundColor Red
    }
}

Write-Host "`n🎨 3. COMPONENT CHECK" -ForegroundColor Yellow
Write-Host "────────────────────────────────────────" -ForegroundColor DarkGray

$components = @(
    "SovereignCanvas.tsx",
    "SovereignCodeBlock.tsx", 
    "SovereignMessage.tsx"
)

$componentPath = "D:\Rezonic_Agentic\apps\phoenix-frontend\components"

foreach ($comp in $components) {
    $fullPath = Join-Path $componentPath $comp
    if (Test-Path $fullPath) {
        $size = [math]::Round((Get-Item $fullPath).Length / 1KB, 2)
        Write-Host "  ✅ $comp ($size KB)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $comp - MISSING" -ForegroundColor Red
    }
}

Write-Host "`n🧪 4. CODE GENERATION TEST" -ForegroundColor Yellow
Write-Host "────────────────────────────────────────" -ForegroundColor DarkGray

try {
    $codeBody = @{ task = "/code add two numbers" } | ConvertTo-Json
    $codeResponse = Invoke-RestMethod -Uri "http://localhost:8002/kernel/stream" -Method Post -Body $codeBody -ContentType "application/json" -TimeoutSec 5
    
    Write-Host "  ✅ Code endpoint responding" -ForegroundColor Green
    
    # Check if response contains code
    if ($codeResponse -match "def " -or $codeResponse -match "```") {
        Write-Host "  ✅ Code generation working" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Code response format may need parsing" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ Code endpoint error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n📦 5. DEPENDENCY CHECK" -ForegroundColor Yellow
Write-Host "────────────────────────────────────────" -ForegroundColor DarkGray

$packageJson = Get-Content "D:\Rezonic_Agentic\apps\phoenix-frontend\package.json" | ConvertFrom-Json
$keyDeps = @("pyodide", "framer-motion", "lucide-react", "react-syntax-highlighter")

foreach ($dep in $keyDeps) {
    if ($packageJson.dependencies.PSObject.Properties.Name -contains $dep) {
        $version = $packageJson.dependencies.$dep
        Write-Host "  ✅ $dep - $version" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $dep - NOT INSTALLED" -ForegroundColor Red
    }
}

Write-Host "`n🎯 6. DASHBOARD CODE BLOCK DETECTION" -ForegroundColor Yellow
Write-Host "────────────────────────────────────────" -ForegroundColor DarkGray

$dashboardPath = "D:\Rezonic_Agentic\apps\phoenix-frontend\app\dashboard\page.tsx"
if (Test-Path $dashboardPath) {
    $dashboardContent = Get-Content $dashboardPath -Raw
    
    if ($dashboardContent -match "SovereignCodeBlock") {
        Write-Host "  ✅ SovereignCodeBlock imported" -ForegroundColor Green
    } else {
        Write-Host "  ❌ SovereignCodeBlock NOT imported" -ForegroundColor Red
    }
    
    if ($dashboardContent -match "extractCodeFromContent|extractCodeFromResponse") {
        Write-Host "  ✅ Code extraction function present" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Code extraction function missing" -ForegroundColor Red
    }
}

Write-Host "`n📈 7. PERFORMANCE METRICS" -ForegroundColor Yellow
Write-Host "────────────────────────────────────────" -ForegroundColor DarkGray

# Count files
$tsxFiles = Get-ChildItem -Path "D:\Rezonic_Agentic\apps\phoenix-frontend\app" -Recurse -Include "*.tsx" | Measure-Object | Select-Object -ExpandProperty Count
$componentFiles = Get-ChildItem -Path "D:\Rezonic_Agentic\apps\phoenix-frontend\components" -Include "*.tsx" | Measure-Object | Select-Object -ExpandProperty Count

Write-Host "  Total TSX files: $tsxFiles" -ForegroundColor Cyan
Write-Host "  Components: $componentFiles" -ForegroundColor Cyan
Write-Host "  Active Workers: $($health.workers)" -ForegroundColor Cyan

Write-Host "`n✅ AUDIT COMPLETE!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan

# Recommendations
Write-Host "`n💡 RECOMMENDATIONS:" -ForegroundColor Yellow
if ($health.workers -gt 0) {
    Write-Host "  ✓ Kernel running with $($health.workers) workers" -ForegroundColor White
}
Write-Host "  → Test dashboard with: /code add two numbers" -ForegroundColor White
Write-Host "  → Check browser console for any errors (F12)" -ForegroundColor White
Write-Host "  → If code blocks don't show, refresh and clear cache (Ctrl+Shift+R)" -ForegroundColor White

