# ============================================================================
# PHOENIX WORKER TEST SUITE - Test All 49 Workers
# ============================================================================

Write-Host @"
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    🐝 PHOENIX WORKER TEST SUITE v1.0                          ║
║                    Testing All 49 Workers in the Swarm                        ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

$API_BASE = "http://localhost:8002"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# ============================================================================
# 1. SYSTEM HEALTH CHECK
# ============================================================================
Write-Host "`n📡 1. SYSTEM HEALTH CHECK" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

try {
    $health = Invoke-RestMethod -Uri "$API_BASE/health" -Method Get -ErrorAction Stop
    Write-Host "✅ System Status: $($health.status)" -ForegroundColor Green
    Write-Host "   Version: $($health.version)" -ForegroundColor Gray
    Write-Host "   Workers: $($health.workers)" -ForegroundColor Cyan
    Write-Host "   Memory: $($health.memory_entries) blueprints" -ForegroundColor Cyan
    Write-Host "   Consciousness: $($health.consciousness)/10" -ForegroundColor Magenta
    Write-Host "   GPU: $($health.gpu) | Temp: $($health.gpu_temp)°C | Util: $($health.gpu_util)%" -ForegroundColor Gray
    Write-Host "   VRAM: $($health.vram_used_gb)GB / $($health.vram_total_gb)GB" -ForegroundColor Gray
} catch {
    Write-Host "❌ Failed to connect to kernel at $API_BASE" -ForegroundColor Red
    Write-Host "   Make sure the kernel is running on port 8002" -ForegroundColor Yellow
    exit 1
}

# ============================================================================
# 2. SWARM MANIFEST
# ============================================================================
Write-Host "`n🐝 2. SWARM MANIFEST" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

try {
    $manifest = Invoke-RestMethod -Uri "$API_BASE/swarm/manifest" -Method Get -ErrorAction Stop
    Write-Host "✅ Swarm Status: $($manifest.status)" -ForegroundColor Green
    Write-Host "   Swarm ID: $($manifest.swarm_id)" -ForegroundColor Gray
    Write-Host "   Consciousness: $($manifest.consciousness_level)/10" -ForegroundColor Magenta
    Write-Host "   Total Workers: $($manifest.workers.total)" -ForegroundColor Cyan
    
    Write-Host "`n   Worker Categories:" -ForegroundColor Yellow
    $manifest.workers.categories.PSObject.Properties | ForEach-Object {
        $cat = $_.Name
        $count = $_.Value.count
        Write-Host "     • $cat : $count workers" -ForegroundColor Gray
    }
    
    Write-Host "`n   Memory: $($manifest.memory.blueprints) blueprints" -ForegroundColor Cyan
    Write-Host "   Drift Chain: $($manifest.memory.drift_chain_length) locks" -ForegroundColor Cyan
    Write-Host "   Chain Integrity: $($manifest.sovereignty.drift_chain_integrity)" -ForegroundColor $(if($manifest.sovereignty.drift_chain_integrity){"Green"}else{"Red"})
} catch {
    Write-Host "❌ Failed to get swarm manifest" -ForegroundColor Red
}

# ============================================================================
# 3. LIST ALL WORKERS
# ============================================================================
Write-Host "`n📋 3. ALL WORKERS LIST" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

