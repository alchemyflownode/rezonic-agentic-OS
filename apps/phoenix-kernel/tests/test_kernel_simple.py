# tests/test_kernel_simple.py
"""
Simple tests for Phoenix Kernel - uses direct HTTP requests
"""

import requests
import pytest

BASE_URL = "http://127.0.0.1:8002"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    print(f"✅ Health: {data['status']}")

def test_kill_status():
    """Test kill switch status"""
    response = requests.get(f"{BASE_URL}/kill/status")
    assert response.status_code == 200
    data = response.json()
    assert "active" in data
    print(f"✅ Kill Status: active={data['active']}")

def test_portfolio():
    """Test portfolio endpoint"""
    response = requests.get(f"{BASE_URL}/portfolio")
    assert response.status_code == 200
    data = response.json()
    assert "balance" in data
    print(f"✅ Portfolio: ₱{data['balance']:,.0f}")

def test_pulse():
    """Test pulse endpoint"""
    response = requests.get(f"{BASE_URL}/pulse")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    print(f"✅ Pulse: {data['total']}/100 - {data['recommendation']}")

def test_workers_list():
    """Test workers list"""
    response = requests.get(f"{BASE_URL}/workers/list")
    assert response.status_code == 200
    data = response.json()
    assert "workers" in data
    print(f"✅ Workers: {data['count']} workers")

def test_memory_stats():
    """Test memory statistics"""
    response = requests.get(f"{BASE_URL}/memory/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_blueprints" in data
    print(f"✅ Memory: {data['total_blueprints']} blueprints")

def test_constitution_rules():
    """Test constitution rules"""
    response = requests.get(f"{BASE_URL}/constitution/rules")
    assert response.status_code == 200
    data = response.json()
    assert "max_risk_per_trade_pct" in data
    print(f"✅ Constitution: {data['max_risk_per_trade_pct']}% risk limit")

def test_symbiote_status():
    """Test symbiote status"""
    response = requests.get(f"{BASE_URL}/symbiote/status")
    assert response.status_code == 200
    data = response.json()
    assert "initialized" in data
    print(f"✅ Symbiote: {data['active_strategy']}")

def test_validate_trade():
    """Test trade validation"""
    response = requests.post(f"{BASE_URL}/validate", json={
        "symbol": "BTCUSDT",
        "amount": 1000,
        "price": 50000,
        "stop_loss": 49000
    })
    assert response.status_code == 200
    data = response.json()
    assert "approved" in data
    status = "APPROVED" if data["approved"] else "REJECTED"
    print(f"✅ Trade Validation: {status}")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🧪 TESTING PHOENIX KERNEL")
    print("="*50)
    
    tests = [
        test_health,
        test_kill_status,
        test_portfolio,
        test_pulse,
        test_workers_list,
        test_memory_stats,
        test_constitution_rules,
        test_symbiote_status,
        test_validate_trade,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print("\n" + "="*50)
    print(f"📊 RESULTS: {passed} passed, {failed} failed")
    print("="*50)
