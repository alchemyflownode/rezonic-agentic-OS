# test_training_bridge.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from memory.training_bridge import TrainingBridge

print("🐝 Testing Training Bridge...")
print("=" * 50)

tb = TrainingBridge()

# Test retrieving training data
print("\n📚 Retrieving training data...")
training_data = tb.get_training_data("constitutional AI")
print(f"   Found {len(training_data)} training memories")
for i, data in enumerate(training_data[:3]):
    task = data.get("task", "Unknown")[:50]
    print(f"   {i+1}. {task}")

# Test storing a training result
print("\n💾 Storing test training result...")
result = {
    "name": "training_bridge_test",
    "timestamp": "2026-03-27",
    "status": "success",
    "message": "Training bridge integration verified"
}
drift_lock = tb.store_training_result(result)
print(f"   ✅ Stored with drift_lock: {drift_lock[:16]}...")

print("\n✅ Training bridge verified!")
