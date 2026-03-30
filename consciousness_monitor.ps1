# consciousness_monitor.ps1
# Real-time monitor for Trading Consciousness

Write-Host "🧠 TRADING CONSCIOUSNESS MONITOR" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Yellow
Write-Host ""

$counter = 0

while ($true) {
    Clear-Host
    Write-Host "🧠 TRADING CONSCIOUSNESS - REAL-TIME MONITOR" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host "Refresh #$counter | $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray
    Write-Host ""
    
    try {
        # Get consciousness state
        $state = Invoke-RestMethod -Uri "http://localhost:8002/api/v1/consciousness/state" -TimeoutSec 3
        Write-Host "📊 CONSCIOUSNESS STATE:" -ForegroundColor Yellow
        Write-Host "  Status: $($state.status)" -ForegroundColor $(if($state.status -eq "active"){"Green"}else{"Red"})
        Write-Host "  Total Simulations: $($state.total_simulations)" -ForegroundColor White
        Write-Host "  Best Strategy: $($state.best_strategy)" -ForegroundColor Green
        Write-Host ""
        
        # Show strategy performance
        Write-Host "📈 STRATEGY PERFORMANCE:" -ForegroundColor Yellow
        $state.strategies.PSObject.Properties.Name | ForEach-Object {
            $s = $state.strategies.$_
            if ($s.total_trades -gt 0) {
                $winColor = if ($s.win_rate -gt 0.5) { "Green" } else { "Red" }
                Write-Host "  • $($_): Win Rate = $([math]::Round($s.win_rate * 100, 1))% | Trades = $($s.total_trades) | PnL = $$([math]::Round($s.total_pnl, 2))" -ForegroundColor $winColor
            } else {
                Write-Host "  • $($_): Waiting for first simulation..." -ForegroundColor Gray
            }
        }
        
        # Get recent simulations
        $sims = Invoke-RestMethod -Uri "http://localhost:8002/api/v1/consciousness/simulations?limit=5" -TimeoutSec 3
        if ($sims.count -gt 0) {
            Write-Host "`n🔄 RECENT SIMULATIONS:" -ForegroundColor Yellow
            $sims.simulations | ForEach-Object {
                $result = if ($_.success) { "✓ WIN" } else { "✗ LOSS" }
                $resultColor = if ($_.success) { "Green" } else { "Red" }
                Write-Host "  $result | $($_.strategy) | $($_.action) | PnL: $$([math]::Round($_.pnl, 2)) | Confidence: $([math]::Round($_.confidence * 100, 0))%" -ForegroundColor $resultColor
                Write-Host "    Reasoning: $($_.reasoning)" -ForegroundColor Gray
            }
        }
        
        # Get autonomous status
        try {
            $auto = Invoke-RestMethod -Uri "http://localhost:8002/api/v1/consciousness/autonomous/status" -TimeoutSec 3
            Write-Host "`n🤖 AUTONOMOUS TRADING:" -ForegroundColor Yellow
            Write-Host "  Enabled: $($auto.enabled)" -ForegroundColor $(if($auto.enabled){"Green"}else{"Red"})
            Write-Host "  Interval: $($auto.interval)s" -ForegroundColor Gray
            Write-Host "  Executions: $($auto.executions)" -ForegroundColor White
        } catch {
            # Autonomous not available yet
        }
        
        # Get insights
        $insights = Invoke-RestMethod -Uri "http://localhost:8002/api/v1/consciousness/insights" -TimeoutSec 3
        Write-Host "`n💡 AI INSIGHTS:" -ForegroundColor Yellow
        Write-Host "  Market Sentiment: $([math]::Round($insights.market_sentiment, 3))" -ForegroundColor $(if($insights.market_sentiment -gt 0){"Green"}else{"Red"})
        Write-Host "  Volatility: $([math]::Round($insights.volatility, 3))" -ForegroundColor Yellow
        Write-Host "  Risk Appetite: $([math]::Round($insights.risk_appetite, 3))" -ForegroundColor Cyan
        Write-Host "  Recommendation: $($insights.recommended_action)" -ForegroundColor White
        Write-Host "  Learning: $($insights.learning_progress)" -ForegroundColor Gray
        
    } catch {
        Write-Host "⚠ Waiting for consciousness to initialize..." -ForegroundColor Yellow
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Gray
    }
    
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host "Updating in 3 seconds... (Press Ctrl+C to stop)" -ForegroundColor Gray
    Start-Sleep -Seconds 3
    $counter++
}