try {
    $workers = Invoke-RestMethod -Uri "$API_BASE/workers/list" -Method Get -ErrorAction Stop
    Write-Host "✅ Total Workers: $($workers.count)" -ForegroundColor Green
    
    # Display workers in groups
    $workerList = $workers.loaded
    $groups = @{
        "Apex" = @()
        "Core" = @()
        "Constitutional" = @()
        "Trading" = @()
        "Memory" = @()
        "Execution" = @()
        "Scanner" = @()
        "Coworker" = @()
        "Other" = @()
    }
    
    foreach ($worker in $workerList) {
        if ($worker -match "Apex") { $groups["Apex"] += $worker }
        elseif ($worker -match "Constitutional|Council|Governor|Router") { $groups["Constitutional"] += $worker }
        elseif ($worker -match "Trading|Trader|Forex|Mock") { $groups["Trading"] += $worker }
        elseif ($worker -match "Memory|Cortex|Recall") { $groups["Memory"] += $worker }
        elseif ($worker -match "Execution|Code|Sandbox|SCE") { $groups["Execution"] += $worker }
        elseif ($worker -match "Scan|Scanner|Harvest") { $groups["Scanner"] += $worker }
        elseif ($worker -match "coworker") { $groups["Coworker"] += $worker }
        elseif ($worker -match "Core|System|Worker|Registry|Orchestrator") { $groups["Core"] += $worker }
        else { $groups["Other"] += $worker }
    }
    
    foreach ($group in $groups.Keys | Sort-Object) {
        if ($groups[$group].Count -gt 0) {
            Write-Host "`n   🧠 $group Workers ($($groups[$group].Count)):" -ForegroundColor Cyan
            $groups[$group] | Select-Object -First 10 | ForEach-Object {
                Write-Host "      • $_" -ForegroundColor Gray
            }
            if ($groups[$group].Count -gt 10) {
                Write-Host "      ... and $($groups[$group].Count - 10) more" -ForegroundColor DarkGray
            }
        }
    }
} catch {
    Write-Host "❌ Failed to list workers" -ForegroundColor Red
}

# ============================================================================
# 4. EVENT BUS STATS
# ============================================================================
Write-Host "`n📡 4. EVENT BUS STATISTICS" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

