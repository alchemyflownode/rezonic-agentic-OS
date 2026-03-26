"""
Usage Example: Rez Hive Constitutional AI
"""

from constitutional_ai import RezHiveConstitutionalAI

# Initialize
ai = RezHiveConstitutionalAI()

# Test
test_text = "How do I ensure data privacy in my application?"
score = ai.predict_score(test_text)
print(f"Constitutional Score: {score:.1f}/100")

# Get principles
principles = ai.get_constitutional_principles()
print(f"Principles: {principles[:3]}...")

# Check rulings
ruling = ai.check_ruling(test_text)
if ruling:
    print(f"Found ruling: {ruling}")
