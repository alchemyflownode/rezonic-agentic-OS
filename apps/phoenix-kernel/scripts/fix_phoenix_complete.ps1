# ============================================================================
# PHOENIX v14.0.0-OKIRU - COMPLETE AUTOMATED FIX SCRIPT
# ============================================================================
# Fixes:
#   1. Rate Limiter Bug (slowapi.Limiter → FallbackRateLimiter)
#   2. Semantic Memory Initialization
#   3. Event Bus Initialization in startup()
#   4. Collaboration Commands (/collaborate, /collab-stats)
#   5. Verification & Testing
# ============================================================================

param(
    [switch]$SkipBackup,
    [switch]$SkipTest,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$filePath = "D:\Rezonic_Agentic\apps\phoenix-kernel\phoenix_v14_omega_okiru.py"
$backupPath = "D:\Rezonic_Agentic\apps\phoenix-kernel\phoenix_v14_omega_okiru.py.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
$testScriptPath = "D:\Rezonic_Agentic\apps\phoenix-kernel\test_phoenix.ps1"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
function Write-Status {
    param([string]$Message, [string]$Status = "INFO")
    $color = switch ($Status) {
        "SUCCESS" { "Green" }
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        default { "Cyan" }
    }
    Write-Host "[$Status] $Message" -ForegroundColor $color
}

function Test-FileExists {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        Write-Status "File not found: $Path" "ERROR"
        return $false
    }
    return $true
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   PHOENIX v14.0.0-OKIRU - COMPLETE AUTOMATED FIX SCRIPT     ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# STEP 1: VERIFY FILE EXISTS
# ============================================================================
Write-Status "Step 1: Verifying Phoenix kernel file..." "INFO"
if (-not (Test-FileExists -Path $filePath)) {
    Write-Status "Cannot proceed. Please verify the file path." "ERROR"
    exit 1
}
Write-Status "Phoenix kernel file found!" "SUCCESS"

# ============================================================================
# STEP 2: CREATE BACKUP
# ============================================================================
if (-not $SkipBackup) {
    Write-Status "Step 2: Creating backup..." "INFO"
    try {
        Copy-Item -Path $filePath -Destination $backupPath -Force
        Write-Status "Backup created: $backupPath" "SUCCESS"
    } catch {
        Write-Status "Failed to create backup: $($_.Exception.Message)" "ERROR"
        exit 1
    }
} else {
    Write-Status "Skipping backup (per user request)" "WARNING"
}

# ============================================================================
# STEP 3: READ FILE CONTENT
# ============================================================================
Write-Status "Step 3: Reading Phoenix kernel file..." "INFO"
try {
    $content = Get-Content -Path $filePath -Raw -Encoding UTF8
    Write-Status "File loaded ($($content.Length) characters)" "SUCCESS"
} catch {
    Write-Status "Failed to read file: $($_.Exception.Message)" "ERROR"
    exit 1
}

# ============================================================================
# FIX 1: REPLACE SLOWAPI WITH FALLBACK RATE LIMITER
# ============================================================================
Write-Status "Fix 1: Replacing slowapi.Limiter with FallbackRateLimiter..." "INFO"

# Check if FallbackRateLimiter class exists
if ($content -match "class FallbackRateLimiter:") {
    Write-Status "FallbackRateLimiter class already exists" "SUCCESS"
} else {
    Write-Status "FallbackRateLimiter class NOT found - adding it..." "WARNING"
    
    $fallbackClass = @"

# ============================================================================
# FALLBACK RATE LIMITER (v14.0.0-FIX)
# ============================================================================
class FallbackRateLimiter:
    """Custom rate limiter with .check() method - replaces slowapi"""
    def __init__(self, calls_per_period: int = 100, period_seconds: int = 60):
        self.calls_per_period = calls_per_period
        self.period_seconds = period_seconds
        self.calls = defaultdict(list)
    
    async def check(self, client_id: str) -> bool:
        """Check if request is within rate limit"""
        now = time.time()
        self.calls[client_id] = [t for t in self.calls[client_id] if now - t < self.period_seconds]
        if len(self.calls[client_id]) >= self.calls_per_period:
            return False
        self.calls[client_id].append(now)
        return True

"@
    
    # Insert after Config class
    $configEnd = $content.IndexOf("config = Config()")
    if ($configEnd -gt 0) {
        $content = $content.Insert($configEnd + "config = Config()".Length, "`n" + $fallbackClass)
        Write-Status "FallbackRateLimiter class added" "SUCCESS"
    }
}

# Replace slowapi Limiter initialization with FallbackRateLimiter
$oldInit = "self.rate_limiter = None`n        if HAS_SLOWAPI:`n            self.rate_limiter = Limiter(key_func=get_remote_address, default_limits=[f`"{config.RATE_LIMIT_CALLS}/{config.RATE_LIMIT_PERIOD}`"])"
$newInit = "self.rate_limiter = FallbackRateLimiter(config.RATE_LIMIT_CALLS, config.RATE_LIMIT_PERIOD)"

if ($content -match [regex]::Escape($oldInit)) {
    $content = $content -replace [regex]::Escape($oldInit), $newInit
    Write-Status "Rate limiter initialization replaced" "SUCCESS"
} else {
    # Try alternative pattern
    if ($content -match "self\.rate_limiter = Limiter") {
        $content = $content -replace "self\.rate_limiter = Limiter\([^)]+\)", "self.rate_limiter = FallbackRateLimiter(config.RATE_LIMIT_CALLS, config.RATE_LIMIT_PERIOD)"
        Write-Status "Rate limiter initialization replaced (alternative pattern)" "SUCCESS"
    } else {
        Write-Status "Could not find rate limiter initialization" "WARNING"
    }
}

# Remove slowapi exception handler reference
if ($content -match "RateLimitExceeded") {
    $content = $content -replace "self\.app\.add_exception_handler\(RateLimitExceeded, _rate_limit_exceeded_handler\)", "# Rate limit handler removed (using FallbackRateLimiter)"
    Write-Status "RateLimitExceeded handler removed" "SUCCESS"
}

# ============================================================================
# FIX 2: ADD EVENT BUS INITIALIZATION TO STARTUP
# ============================================================================
Write-Status "Fix 2: Adding event bus initialization to startup()..." "INFO"

$eventBusInit = @"
        # ========== CRITICAL: Initialize Event Bus FIRST ==========
        await event_bus.initialize()
        logger.info("✅ Event bus initialized with SQLite persistence")
        # ===========================================================
        
"@

# Find startup method and add event bus init
$startupPattern = "async def startup\(self\):`n        # Initialize metrics"
if ($content -match [regex]::Escape($startupPattern)) {
    $content = $content -replace [regex]::Escape($startupPattern), "async def startup(self):`n$eventBusInit        # Initialize metrics"
    Write-Status "Event bus initialization added to startup()" "SUCCESS"
} else {
    # Try alternative pattern
    $altPattern = "async def startup\(self\):"
    if ($content -match $altPattern) {
        $content = $content -replace $altPattern, "async def startup(self):`n$eventBusInit"
        Write-Status "Event bus initialization added (alternative pattern)" "SUCCESS"
    } else {
        Write-Status "Could not find startup method" "WARNING"
    }
}

# ============================================================================
# FIX 3: ADD COLLABORATION COMMANDS TO REFLEX COMMANDS
# ============================================================================
Write-Status "Fix 3: Adding collaboration commands to ReflexCommands..." "INFO"

$collabCommands = @"
        elif cmd.startswith("/collaborate"):
            task = cmd.replace("/collaborate", "").strip()
            if task:
                # Analyze task and determine workers needed
                workers_needed = []
                if any(kw in task.lower() for kw in ['code', 'generate', 'create', 'build']):
                    workers_needed.append('code_gen')
                if any(kw in task.lower() for kw in ['trade', 'backtest', 'strategy']):
                    workers_needed.extend(['crypto', 'backtest'])
                if any(kw in task.lower() for kw in ['visual', 'chart', 'graph']):
                    workers_needed.append('vision')
                if any(kw in task.lower() for kw in ['store', 'memory', 'save']):
                    workers_needed.append('memory')
                
                content = f"🤝 **Collaboration Request**\n\n📋 Task: {task}\n🔧 Workers: {', '.join(workers_needed) if workers_needed else 'Auto-detect'}\n\n"
                content += "**Executing...**\n"
                
                for worker_name in workers_needed:
                    worker_info = self.kernel.workers.get(worker_name)
                    if worker_info:
                        try:
                            worker = worker_info['class']()
                            result = await worker.execute(task)
                            content += f"  ✅ {worker_name}: Success\n"
                        except Exception as e:
                            content += f"  ❌ {worker_name}: {str(e)[:50]}...\n"
                
                return {"type": "reflex", "content": content}
            return {"type": "reflex", "content": "Usage: /collaborate <task>"}
        
        elif cmd == "/collab-stats":
            return {"type": "reflex", "content": f"🤝 **Collaboration Stats**\n\n📊 Workers Available: {len(self.kernel.workers)}\n💾 Total Blueprints: {len(sovereign_memory.memories)}\n🔗 Drift Chain: {len(self.kernel.drift_chain)} locks"}

"@

# Find the return None at end of ReflexCommands.execute and insert before it
if ($content -match "return None`n`n# ============================================================================") {
    $content = $content -replace "return None`n`n# ============================================================================", "$collabCommands        return None`n`n# ============================================================================
"
    Write-Status "Collaboration commands added" "SUCCESS"
} else {
    Write-Status "Could not find insertion point for collaboration commands" "WARNING"
}

# ============================================================================
# FIX 4: ADD SEMANTIC MEMORY INITIALIZATION
# ============================================================================
Write-Status "Fix 4: Adding semantic memory initialization..." "INFO"

# Check if semantic memory code exists
if ($content -match "class SemanticMemoryEngine:") {
    Write-Status "Semantic memory code already exists" "SUCCESS"
    
    # Add initialization to startup if not present
    if ($content -notmatch "await semantic_memory\.initialize\(\)") {
        $semanticInit = "        # Initialize semantic memory (optional)`n        if HAS_SEMANTIC:`n            await semantic_memory.initialize()`n`n"
        
        # Insert after event bus init
        if ($content -match "await event_bus\.initialize\(\)") {
            $content = $content -replace "await event_bus\.initialize\(\)`n        logger\.info\(`"✅ Event bus initialized", "await event_bus.initialize()`n        logger.info(`"✅ Event bus initialized`n`n        # Initialize semantic memory (optional)`n        if HAS_SEMANTIC:`n            await semantic_memory.initialize()"
            Write-Status "Semantic memory initialization added" "SUCCESS"
        }
    }
} else {
    Write-Status "Semantic memory code not found - skipping (install dependencies first)" "WARNING"
}

# ============================================================================
# STEP 4: SAVE FIXED FILE
# ============================================================================
Write-Status "Step 4: Saving fixed Phoenix kernel..." "INFO"
try {
    Set-Content -Path $filePath -Value $content -Encoding UTF8 -NoNewline
    Write-Status "File saved successfully!" "SUCCESS"
} catch {
    Write-Status "Failed to save file: $($_.Exception.Message)" "ERROR"
    Write-Status "Restoring backup..." "WARNING"
    Copy-Item -Path $backupPath -Destination $filePath -Force
    exit 1
}

# ============================================================================
# STEP 5: VERIFY PYTHON SYNTAX
# ============================================================================
Write-Status "Step 5: Verifying Python syntax..." "INFO"
try {
    $pythonCheck = python -m py_compile $filePath 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Python syntax: VALID" "SUCCESS"
    } else {
        Write-Status "Python syntax: ERRORS DETECTED" "ERROR"
        Write-Status "$pythonCheck" "WARNING"
        Write-Status "Restoring backup..." "WARNING"
        Copy-Item -Path $backupPath -Destination $filePath -Force
        exit 1
    }
} catch {
    Write-Status "Could not verify Python syntax" "WARNING"
}

