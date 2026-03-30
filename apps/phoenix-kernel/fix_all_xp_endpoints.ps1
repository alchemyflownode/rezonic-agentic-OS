<#
.SYNOPSIS
    Fixes all XP endpoints in kernel.py by adding XP code INSIDE the async functions
    and removing any stray XP blocks.

.DESCRIPTION
    This script:
    1. Creates a backup of kernel.py
    2. Finds and fixes api_rezcoder_review, api_rezcoder_fix, and api_mcp_generate
    3. Removes any duplicate/stray XP blocks outside functions
    4. Validates syntax after changes
    5. Shows you exactly what changed
#>

[CmdletBinding()]
param(
    [string]$FilePath = "kernel.py",
    [switch]$DryRun,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

# Colors
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Cyan = "Cyan"

Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║  🔧 Phoenix XP Endpoint Auto-Fixer                           ║
║  Adds XP tracking to RezCoder and MCP endpoints              ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# Check if file exists
if (-not (Test-Path $FilePath)) {
    Write-Host "❌ File not found: $FilePath" -ForegroundColor Red
    exit 1
}

# Create backup
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = "$FilePath.bak.$timestamp"
Copy-Item $FilePath $backup -Force
Write-Host "💾 Backup created: $backup" -ForegroundColor Green

# Read the file
$content = Get-Content $FilePath -Raw -Encoding UTF8
$original = $content

Write-Host "🔍 Scanning for endpoints..." -ForegroundColor Cyan

# ============================================
# 1. FIX api_rezcoder_review
# ============================================
Write-Host "`n📝 Fixing api_rezcoder_review..." -ForegroundColor Yellow

$reviewPattern = @'
(@self\.app\.get\("/api/v1/rezcoder/review"\)\s*
async def api_rezcoder_review\(filepath: str, recursive: bool = False\):.*?
    worker = self\.workers\.get\("rezcoder", \{\}\)\.get\("instance"\).*?
    if not worker:.*?
        return JSONResponse\(\{"error": "RezCoder not available"\}, status_code=503\).*?
    await worker\.initialize\(\).*?
)(return await worker\.execute\("review", file_path=filepath, recursive=recursive\))
'@

$reviewReplacement = @'
$1    result = await worker.execute("review", file_path=filepath, recursive=recursive)
    
    # Add XP for review
    mastery = self.workers.get("mastery", {}).get("instance")
    if mastery:
        await mastery.add_xp("code_review", amount=50, description=f"Reviewed {filepath}", source="rezcoder")
    
    return result
'@

if ($content -match $reviewPattern) {
    $content = $content -replace $reviewPattern, $reviewReplacement
    Write-Host "  ✅ Fixed api_rezcoder_review" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ Could not find review endpoint pattern" -ForegroundColor Yellow
}

# ============================================
# 2. FIX api_rezcoder_fix
# ============================================
Write-Host "📝 Fixing api_rezcoder_fix..." -ForegroundColor Yellow

$fixPattern = @'
(@self\.app\.post\("/api/v1/rezcoder/fix"\)\s*
async def api_rezcoder_fix\(filepath: str, confidence: float = 0\.8, backup: bool = True\):.*?
    worker = self\.workers\.get\("rezcoder", \{\}\)\.get\("instance"\).*?
    if not worker:.*?
        return JSONResponse\(\{"error": "RezCoder not available"\}, status_code=503\).*?
    await worker\.initialize\(\).*?
)(return await worker\.execute\("fix", file_path=filepath, confidence=confidence, backup=backup\))
'@

$fixReplacement = @'
$1    result = await worker.execute("fix", file_path=filepath, confidence=confidence, backup=backup)
    
    # Add XP for fix
    mastery = self.workers.get("mastery", {}).get("instance")
    if mastery:
        await mastery.add_xp("code_fix", amount=100, description=f"Fixed {filepath}", source="rezcoder")
    
    return result
'@

if ($content -match $fixPattern) {
    $content = $content -replace $fixPattern, $fixReplacement
    Write-Host "  ✅ Fixed api_rezcoder_fix" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ Could not find fix endpoint pattern" -ForegroundColor Yellow
}

# ============================================
# 3. FIX api_mcp_generate
# ============================================
Write-Host "📝 Fixing api_mcp_generate..." -ForegroundColor Yellow

$genPattern = @'
(@self\.app\.get\("/api/v1/mcp/generate"\)\s*
async def api_mcp_generate\(intent: str, language: str = "python"\):.*?
    worker = self\.workers\.get\("sovereign_mcp_server", \{\}\)\.get\("instance"\).*?
    if not worker:.*?
        return JSONResponse\(\{"error": "MCP server not available"\}, status_code=503\).*?
    await worker\.initialize\(\).*?
)(return await worker\.execute\(f"generate_code {intent} --language {language}"\))
'@

$genReplacement = @'
$1    result = await worker.execute(f"generate_code {intent} --language {language}")
    
    # Add XP for code generation
    mastery = self.workers.get("mastery", {}).get("instance")
    if mastery:
        await mastery.add_xp("code_generate", amount=75, description=f"Generated code for {intent}", source="mcp")
    
    return result
'@

if ($content -match $genPattern) {
    $content = $content -replace $genPattern, $genReplacement
    Write-Host "  ✅ Fixed api_mcp_generate" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ Could not find generate endpoint pattern" -ForegroundColor Yellow
}

# ============================================
# 4. REMOVE STRAY XP BLOCKS
# ============================================
Write-Host "🧹 Removing stray XP blocks..." -ForegroundColor Yellow

$strayPattern = @'
(?m)^\s*#\s*Add XP for (?:code_review|code_fix|code_generate)\s*\r?\n\s*mastery = self\.workers\.get\("mastery", \{\}\)\.get\("instance"\)\s*\r?\n\s*if mastery:\s*\r?\n\s*await mastery\.add_xp\(.*?\)\s*\r?\n
'@

$content = $content -replace $strayPattern, ""

# ============================================
# 5. VALIDATE CHANGES
# ============================================
if ($DryRun) {
    Write-Host "`n🧪 DRY RUN - No changes written" -ForegroundColor Cyan
    Write-Host "📊 Changes detected: $($original.Length - $content.Length) characters" -ForegroundColor Cyan
    
    # Show diff preview
    $diff = Compare-Object -ReferenceObject ($original -split "`n") -DifferenceObject ($content -split "`n")
    $diff | Where-Object { $_.SideIndicator -eq "<=" } | Select-Object -First 10 | ForEach-Object {
        Write-Host "  - $($_.InputObject)" -ForegroundColor Red
    }
    $diff | Where-Object { $_.SideIndicator -eq "=>" } | Select-Object -First 10 | ForEach-Object {
        Write-Host "  + $($_.InputObject)" -ForegroundColor Green
    }
    exit 0
}

# Write the fixed content
Write-Host "`n💾 Writing changes..." -ForegroundColor Cyan
[System.IO.File]::WriteAllText((Resolve-Path $FilePath).Path, $content, [System.Text.Encoding]::UTF8)

# Validate syntax
Write-Host "🔎 Validating Python syntax..." -ForegroundColor Cyan
$syntaxCheck = python -m py_compile $FilePath 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Syntax validation passed" -ForegroundColor Green
} else {
    Write-Host "❌ Syntax errors found!" -ForegroundColor Red
    Write-Host $syntaxCheck -ForegroundColor Red
    Write-Host "🔄 Restoring backup..." -ForegroundColor Yellow
    Copy-Item $backup $FilePath -Force
    exit 1
}

# ============================================
# 6. VERIFY THE FIX
# ============================================
Write-Host "`n✅ FIX COMPLETE!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Cyan
Write-Host "Fixed endpoints:" -ForegroundColor Yellow
Write-Host "  • api_rezcoder_review  → +50 XP for code_review" -ForegroundColor Green
Write-Host "  • api_rezcoder_fix     → +100 XP for code_fix" -ForegroundColor Green
Write-Host "  • api_mcp_generate     → +75 XP for code_generate" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Cyan

Write-Host @"

📋 Next Steps:
  1. Restart kernel: python kernel.py
  2. Test review: Invoke-RestMethod 'http://127.0.0.1:8002/api/v1/rezcoder/review?filepath=kernel.py'
  3. Check XP: Invoke-RestMethod 'http://127.0.0.1:8002/kernel/stream' -Method POST -Body '{"task":"/xp"}'

💾 Backup saved to: $backup

"@ -ForegroundColor White

exit 0