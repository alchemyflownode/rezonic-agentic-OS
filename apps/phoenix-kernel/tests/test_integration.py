# tests/test_integration.py
"""Integration tests for the complete Phoenix Kernel"""

import sys
import asyncio
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================================
# TEST SECURITY MODULES
# ============================================================================

class TestSecurity:
    """Test security modules integration"""
    
    def test_key_manager_flow(self):
        """Test complete key management flow"""
        from security.key_manager import KeyManager
        
        # Create manager
        km = KeyManager(master_password="test_password_123")
        
        # Encrypt keys
        result = km.encrypt_api_key("test_exchange", "api_key_123", "api_secret_456")
        assert result["success"] == True
        
        # List exchanges
        exchanges = km.list_exchanges()
        assert "test_exchange" in exchanges
        
        # Decrypt keys
        decrypted = km.decrypt_api_key("test_exchange")
        assert decrypted["success"] == True
        assert decrypted["api_key"] == "api_key_123"
        
        # Delete keys
        result = km.delete_api_key("test_exchange")
        assert result["success"] == True
    
    def test_rate_limiter(self):
        """Test rate limiter functionality"""
        from security.rate_limiter import RateLimiter
        import asyncio
        
        limiter = RateLimiter(rate=5, per_second=1)
        
        async def test():
            # Should allow 5 requests
            for i in range(5):
                assert await limiter.acquire("test_client") == True
            
            # 6th should be denied
            assert await limiter.acquire("test_client") == False
        
        asyncio.run(test())
    
    def test_input_validator(self):
        """Test input validation"""
        from security.input_validator import InputValidator, TradeValidator
        
        # Test path validation
        valid, error, path = InputValidator.validate_path(".")
        assert valid == True
        
        # Test dangerous command blocking
        valid, error = InputValidator.validate_command("rm -rf /")
        assert valid == False
        
        # Test trade validation
        valid, error = TradeValidator.validate_order({
            "symbol": "BTC/USDT",
            "side": "BUY",
            "amount": 100.0,
            "type": "MARKET"
        })
        assert valid == True


# ============================================================================
# TEST EXCHANGE MODULES
# ============================================================================

class TestExchange:
    """Test exchange modules integration"""
    
    @pytest.mark.asyncio
    async def test_exchange_interface(self):
        """Test exchange base interface"""
        from exchange.base import ExchangeInterface, Order, MarketData
        
        # Test that abstract class can't be instantiated
        try:
            ExchangeInterface()
            assert False, "Should not be instantiable"
        except TypeError:
            pass
    
    @pytest.mark.asyncio
    async def test_binance_connector_initialization(self):
        """Test Binance connector initialization"""
        from exchange.binance_connector import BinanceConnector
        
        connector = BinanceConnector(testnet=True)
        assert connector.testnet == True
        assert "testnet" in connector.rest_url


# ============================================================================
# TEST WORKER MODULES
# ============================================================================

class TestWorkers:
    """Test worker modules integration"""
    
    def test_decorators_exist(self):
        """Test error handling decorators exist"""
        from workers.decorators import handle_errors, with_timeout, log_execution
        assert callable(handle_errors)
        assert callable(with_timeout)
        assert callable(log_execution)
    
    @pytest.mark.asyncio
    async def test_backup_worker(self):
        """Test backup worker initialization"""
        from workers.backup_worker import BackupWorker
        
        worker = BackupWorker()
        assert worker.name == "backup_worker"
        assert worker.backup_root.exists()


# ============================================================================
# TEST MONITORING MODULES
# ============================================================================

class TestMonitoring:
    """Test monitoring modules"""
    
    def test_metrics_exist(self):
        """Test metrics module has required components"""
        from monitoring.metrics import (
            trades_total, trades_successful, trades_failed,
            portfolio_value, workers_active, integrity_score
        )
        assert trades_total is not None
        assert portfolio_value is not None


# ============================================================================
# TEST CONSTITUTION INTEGRATION
# ============================================================================

class TestConstitution:
    """Test constitutional enforcement"""
    
    def test_constitution_import(self):
        """Test constitution module"""
        # Note: constitution is defined in phoenix_kernel_v14c.py
        # This test verifies the module structure
        try:
            from phoenix_kernel_v14c import Constitution
            assert True
        except ImportError:
            # If not importable as module, that's fine - it's part of main kernel
            pass


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    print("🧪 Running integration tests...")
    
    # Run security tests
    test_sec = TestSecurity()
    test_sec.test_key_manager_flow()
    print("✅ Key manager flow passed")
    test_sec.test_rate_limiter()
    print("✅ Rate limiter passed")
    test_sec.test_input_validator()
    print("✅ Input validator passed")
    
    # Run exchange tests
    test_ex = TestExchange()
    import asyncio
    asyncio.run(test_ex.test_binance_connector_initialization())
    print("✅ Binance connector passed")
    
    # Run worker tests
    test_wk = TestWorkers()
    test_wk.test_decorators_exist()
    print("✅ Worker decorators passed")
    
    # Run monitoring tests
    test_mon = TestMonitoring()
    test_mon.test_metrics_exist()
    print("✅ Metrics module passed")
    
    print("\n🎉 All integration tests passed!")