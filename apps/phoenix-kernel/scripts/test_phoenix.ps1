$API_BASE = "http://localhost:8002"
$testsPassed = 0
$testsFailed = 0

Write-Host "
🧪 PHOENIX TEST SUITE
" -ForegroundColor Cyan

# Test 1
try {
    $result = Invoke-RestMethod -Uri "$API_BASE/health" -Method Get
    Write-Host "✅ Health: PASS" -ForegroundColor Green
    $testsPassed++
} catch {
    Write-Host "❌ Health: FAIL" -ForegroundColor Red
    $testsFailed++
}

# Test 2
try {
    $result = Invoke-RestMethod -Uri "$API_BASE/workers/list" -Method Get
    Write-Host "✅ Workers: PASS" -ForegroundColor Green
    $testsPassed++
} catch {
    Write-Host "❌ Workers: FAIL" -ForegroundColor Red
    $testsFailed++
}

# Test 3
try {
    $body = @{task = "/health"} | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$API_BASE/kernel/stream" -Method Post -ContentType "application/json" -Body $body
    Write-Host "✅ Stream: PASS" -ForegroundColor Green
    $testsPassed++
} catch {
    Write-Host "❌ Stream: FAIL" -ForegroundColor Red
    $testsFailed++
}

Write-Host "
📊 Results: $testsPassed passed, $testsFailed failed
" -ForegroundColor Cyan
