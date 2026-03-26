# KILL ALL NODE PROCESSES (Clean reset)
Write-Host "🛑 Stopping all Node.js processes..." -ForegroundColor Yellow
taskkill /F /IM node.exe 2>$null
taskkill /F /IM next.exe 2>$null
Write-Host "✅ All Node processes killed" -ForegroundColor Green

# Wait a moment for ports to free up
Start-Sleep -Seconds 2

# Clear Next.js cache
Write-Host "`n🧹 Clearing Next.js cache..." -ForegroundColor Yellow
if (Test-Path "D:\Rezonic_Agentic\apps\phoenix-frontend\.next") {
    Remove-Item "D:\Rezonic_Agentic\apps\phoenix-frontend\.next" -Recurse -Force
    Write-Host "✅ Cache cleared" -ForegroundColor Green
}

# Navigate to frontend
Set-Location "D:\Rezonic_Agentic\apps\phoenix-frontend"

# Start fresh
Write-Host "`n🚀 Starting fresh Next.js server..." -ForegroundColor Cyan
Write-Host "npm run dev" -ForegroundColor White
npm run dev