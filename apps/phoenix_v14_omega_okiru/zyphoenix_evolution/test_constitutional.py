"""
Rez Hive Constitutional AI Test
Run this to verify everything works
"""

import sys
import os
from pathlib import Path

# Add to path
sys.path.insert(0, r'D:\Rezonic_Agentic\apps\phoenix-backend')

print("🏛️ REZ HIVE CONSTITUTIONAL AI TEST")
print("=" * 60)

try:
    from constitutional_ai import RezHiveConstitutionalAI
    
    print("\n✅ Import successful")
    
    # Initialize
    ai = RezHiveConstitutionalAI()
    
    # Test prediction
    test_text = "How do I ensure data privacy in my sovereign AI system?"
    score = ai.predict_score(test_text)
    print(f"\n📊 Test Prediction:")
    print(f"   Text: {test_text[:50]}...")
    print(f"   Constitutional Score: {score:.1f}/100")
    
    # Get principles
    principles = ai.get_constitutional_principles()
    print(f"\n📜 Constitutional Principles:")
    for p in principles[:3]:
        print(f"   • {p}")
    
    # Check memory
    ruling = ai.check_ruling(test_text)
    if ruling:
        print(f"\n⚖️ Found ruling: {ruling.get('context', 'N/A')[:100]}")
    
    print("\n✅ Constitutional AI is ready!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