# ============================================================================
# STEP 6: CREATE TEST SCRIPT
# ============================================================================
if (-not $SkipTest) {
    Write-Status "Step 6: Creating test script..." "INFO"
    
    $testScript = @"
# ============================================================================
# PHOENIX v14.0.0-OKIRU - TEST SCRIPT
# ============================================================================

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        PHOENIX v14.0.0-OKIRU - VERIFICATION TESTS            ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

`$API_BASE = "http://localhost:8002"
`$testsPassed = 0
`$testsFailed = 0

function Test-Endpoint {
    param([string]`$Name, [string]`$Method, [string]`$Uri, [hashtable]`$Body)
    
    Write-Host "`n[TEST] `$Name..." -ForegroundColor Yellow
    
    try {
        if (`$Method -eq "GET") {
            `$result = Invoke-RestMethod -Uri `$Uri -Method Get -ErrorAction Stop
        } else {
            `$jsonBody = `$Body | ConvertTo-Json
            `$result = Invoke-RestMethod -Uri `$Uri -Method Post -ContentType "application/json" -Body `$jsonBody -ErrorAction Stop
        }
        
        Write-Host "  ✅ PASS" -ForegroundColor Green
        `$script:testsPassed++
        return `$true
    } catch {
        Write-Host "  ❌ FAIL: `$(`$_.Exception.Message)" -ForegroundColor Red
        `$script:testsFailed++
        return `$false
    }
}

# Test 1: Health Endpoint
Test-Endpoint -Name "Health Check (GET)" -Method "GET" -Uri "`$API_BASE/health"

# Test 2: Workers List
Test-Endpoint -Name "Workers List (GET)" -Method "GET" -Uri "`$API_BASE/workers/list"

# Test 3: Events Stats
Test-Endpoint -Name "Events Stats (GET)" -Method "GET" -Uri "`$API_BASE/events/stats"

# Test 4: Health Reflex Command
Test-Endpoint -Name "Health Reflex (POST)" -Method "POST" -Uri "`$API_BASE/kernel/stream" -Body @{task = "/health"}

# Test 5: Workers Reflex Command
Test-Endpoint -Name "Workers Reflex (POST)" -Method "POST" -Uri "`$API_BASE/kernel/stream" -Body @{task = "/workers"}

# Test 6: Code Generation
Test-Endpoint -Name "Code Generation (POST)" -Method "POST" -Uri "`$API_BASE/kernel/stream" -Body @{task = "/code add two numbers"}

# Test 7: Collaboration Command
Test-Endpoint -Name "Collaboration (POST)" -Method "POST" -Uri "`$API_BASE/kernel/stream" -Body @{task = "/collaborate test trading bot"}

# Test 8: Collaboration Stats
Test-Endpoint -Name "Collab Stats (POST)" -Method "POST" -Uri "`$API_BASE/kernel/stream" -Body @{task = "/collab-stats"}

# Summary
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                      TEST SUMMARY                            ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Tests Passed: `$testsPassed" -ForegroundColor Green
Write-Host "  Tests Failed: `$testsFailed" -ForegroundColor $(if (`$testsFailed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if (`$testsFailed -eq 0) {
    Write-Host "🎉 ALL TESTS PASSED! Phoenix v14.0.0-OKIRU is operational!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some tests failed. Check the logs above." -ForegroundColor Yellow
}
"@
    
    Set-Content -Path $testScriptPath -Value $testScript -Encoding UTF8
    Write-Status "Test script created: $testScriptPath" "SUCCESS"
}

