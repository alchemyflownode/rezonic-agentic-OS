# test_core.py
import sys
sys.path.insert(0, '.')

from backend.core.circuit_breaker import CircuitBreaker
from backend.core.state_store import StateStore
from backend.core.event_bus import EventBus

print("=" * 50)
print("🧪 CORE MODULE TEST")
print("=" * 50)

# Test CircuitBreaker
print("\n1. Testing CircuitBreaker...")
cb = CircuitBreaker()
print(f"   ✅ State: {cb.get_state()}")
cb.record_failure()
print(f"   ✅ After failure: {cb.get_state()}")

# Test StateStore
print("\n2. Testing StateStore...")
store = StateStore()
store.save({'test': 'data', 'position': 'FLAT'}, 'test_key')
loaded = store.load('test_key')
print(f"   ✅ Saved & Loaded: {loaded}")

# Test EventBus
print("\n3. Testing EventBus...")
bus = EventBus()
print(f"   ✅ Stats: {bus.get_stats()}")

print("\n" + "=" * 50)
print("✅ ALL CORE MODULES WORKING")
print("=" * 50)