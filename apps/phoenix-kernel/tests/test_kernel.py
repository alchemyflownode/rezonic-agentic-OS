# tests/test_kernel.py
"""
Unit tests for Phoenix Kernel.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rezonic_unified_v15 import PhoenixKernel

@pytest.fixture
def client():
    """Create test client for the kernel"""
    kernel = PhoenixKernel()
    # Use the correct TestClient initialization
    return TestClient(kernel.app)  # This is correct

def test_health(client):
    """Test health endpoint returns correct status"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "workers" in data
    assert "ollama" in data

def test_kill_status(client):
    """Test kill switch status endpoint"""
    response = client.get("/kill/status")
    assert response.status_code == 200
    data = response.json()
    assert "active" in data
    assert data["active"] == False

def test_portfolio(client):
    """Test portfolio endpoint returns balance"""
    response = client.get("/portfolio")
    assert response.status_code == 200
    data = response.json()
    assert "balance" in data
    assert data["balance"] > 0

def test_pulse(client):
    """Test pulse endpoint returns score between 0-100"""
    response = client.get("/pulse")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert 0 <= data["total"] <= 100

def test_validate_trade(client):
    """Test trade validation endpoint"""
    response = client.post("/validate", json={
        "symbol": "BTCUSDT",
        "amount": 1000,
        "price": 50000,
        "stop_loss": 49000
    })
    assert response.status_code == 200
    data = response.json()
    assert "approved" in data
    assert "violations" in data

def test_memory_stats(client):
    """Test memory statistics endpoint"""
    response = client.get("/memory/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_blueprints" in data

def test_workers_list(client):
    """Test workers list endpoint"""
    response = client.get("/workers/list")
    assert response.status_code == 200
    data = response.json()
    assert "workers" in data
    assert data["count"] > 0

def test_constitution_rules(client):
    """Test constitution rules endpoint"""
    response = client.get("/constitution/rules")
    assert response.status_code == 200
    data = response.json()
    assert "max_risk_per_trade_pct" in data
    assert "require_stop_loss" in data

def test_symbiote_status(client):
    """Test symbiote status endpoint"""
    response = client.get("/symbiote/status")
    assert response.status_code == 200
    data = response.json()
    assert "initialized" in data
    assert "providers" in data

def test_404(client):
    """Test non-existent endpoint returns 404"""
    response = client.get("/nonexistent")
    assert response.status_code == 404
