# -*- coding: utf-8 -*-
"""
REZTRAINER CONSTITUTIONAL FORENSIC SCANNER
Save this as constitutional_forensic_scanner.py and run with: python constitutional_forensic_scanner.py
"""

import os
import json
import pickle
import torch
import hashlib
import subprocess
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

BASE_DIR = Path(r"G:\okiru-pure\rezsparse-trainer")
REPORTS_DIR = BASE_DIR / "models" / "distilled" / "reports"
CONSTITUTIONAL_MODEL = BASE_DIR / "production_constitutional_predictor.pkl"

class ConstitutionalForensicScanner:
    """Complete forensic audit of Constitutional AI ecosystem"""
    
    def __init__(self):
        self.results = {
            "scan_timestamp": datetime.now().isoformat(),
            "system_health": {},
            "models": [],
            "distillations": [],
            "constitutional_scores": [],
            "violations": [],
            "recommendations": [],
            "pipeline_status": {}
        }
        
    def scan_system_health(self):
        """Check all critical components"""
        print("\n🏥 SYSTEM HEALTH CHECK")
        print("=" * 60)
        
        # Check Python environment
        self.results["system_health"]["python"] = {
            "version": sys.version,
            "executable": sys.executable
        }
        print(f"✅ Python: {sys.version[:30]}...")
        
        # Check PyTorch
        try:
            import torch
            self.results["system_health"]["pytorch"] = {
                "version": torch.__version__,
                "cuda_available": torch.cuda.is_available(),
                "cuda_version": torch.version.cuda if torch.cuda.is_available() else None
            }
            if torch.cuda.is_available():
                print(f"✅ PyTorch {torch.__version__} - CUDA {torch.version.cuda}")
            else:
                print("⚠️ PyTorch - CUDA not available")
        except ImportError:
            self.results["system_health"]["pytorch"] = {"error": "Not installed"}
            print("❌ PyTorch not installed")
        except Exception as e:
            self.results["system_health"]["pytorch"] = {"error": str(e)}
            print(f"❌ PyTorch error: {e}")
        
        # Check Ollama
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                models = result.stdout.strip().split('\n')[1:]
                self.results["system_health"]["ollama"] = {
                    "status": "running",
                    "model_count": len(models),
                    "models": [m.split()[0] for m in models if m]
                }
                print(f"✅ Ollama running - {len(models)} models")
            else:
                self.results["system_health"]["ollama"] = {"status": "not_running"}
                print("❌ Ollama not running")
        except FileNotFoundError:
            self.results["system_health"]["ollama"] = {"status": "not_found"}
            print("❌ Ollama not found")
        except Exception as e:
            self.results["system_health"]["ollama"] = {"status": "error", "error": str(e)}
            print(f"❌ Ollama error: {e}")
        
        # Check RTX 3060 Optimizer
        optimizer_path = BASE_DIR / "src" / "trainer" / "rtx3060_optimizer.py"
        if optimizer_path.exists():
            self.results["system_health"]["rtx_optimizer"] = {
                "status": "installed",
                "path": str(optimizer_path),
                "size_kb": optimizer_path.stat().st_size / 1024
            }
            print(f"✅ RTX 3060 Optimizer: {optimizer_path.stat().st_size / 1024:.1f} KB")
        else:
            self.results["system_health"]["rtx_optimizer"] = {"status": "missing"}
            print("❌ RTX 3060 Optimizer not found")
        
        return self.results["system_health"]
    
    def scan_constitutional_model(self):
        """Deep scan of the constitutional scoring model"""
        print("\n🏛️  CONSTITUTIONAL MODEL FORENSICS")
        print("=" * 60)
        
        if not CONSTITUTIONAL_MODEL.exists():
            print(f"❌ Constitutional model not found at: {CONSTITUTIONAL_MODEL}")
            return None
        
        model_info = {
            "path": str(CONSTITUTIONAL_MODEL),
            "size_mb": CONSTITUTIONAL_MODEL.stat().st_size / (1024 * 1024),
            "modified": datetime.fromtimestamp(CONSTITUTIONAL_MODEL.stat().st_mtime).isoformat(),
            "hash": self._calculate_hash(CONSTITUTIONAL_MODEL)
        }
        
        try:
            with open(CONSTITUTIONAL_MODEL, 'rb') as f:
                data = pickle.load(f)
            
            model_info["type"] = str(type(data['model']))
            model_info["features"] = len(data.get('feature_names', []))
            model_info["version"] = data.get('version', 'unknown')
            
            # Extract constitutional principles
            coefs = data['model'].coef_[0]
            feature_names = data['feature_names']
            
            # Top constitutional principles
            top_indices = np.argsort(coefs)[-10:][::-1]
            model_info["top_principles"] = [
                {"principle": feature_names[i], "weight": float(coefs[i])}
                for i in top_indices
            ]
            
            # Bottom anti-patterns
            bottom_indices = np.argsort(coefs)[:10]
            model_info["anti_patterns"] = [
                {"pattern": feature_names[i], "weight": float(coefs[i])}
                for i in bottom_indices
            ]
            
            print(f"\n✅ Constitutional Model Loaded:")
            print(f"  📊 Features: {model_info['features']}")
            print(f"  📦 Version: {model_info['version']}")
            print(f"  🔑 Hash: {model_info['hash'][:16]}...")
            
            print(f"\n🏛️  TOP CONSTITUTIONAL PRINCIPLES:")
            for i, p in enumerate(model_info["top_principles"][:5], 1):
                print(f"  {i}. {p['principle']}: +{p['weight']:.3f}")
            
            print(f"\n⚠️  TOP ANTI-PATTERNS:")
            for i, p in enumerate(model_info["anti_patterns"][:5], 1):
                print(f"  {i}. {p['pattern']}: {p['weight']:.3f}")
            
        except Exception as e:
            model_info["error"] = str(e)
            print(f"❌ Failed to load constitutional model: {e}")
        
        self.results["constitutional_model"] = model_info
        return model_info
    
    def _calculate_hash(self, file_path):
        """Calculate SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for block in iter(lambda: f.read(4096), b''):
                sha256.update(block)
        return sha256.hexdigest()
    
    def run_full_scan(self):
        """Execute complete constitutional forensic scan"""
        print("\n" + "="*80)
        print("🔬 REZTRAINER CONSTITUTIONAL FORENSIC SCAN v2.0")
        print("="*80)
        print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        self.scan_system_health()
        self.scan_constitutional_model()
        
        print("\n" + "="*80)
        print("✅ CONSTITUTIONAL FORENSIC SCAN COMPLETE!")
        print("="*80)
        
        return self.results

if __name__ == "__main__":
    scanner = ConstitutionalForensicScanner()
    results = scanner.run_full_scan()
