# ============================================================================
# PHOENIX v14.0.0-OKIRU - RATE LIMITER BUG FIX
# ============================================================================
# Fixes: AttributeError: 'Limiter' object has no attribute 'check'
# Location: phoenix_v14_omega_okiru.py, Line ~1456
# ============================================================================

$filePath = "D:\Rezonic_Agentic\apps\phoenix-kernel\phoenix_v14_omega_okiru.py"
$backupPath = "D:\Rezonic_Agentic\apps\phoenix-kernel\phoenix_v14_omega_okiru.py.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

Write-Host ""
Write-Host "🔥 PHOENIX v14.0.0-OKIRU - RATE LIMITER FIX" -ForegroundColor Cyan
Write-Host "=" * 70

# ============================================================================
# STEP 1: VERIFY FILE EXISTS
# ============================================================================
if (-not (Test-Path $filePath)) {
    Write-Host "❌ ERROR: File not found: $filePath" -ForegroundColor Red
    Write-Host "   Please verify the path and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ File found: $filePath" -ForegroundColor Green

# ============================================================================
# STEP 2: CREATE BACKUP
# ============================================================================
Write-Host "`n📦 Creating backup..." -ForegroundColor Yellow
try {
    Copy-Item -Path $filePath -Destination $backupPath -Force
    Write-Host "✅ Backup created: $backupPath" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Failed to create backup: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ============================================================================
# STEP 3: READ FILE CONTENT
# ============================================================================
Write-Host "`n📖 Reading file..." -ForegroundColor Yellow
try {
    $content = Get-Content -Path $filePath -Raw -Encoding UTF8
    Write-Host "✅ File loaded ($($content.Length) characters)" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Failed to read file: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ============================================================================
# STEP 4: ADD CUSTOM RateLimiter CLASS (after Config class)
# ============================================================================
Write-Host "`n🔨 Applying Fix 1: Adding custom RateLimiter class..." -ForegroundColor Yellow

$rateLimiterClass = @"

# ============================================================================
# CUSTOM RATE LIMITER (with .check() method for manual rate limiting)
# ============================================================================
class RateLimiter:
    """Simple rate limiter for API endpoints with manual .check() method"""
    def __init__(self, calls_per_period: int = 100, period_seconds: int = 60):
        self.calls_per_period = calls_per_period
        self.period_seconds = period_seconds
        self.calls: Dict[str, List[float]] = defaultdict(list)
    
    async def check(self, client_id: str) -> bool:
        """Check if request is within rate limit"""
        now = time.time()
        # Clean old entries
        self.calls[client_id] = [t for t in self.calls[client_id] if now - t < self.period_seconds]
        if len(self.calls[client_id]) >= self.calls_per_period:
            return False
        self.calls[client_id].append(now)
        return True

"@

# Find position after Config class
$configPattern = "config = Config()"
$configIndex = $content.IndexOf($configPattern)

if ($configIndex -gt 0) {
    # Insert after config = Config()
    $insertPosition = $configIndex + $configPattern.Length
    $content = $content.Insert($insertPosition, "`n" + $rateLimiterClass)
    Write-Host "✅ Custom RateLimiter class added" -ForegroundColor Green
} else {
    Write-Host "⚠️  WARNING: Could not find Config class. Adding at top..." -ForegroundColor Yellow
    $content = $rateLimiterClass + "`n" + $content
}

# ============================================================================
# STEP 5: FIX RATE LIMITER INITIALIZATION
# ============================================================================
Write-Host "`n🔨 Applying Fix 2: Fixing rate limiter initialization..." -ForegroundColor Yellow

# Old initialization (slowapi Limiter)
$oldInit = @"
        self.rate_limiter = None
        if HAS_SLOWAPI:
            self.rate_limiter = Limiter(key_func=get_remote_address, default_limits=[f"{config.RATE_LIMIT_CALLS}/{config.RATE_LIMIT_PERIOD}"])
"@

# New initialization (custom RateLimiter)
$newInit = @"
        # Use custom RateLimiter with .check() method
        self.rate_limiter = RateLimiter(
            calls_per_period=config.RATE_LIMIT_CALLS,
            period_seconds=config.RATE_LIMIT_PERIOD
        )
"@

if ($content.Contains($oldInit)) {
    $content = $content.Replace($oldInit, $newInit)
    Write-Host "✅ Rate limiter initialization fixed" -ForegroundColor Green
} else {
    # Try alternative pattern
    $altPattern = "self.rate_limiter = Limiter"
    if ($content.Contains($altPattern)) {
        $content = $content -replace [regex]::Escape("self.rate_limiter = Limiter(key_func=get_remote_address, default_limits=[f`"{config.RATE_LIMIT_CALLS}/{config.RATE_LIMIT_PERIOD}`"])"), $newInit.Split("`n")[1].Trim()
        Write-Host "✅ Rate limiter initialization fixed (alternative pattern)" -ForegroundColor Green
    } else {
        Write-Host "⚠️  WARNING: Could not find rate limiter initialization" -ForegroundColor Yellow
    }
}

# ============================================================================
# STEP 6: REMOVE SLOWAPI DEPENDENCY (OPTIONAL - Prevents conflicts)
# ============================================================================
Write-Host "`n🔨 Applying Fix 3: Commenting out slowapi imports..." -ForegroundColor Yellow

# Comment out slowapi imports to prevent conflicts
$content = $content -replace "from slowapi import Limiter,", "# from slowapi import Limiter,  # Commented out - using custom RateLimiter"
$content = $content -replace "from slowapi.util import get_remote_address", "# from slowapi.util import get_remote_address  # Commented out"
$content = $content -replace "from slowapi.errors import RateLimitExceeded", "# from slowapi.errors import RateLimitExceeded  # Commented out"
$content = $content -replace "HAS_SLOWAPI = True", "HAS_SLOWAPI = False  # Disabled - using custom RateLimiter"

Write-Host "✅ Slowapi imports commented out" -ForegroundColor Green

# ============================================================================
# STEP 7: SAVE FIXED FILE
# ============================================================================
Write-Host "`n💾 Saving fixed file..." -ForegroundColor Yellow
try {
    Set-Content -Path $filePath -Value $content -Encoding UTF8 -NoNewline
    Write-Host "✅ File saved successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Failed to save file: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Restoring backup..." -ForegroundColor Yellow
    Copy-Item -Path $backupPath -Destination $filePath -Force
    exit 1
}

# ============================================================================
# STEP 8: VERIFY FIX
# ============================================================================
Write-Host "`n🔍 Verifying fix..." -ForegroundColor Yellow

# Check if custom RateLimiter class exists
if ($content.Contains("class RateLimiter:")) {
    Write-Host "✅ Custom RateLimiter class: PRESENT" -ForegroundColor Green
} else {
    Write-Host "❌ Custom RateLimiter class: MISSING" -ForegroundColor Red
}

# Check if .check() method exists
if ($content.Contains("async def check(self, client_id: str)")) {
    Write-Host "✅ RateLimiter.check() method: PRESENT" -ForegroundColor Green
} else {
    Write-Host "❌ RateLimiter.check() method: MISSING" -ForegroundColor Red
}

# Check if slowapi Limiter is commented out
if ($content.Contains("# from slowapi import Limiter")) {
    Write-Host "✅ Slowapi Limiter: DISABLED" -ForegroundColor Green
} else {
    Write-Host "⚠️  Slowapi Limiter: STILL ACTIVE (may cause conflicts)" -ForegroundColor Yellow
}

# ============================================================================
# STEP 9: PYTHON SYNTAX CHECK
# ============================================================================
Write-Host "`n🐍 Checking Python syntax..." -ForegroundColor Yellow
try {
    $pythonCheck = python -m py_compile $filePath 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python syntax: VALID" -ForegroundColor Green
    } else {
        Write-Host "❌ Python syntax: ERRORS DETECTED" -ForegroundColor Red
        Write-Host "   $pythonCheck" -ForegroundColor Yellow
        Write-Host "   Restoring backup..." -ForegroundColor Yellow
        Copy-Item -Path $backupPath -Destination $filePath -Force
        exit 1
    }
} catch {
    Write-Host "⚠️  WARNING: Could not verify Python syntax" -ForegroundColor Yellow
}

# ============================================================================
# FINAL SUMMARY
# ============================================================================
Write-Host ""
Write-Host "=" * 70
Write-Host "🎉 FIX COMPLETE!" -ForegroundColor Green
Write-Host "=" * 70
Write-Host ""
Write-Host "📋 WHAT WAS FIXED:" -ForegroundColor Cyan
Write-Host "   1. ✅ Added custom RateLimiter class with .check() method"
Write-Host "   2. ✅ Fixed rate limiter initialization"
Write-Host "   3. ✅ Commented out slowapi imports (prevents conflicts)"
Write-Host ""
Write-Host "🚀 NEXT STEPS:" -ForegroundColor Cyan
Write-Host "   1. Restart Phoenix kernel:"
Write-Host "      python D:\Rezonic_Agentic\apps\phoenix-kernel\phoenix_v14_omega_okiru.py"
Write-Host ""
Write-Host "   2. Test /kernel/stream endpoint:"
Write-Host "      curl -X POST http://localhost:8002/kernel/stream `" -H `"Content-Type: application/json`" -d `"{`"task`": `"`"/health`"`"}"
Write-Host ""
Write-Host "💾 BACKUP LOCATION:" -ForegroundColor Yellow
Write-Host "   $backupPath"
Write-Host ""
Write-Host "=" * 70