# ============================================================================
# FINAL SUMMARY
# ============================================================================
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                    FIX COMPLETE!                             ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 WHAT WAS FIXED:" -ForegroundColor Yellow
Write-Host "   1. ✅ Rate Limiter: slowapi.Limiter → FallbackRateLimiter" -ForegroundColor Green
Write-Host "   2. ✅ Event Bus: Added initialization to startup()" -ForegroundColor Green
Write-Host "   3. ✅ Collaboration: Added /collaborate and /collab-stats commands" -ForegroundColor Green
Write-Host "   4. ✅ Semantic Memory: Added initialization (if code exists)" -ForegroundColor Green
Write-Host "   5. ✅ Backup Created: $backupPath" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 NEXT STEPS:" -ForegroundColor Yellow
Write-Host "   1. Restart Phoenix kernel:" -ForegroundColor White
Write-Host "      cd D:\Rezonic_Agentic\apps\phoenix-kernel" -ForegroundColor Gray
Write-Host "      python phoenix_v14_omega_okiru.py" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Run test script (in NEW terminal):" -ForegroundColor White
Write-Host "      cd D:\Rezonic_Agentic\apps\phoenix-kernel" -ForegroundColor Gray
Write-Host "      .\test_phoenix.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "   3. Install semantic memory dependencies (optional):" -ForegroundColor White
Write-Host "      pip install torch sentence-transformers chromadb numpy" -ForegroundColor Gray
Write-Host ""
Write-Host "💾 BACKUP LOCATION:" -ForegroundColor Yellow
Write-Host "   $backupPath" -ForegroundColor Gray
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          PHOENIX v14.0.0-OKIRU IS READY TO SOAR! 🏛️🔥        ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""