# REZ HIVE v8.0 - CORRECTED LAUNCHER
# Based on your actual structure

$RootPath = "D:\okiru-os\RezHiveOS"
$BackendPath = "$RootPath\backend"
$FrontendPath = "$RootPath\backend"  # Your frontend is IN the backend folder!

Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         REZ HIVE v8.0 - SOVEREIGN LAUNCHER                   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Kill processes on ports
Write-Host "📡 Clearing ports..." -ForegroundColor Yellow
$ports = @(8001, 8003, 3000)
foreach ($port in $ports) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  Stopping $($proc.Name) on port $port" -ForegroundColor Red
            Stop-Process -Id $conn.OwningProcess -Force
        }
    }
}

# Ask which backend to run
Write-Host ""
Write-Host "🔧 Which backend do you want to run?" -ForegroundColor Yellow
Write-Host "  1) main.py (original - port 8001)" -ForegroundColor Gray
Write-Host "  2) v8-unified-kernel.py (if exists - port 8003)" -ForegroundColor Gray
$choice = Read-Host "Enter choice (1 or 2)"

if ($choice -eq "2" -and (Test-Path "$BackendPath\v8-unified-kernel.py")) {
    $backendFile = "v8-unified-kernel.py"
    $port = 8003
    Write-Host "  Selected: v8-unified-kernel.py on port $port" -ForegroundColor Green
} else {
    $backendFile = "main.py"
    $port = 8001
    Write-Host "  Selected: main.py on port $port" -ForegroundColor Green
}

# Check if frontend is Next.js or just static
$isNextJs = Test-Path "$FrontendPath\package.json"

if ($isNextJs) {
    # It's a Next.js app - need to run dev server
    Write-Host ""
    Write-Host "🚀 Starting Next.js dev server..." -ForegroundColor Green
    Start-Process cmd -ArgumentList "/k cd /d $FrontendPath && title Frontend && npm run dev"
    $frontendUrl = "http://localhost:3000"
} else {
    # It's just a TypeScript file - need to serve it somehow
    Write-Host ""
    Write-Host "⚠️  SovereignDashboard.tsx found but no package.json" -ForegroundColor Yellow
    Write-Host "   You'll need to open this file directly or set up a web server" -ForegroundColor Yellow
    $frontendUrl = "file://$FrontendPath\SovereignDashboard.tsx"
}

# Start backend
Write-Host ""
Write-Host "🚀 Starting backend: $backendFile on port $port..." -ForegroundColor Green
Start-Process cmd -ArgumentList "/k cd /d $BackendPath && title REZ HIVE Backend && python $backendFile"

Start-Sleep -Seconds 3

# Open browser
if ($isNextJs) {
    Start-Process $frontendUrl
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         ✅ REZ HIVE v8.0 IS RUNNING!                         ║" -ForegroundColor Green
Write-Host "╠══════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║  📊 Backend:  http://localhost:$port                         ║" -ForegroundColor White
Write-Host "║  🎨 Frontend: $frontendUrl                                   ║" -ForegroundColor White
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "📡 Test endpoints:" -ForegroundColor Yellow
Write-Host "   curl http://localhost:$port/health" -ForegroundColor Gray
Write-Host "   curl http://localhost:$port/workers" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 Services will keep running in their own windows" -ForegroundColor Yellow
Write-Host "   Close this window to exit launcher (services continue)"
Write-Host ""
Read-Host "Press Enter to close this window"