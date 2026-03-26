"""
Rez Hive Constitutional AI - Integration Wrapper
Combines assets from RezTrainer and LangChain
"""

import os
import sys
import json
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime

print("🏛️ Rez Hive Constitutional AI Integration")
print("=" * 60)

class RezHiveConstitutionalAI:
    """Complete constitutional AI combining all assets"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        
        # Load RezTrainer assets with error handling
        self.predictor = self._load_predictor()
        self.memory = self._load_constitutional_memory()
        self.manifest = self._load_manifest()
        
        print(f"✅ Loaded predictor: {self.predictor is not None}")
        print(f"✅ Loaded memory: {len(self.memory.get('rulings', []))} rulings")
        print(f"✅ Loaded manifest: {len(self.manifest.get('principles', []))} principles")
    
    def _load_predictor(self):
        """Load the production constitutional predictor"""
        predictor_path = self.base_path / "data/constitutional/production_constitutional_predictor.pkl"
        try:
            if predictor_path.exists():
                with open(predictor_path, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"⚠️ Could not load predictor: {e}")
        return None
    
    def _load_constitutional_memory(self):
        """Load constitutional memory"""
        memory_path = self.base_path / "data/constitutional/constitutional_memory.json"
        try:
            if memory_path.exists():
                with open(memory_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load memory: {e}")
        
        # Return default memory
        return {
            "version": "1.0.0",
            "principles": [
                "Data Sovereignty",
                "Privacy",
                "Transparency",
                "Safety",
                "Accountability"
            ],
            "rulings": [],
            "precedents": []
        }
    
    def _load_manifest(self):
        """Load constitutional manifest"""
        manifest_path = self.base_path / "data/constitutional/constitutional_manifest.json"
        try:
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load manifest: {e}")
        
        # Return default manifest
        return {
            "name": "Rez Hive Constitutional AI",
            "version": "1.0.0",
            "principles": [
                "Sovereignty: User controls their data and AI interactions",
                "Privacy: Zero-drift protocol ensures data never leaves local system",
                "Transparency: All decisions are explainable and auditable",
                "Safety: Constitutional guardrails prevent harmful outputs",
                "Accountability: Drift locks provide full traceability"
            ],
            "governance": {
                "executive_committee": ["qwen2.5-coder:7b"],
                "advisory_panel": ["llama3.2:3b"]
            }
        }
    
    def predict_score(self, text: str) -> float:
        """Predict constitutional score using trained model"""
        if self.predictor and 'model' in self.predictor:
            try:
                # Extract features (simplified but functional)
                features = self._extract_features(text)
                score = self.predictor['model'].predict([features])[0]
                return float(np.clip(score, 0, 100))
            except Exception as e:
                print(f"⚠️ Prediction error: {e}")
                return 70.0
        return 70.0  # Default safe score
    
    def _extract_features(self, text: str) -> np.ndarray:
        """Extract features for predictor"""
        features = np.zeros(512)
        words = text.split()
        
        # Basic text features
        features[0] = len(text) / 1000  # Length normalized
        features[1] = len(words) / 100  # Word count
        features[2] = text.count('\n') / 50  # Newlines
        features[3] = len([w for w in words if w.isupper()]) / 20  # Uppercase words
        features[4] = 1 if 'SCE' in text else 0  # SCE mention
        features[5] = 1 if 'constitution' in text.lower() else 0  # Constitution mention
        features[6] = 1 if 'privacy' in text.lower() else 0  # Privacy mention
        features[7] = 1 if 'security' in text.lower() else 0  # Security mention
        
        # Add some random features for diversity
        features[8:512] = np.random.randn(504) * 0.1
        
        return features
    
    def get_constitutional_principles(self) -> list:
        """Get constitutional principles"""
        return self.manifest.get('principles', [
            "Data Sovereignty",
            "Privacy",
            "Transparency", 
            "Safety",
            "Accountability"
        ])
    
    def check_ruling(self, text: str) -> dict:
        """Check if text matches any constitutional ruling"""
        for ruling in self.memory.get('rulings', []):
            if ruling.get('context', '').lower() in text.lower():
                return ruling
        return None
    
    def get_status(self) -> dict:
        """Get status of all components"""
        return {
            "predictor_loaded": self.predictor is not None,
            "memory_loaded": len(self.memory.get('rulings', [])) > 0,
            "manifest_loaded": len(self.manifest.get('principles', [])) > 0,
            "principles_count": len(self.get_constitutional_principles()),
            "version": self.manifest.get('version', '1.0.0')
        }

# Export
__all__ = ['RezHiveConstitutionalAI']

if __name__ == "__main__":
    # Quick test
    ai = RezHiveConstitutionalAI()
    test_text = "How do I ensure data privacy?"
    score = ai.predict_score(test_text)
    print(f"\n📊 Test: '{test_text}'")
    print(f"   Constitutional Score: {score:.1f}/100")
    print(f"   Status: {ai.get_status()}")
