# monitoring/metrics.py
"""Prometheus metrics for monitoring"""

from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest, CONTENT_TYPE_LATEST
import time
from typing import Optional

# ============================================================================
# TRADE METRICS
# ============================================================================

trades_total = Counter('trades_total', 'Total trades executed', ['exchange', 'symbol', 'side'])
trades_successful = Counter('trades_successful', 'Successful trades', ['exchange', 'symbol'])
trades_failed = Counter('trades_failed', 'Failed trades', ['exchange', 'symbol', 'reason'])
trades_blocked = Counter('trades_blocked', 'Trades blocked by constitution', ['invariant'])

# ============================================================================
# PORTFOLIO METRICS
# ============================================================================

portfolio_value = Gauge('portfolio_value', 'Current portfolio value', ['currency'])
daily_pnl = Gauge('daily_pnl', 'Daily profit/loss', ['currency'])
max_drawdown = Gauge('max_drawdown', 'Maximum drawdown percentage')
open_positions = Gauge('open_positions', 'Number of open positions')

# ============================================================================
# PERFORMANCE METRICS
# ============================================================================

trade_latency = Histogram('trade_latency', 'Trade execution latency', ['exchange'], buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5])
worker_latency = Histogram('worker_latency', 'Worker execution latency', ['worker'])

# ============================================================================
# SYSTEM METRICS
# ============================================================================

workers_active = Gauge('workers_active', 'Number of active workers')
workers_total = Gauge('workers_total', 'Total workers registered')
memory_blueprints = Gauge('memory_blueprints', 'Number of memory blueprints')
drift_chain_length = Gauge('drift_chain_length', 'Length of drift chain')
integrity_score = Gauge('integrity_score', 'System integrity score (0-100)')

# ============================================================================
# EXCHANGE METRICS
# ============================================================================

exchange_connected = Gauge('exchange_connected', 'Exchange connection status', ['exchange'])
exchange_latency = Histogram('exchange_latency', 'Exchange API latency', ['exchange', 'endpoint'])
exchange_rate_limit_remaining = Gauge('exchange_rate_limit_remaining', 'Rate limit remaining', ['exchange'])

# ============================================================================
# CONSTITUTION METRICS
# ============================================================================

invariant_violations = Counter('invariant_violations', 'Invariant violations', ['invariant'])
constitutional_rulings = Counter('constitutional_rulings', 'Constitutional rulings', ['ruling'])

# ============================================================================
# SYSTEM INFO
# ============================================================================

system_info = Info('phoenix', 'Phoenix Kernel Information')
system_info.info({
    'version': '13.3.0',
    'workers': '53',
    'integrity': '98.2'
})

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def record_trade(exchange: str, symbol: str, side: str, success: bool, latency_ms: float = None, error: str = None):
    """Record a trade execution"""
    trades_total.labels(exchange=exchange, symbol=symbol, side=side).inc()
    
    if success:
        trades_successful.labels(exchange=exchange, symbol=symbol).inc()
        if latency_ms:
            trade_latency.labels(exchange=exchange).observe(latency_ms / 1000)
    else:
        reason = error or "unknown"
        trades_failed.labels(exchange=exchange, symbol=symbol, reason=reason[:50]).inc()


def record_blocked_trade(invariant: str):
    """Record a trade blocked by constitution"""
    trades_blocked.labels(invariant=invariant).inc()
    invariant_violations.labels(invariant=invariant).inc()


def update_portfolio(usd_value: float, btc_value: float = None, eth_value: float = None):
    """Update portfolio metrics"""
    portfolio_value.labels(currency="USD").set(usd_value)
    if btc_value:
        portfolio_value.labels(currency="BTC").set(btc_value)
    if eth_value:
        portfolio_value.labels(currency="ETH").set(eth_value)


def update_worker_metrics(worker_name: str, active: bool, latency_ms: float = None):
    """Update worker metrics"""
    if latency_ms:
        worker_latency.labels(worker=worker_name).observe(latency_ms / 1000)


def update_exchange_status(exchange: str, connected: bool, latency_ms: float = None, rate_limit: int = None):
    """Update exchange connection status"""
    exchange_connected.labels(exchange=exchange).set(1 if connected else 0)
    if latency_ms:
        exchange_latency.labels(exchange=exchange, endpoint="health").observe(latency_ms / 1000)
    if rate_limit is not None:
        exchange_rate_limit_remaining.labels(exchange=exchange).set(rate_limit)


__all__ = [
    'trades_total', 'trades_successful', 'trades_failed', 'trades_blocked',
    'portfolio_value', 'daily_pnl', 'max_drawdown', 'open_positions',
    'trade_latency', 'worker_latency',
    'workers_active', 'workers_total', 'memory_blueprints', 'drift_chain_length', 'integrity_score',
    'exchange_connected', 'exchange_latency', 'exchange_rate_limit_remaining',
    'invariant_violations', 'constitutional_rulings', 'system_info',
    'record_trade', 'record_blocked_trade', 'update_portfolio', 'update_worker_metrics', 'update_exchange_status'
]