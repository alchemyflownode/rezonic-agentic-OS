import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from pathlib import Path

print("=" * 60)
print("🏛️  CREATING CONSTITUTIONAL SCORING MODEL")
print("=" * 60)

# ============================================================================
# STEP 1: Define constitutional training data
# ============================================================================
print("\n[1/4] Loading constitutional principles...")

# Constitutional texts (positive examples)
constitutional_texts = [
    # Sovereign AI principles
    "model follows zero-drift enforcement with immutable code laws",
    "constitutional ai with semantic integrity and explicit types",
    "sovereign model that never uses any or unknown types",
    "model enforces native sovereignty without lodash dependencies",
    "constitutional ai with architectural silence no console logs",
    "truth-first verification with comprehensive error handling",
    "model aligns with sovereign ai constitution v2.0",
    "constitutional distillation with audit trail and verification",
    "sovereign model that enforces type safety and error handling",
    "zero-drift constitutional ai with immutable laws",
]

# Non-constitutional texts (negative examples)
non_constitutional_texts = [
    # Common anti-patterns
    "function process(data: any) { return data; }",
    "import { cloneDeep } from 'lodash'; const copy = cloneDeep(obj);",
    "console.log('Debugging output'); console.error(error);",
    "function process(data) { return JSON.parse(data); }",
    "var x = 5; var y = 10; console.log(x + y);",
# CONSTITUTIONAL SAFETY: eval() detected - ensure input is sanitized and consider using ast.literal_eval()
    "const result = eval(userInput); // dangerous",
    "function process(data: unknown) { return data; }",
    "_.merge(obj1, obj2); _.clone(obj); _.assign({}, src);",
    "console.table(results); console.dir(obj);",
    "debugger; // breakpoint in production",
]

# Create training data
X_text = constitutional_texts + non_constitutional_texts
y = [1] * len(constitutional_texts) + [0] * len(non_constitutional_texts)

print(f"   ✅ Constitutional examples: {len(constitutional_texts)}")
print(f"   ✅ Non-constitutional examples: {len(non_constitutional_texts)}")

# ============================================================================
# STEP 2: Create feature vectors
# ============================================================================
print("\n[2/4] Creating feature vectors...")

vectorizer = TfidfVectorizer(
    max_features=100,
    ngram_range=(1, 3),
    stop_words='english'
)

X = vectorizer.fit_transform(X_text)

print(f"   ✅ Features extracted: {X.shape[1]}")

# ============================================================================
# STEP 3: Train constitutional classifier
# ============================================================================
print("\n[3/4] Training constitutional classifier...")

model = LogisticRegression(
    class_weight='balanced',
    max_iter=1000,
    random_state=42
)
model.fit(X, y)

# Calculate training accuracy
accuracy = model.score(X, y)
print(f"   ✅ Training accuracy: {accuracy:.2%}")

# ============================================================================
# STEP 4: Save the constitutional model
# ============================================================================
print("\n[4/4] Saving constitutional model...")

constitutional_model = {
    'model': model,
    'vectorizer': vectorizer,
    'feature_names': vectorizer.get_feature_names_out().tolist(),
    'version': 'rezstack_constitutional_v1.0',
    'created': '2026-02-11',
    'description': 'Constitutional AI scoring model for sovereign distillation'
}

output_path = Path("production_constitutional_predictor.pkl")
with open(output_path, 'wb') as f:
    pickle.dump(constitutional_model, f)

print(f"\n✅ Constitutional model saved to: {output_path}")
print(f"   📊 File size: {output_path.stat().st_size / 1024:.1f} KB")
print(f"   🏛️  Features: {len(constitutional_model['feature_names'])}")

# ============================================================================
# STEP 5: Test the model
# ============================================================================
print("\n[5/5] Testing constitutional model...")

test_texts = [
    "model follows zero-drift enforcement with constitutional laws",
    "function test(data: any) { return data; }",
    "constitutional distillation with sovereign principles",
    "import { cloneDeep } from 'lodash';",
]

print("\n📊 TEST RESULTS:")
print("-" * 60)

for text in test_texts:
    vec = vectorizer.transform([text])
    score = model.predict_proba(vec)[0][1]
    is_constitutional = model.predict(vec)[0] == 1
    
    status = "✅ CONSTITUTIONAL" if is_constitutional else "❌ NON-CONSTITUTIONAL"
    print(f"{status} - Score: {score:.2%}")
    print(f"   └─ {text[:60]}...")
    print()

print("=" * 60)
print("🏛️  CONSTITUTIONAL MODEL CREATED SUCCESSFULLY!")
print("=" * 60)
print("\n📋 Next steps:")
print("   1. Run the forensic scanner again")
print("   2. Distill your first model with constitutional scoring")
print("   3. Deploy sovereign models to Ollama")