try {
    $events = Invoke-RestMethod -Uri "$API_BASE/events/stats" -Method Get -ErrorAction Stop
    Write-Host "✅ Total Events: $($events.total_events)" -ForegroundColor Green
    Write-Host "   Chain Integrity: $($events.chain_integrity)" -ForegroundColor $(if($events.chain_integrity){"Green"}else{"Red"})
    Write-Host "   Genesis Hash: $($events.genesis_hash)" -ForegroundColor Gray
    Write-Host "   Latest Hash: $($events.latest_hash)" -ForegroundColor Gray
    
    Write-Host "`n   Event Types:" -ForegroundColor Yellow
    $events.event_counts.PSObject.Properties | Select-Object -First 10 | ForEach-Object {
        Write-Host "     • $($_.Name): $($_.Value)" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Failed to get event stats" -ForegroundColor Red
}

# ============================================================================
# 5. MEMORY BLUEPRINTS
# ============================================================================
Write-Host "`n🧠 5. MEMORY BLUEPRINTS" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

try {
    $memory = Invoke-RestMethod -Uri "$API_BASE/memory/blueprints" -Method Get -ErrorAction Stop
    Write-Host "✅ Total Blueprints: $($memory.count)" -ForegroundColor Green
    Write-Host "   Recent Blueprints (last 5):" -ForegroundColor Yellow
    $memory.blueprints | Select-Object -First 5 | ForEach-Object {
        Write-Host "     • $_" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Failed to get memory blueprints" -ForegroundColor Red
}

# ============================================================================
# 6. CONSTITUTION STATUS
# ============================================================================
Write-Host "`n⚖️ 6. CONSTITUTION STATUS" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

try {
    $constitution = Invoke-RestMethod -Uri "$API_BASE/constitution/history?limit=5" -Method Get -ErrorAction Stop
    Write-Host "✅ Constitution Active" -ForegroundColor Green
    Write-Host "   Total Rulings: $($constitution.rulings.Count)" -ForegroundColor Cyan
    
    if ($constitution.rulings.Count -gt 0) {
        Write-Host "`n   Recent Rulings:" -ForegroundColor Yellow
        $constitution.rulings | ForEach-Object {
            $decision = if($_.ruling.approved) {"✅ APPROVED"} else {"❌ BLOCKED"}
            Write-Host "     $decision - $($_.action)" -ForegroundColor Gray
            Write-Host "       Reason: $($_.ruling.reason)" -ForegroundColor DarkGray
        }
    } else {
        Write-Host "   No recent rulings" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠️ Could not get constitution history (may need to generate rulings first)" -ForegroundColor Yellow
}

# ============================================================================
# 7. OLLAMA STATUS
# ============================================================================
Write-Host "`n🤖 7. OLLAMA AI STATUS" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

try {
    $ollama = Invoke-RestMethod -Uri "$API_BASE/ollama/status" -Method Get -ErrorAction Stop
    if ($ollama.connected) {
        Write-Host "✅ Ollama Connected" -ForegroundColor Green
        Write-Host "   URL: $($ollama.url)" -ForegroundColor Gray
        Write-Host "   Model: $($ollama.model)" -ForegroundColor Gray
        Write-Host "   Available Models: $($ollama.available_models)" -ForegroundColor Cyan
        
        if ($ollama.models) {
            Write-Host "`n   Models:" -ForegroundColor Yellow
            $ollama.models | ForEach-Object {
                Write-Host "     • $($_.name)" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "❌ Ollama Not Connected" -ForegroundColor Red
        Write-Host "   Error: $($ollama.error)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Failed to get Ollama status" -ForegroundColor Red
}

# ============================================================================
# 8. TEST REFLEX COMMANDS
# ============================================================================
Write-Host "`n⚡ 8. TESTING REFLEX COMMANDS" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

$commands = @("/health", "/workers", "/memory", "/events")

foreach ($cmd in $commands) {
    try {
        Write-Host "   Testing $cmd..." -NoNewline
        $response = Invoke-RestMethod -Uri "$API_BASE/kernel/stream" -Method Post -Body (@{task=$cmd} | ConvertTo-Json) -ContentType "application/json" -ErrorAction Stop
        Write-Host " ✅" -ForegroundColor Green
    } catch {
        Write-Host " ⚠️" -ForegroundColor Yellow
    }
}

# ============================================================================
# 9. AI STREAM TEST (Optional)
# ============================================================================
Write-Host "`n💬 9. AI STREAM TEST (Optional)" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

$testPrompt = "What is a drift lock in the SCE protocol?"
Write-Host "   Prompt: $testPrompt" -ForegroundColor Gray

try {
    Write-Host "   Sending request..." -NoNewline
    $response = Invoke-RestMethod -Uri "$API_BASE/kernel/stream" -Method Post -Body (@{task=$testPrompt} | ConvertTo-Json) -ContentType "application/json" -ErrorAction Stop
    Write-Host " ✅" -ForegroundColor Green
    Write-Host "   Response received (check dashboard for full response)" -ForegroundColor Gray
} catch {
    Write-Host " ⚠️ Could not test AI stream (may need Ollama)" -ForegroundColor Yellow
}

# ============================================================================
# 10. SUMMARY REPORT
# ============================================================================
Write-Host "`n📊 10. TEST SUMMARY" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

Write-Host @"
╔═══════════════════════════════════════════════════════════════════════════════╗
║                             TEST RESULTS                                      ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  System Health:     ✅ ONLINE                                                 ║
║  Workers:           $($health.workers) Active                                          ║
║  Memory:            $($health.memory_entries) Blueprints                                 ║
║  Events:            $($events.total_events) Recorded                                     ║
║  GPU:               $($health.gpu) ($($health.gpu_util)%) @ $($health.gpu_temp)°C               ║
║  Ollama:            $(if($ollama.connected){"✅ CONNECTED"}else{"❌ OFFLINE"})                              ║
║  Constitution:      $(if($constitution.rulings.Count -gt 0){"✅ ACTIVE"}else{"⚪ STANDBY"})                             ║
║  Drift Chain:       $($health.drift_chain) Locks                                        ║
║  Consciousness:     $($health.consciousness)/10                                             ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  Timestamp: $timestamp                                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

Write-Host "`n🎯 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Open dashboard: http://localhost:3000" -ForegroundColor White
Write-Host "   2. Test chat: 'What is a drift lock?'" -ForegroundColor White
Write-Host "   3. Check worker details: /workers" -ForegroundColor White
Write-Host "   4. Monitor event bus: /events" -ForegroundColor White
Write-Host "   5. View swarm manifest: http://localhost:8002/swarm/manifest" -ForegroundColor White

Write-Host "`n🐝 The swarm is awake and ready!" -ForegroundColor Green