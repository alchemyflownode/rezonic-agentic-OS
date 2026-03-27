"""
Merge Rezsparse Trainer with Rezhive Memory
Integrate training pipelines with sovereign memory
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
import logging

# Add paths
REZSPARSE_PATH = Path("G:/okiru-pure/rezsparse-trainer")
PHOENIX_PATH = Path("D:/Rezonic_Agentic/apps/phoenix-kernel")

sys.path.insert(0, str(PHOENIX_PATH))
from memory_manager import SovereignMemoryManager

logger = logging.getLogger("MERGE_REZSPARSE")

class RezsparseMerger:
    """Merge Rezsparse Trainer with Rezhive"""
    
    def __init__(self):
        self.rezsparse = REZSPARSE_PATH
        self.phoenix = PHOENIX_PATH
        self.memory_dir = self.phoenix / "data" / "memory"
        
        # Verify paths exist
        if not self.rezsparse.exists():
            raise FileNotFoundError(f"Rezsparse not found: {self.rezsparse}")
        if not self.memory_dir.exists():
            raise FileNotFoundError(f"Memory dir not found: {self.memory_dir}")
    
    def merge_training_data(self):
        """Import Rezsparse training data into Rezhive"""
        
        print("🐝 Merging Rezsparse Training Data...")
        print("=" * 50)
        
        with SovereignMemoryManager(self.memory_dir) as manager:
            stats = manager.get_stats()
            print(f"📊 Before merge: {stats['total_entries']} entries")
            
            # 1. Import training modules
            self._import_training_modules(manager)
            
            # 2. Import Constitutional AI rules
            self._import_constitutional_rules(manager)
            
            # 3. Import model configurations
            self._import_model_configs(manager)
            
            # 4. Import training datasets
            self._import_training_datasets(manager)
            
            # Get final stats
            stats = manager.get_stats()
            print(f"\n📊 After merge: {stats['total_entries']} entries")
            print(f"💾 DB Size: {stats['db_size_mb']:.2f} MB")
    
    def _import_training_modules(self, manager):
        """Import training modules as blueprints"""
        
        trainer_dir = self.rezsparse / "trainer"
        if not trainer_dir.exists():
            print("   ⚠ Trainer directory not found")
            return
        
        count = 0
        for py_file in trainer_dir.glob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                blueprint = {
                    "type": "training_module",
                    "source": "rezsparse",
                    "file": py_file.name,
                    "content": content[:5000],  # Store preview
                    "full_path": str(py_file)
                }
                
                manager.store(
                    blueprint=blueprint,
                    task=f"Training module: {py_file.stem}",
                    intent_type="training",
                    tags=["training", "module", "rezsparse"]
                )
                count += 1
                
            except Exception as e:
                print(f"   ⚠ Error importing {py_file.name}: {e}")
        
        print(f"   ✅ Imported {count} training modules")
    
    def _import_constitutional_rules(self, manager):
        """Import Constitutional AI rules"""
        
        # Look for constitutional files
        constitutional_files = [
            self.rezsparse / "constitutional_forensic_scanner.py",
            self.rezsparse / "sovereign-constitutional.Modelfile",
            self.rezsparse / "ConstitutionalSafetyTool"
        ]
        
        count = 0
        for file_path in constitutional_files:
            if file_path.exists():
                if file_path.is_file():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                else:
                    content = f"Directory: {file_path}"
                
                blueprint = {
                    "type": "constitutional_rule",
                    "source": str(file_path),
                    "content": content[:5000]
                }
                
                manager.store(
                    blueprint=blueprint,
                    task=f"Constitutional AI: {file_path.name}",
                    intent_type="constitutional",
                    tags=["constitutional", "safety", "rezsparse"]
                )
                count += 1
        
        print(f"   ✅ Imported {count} constitutional rules")
    
    def _import_model_configs(self, manager):
        """Import model configurations"""
        
        config_dir = self.rezsparse / "configs"
        if config_dir.exists():
            count = 0
            for config_file in config_dir.glob("*.json"):
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    
                    manager.store(
                        blueprint=config,
                        task=f"Model config: {config_file.stem}",
                        intent_type="model_config",
                        tags=["config", "model", "rezsparse"]
                    )
                    count += 1
                except Exception as e:
                    print(f"   ⚠ Error importing {config_file.name}: {e}")
            
            print(f"   ✅ Imported {count} model configs")
    
    def _import_training_datasets(self, manager):
        """Import training datasets as blueprints"""
        
        data_dir = self.rezsparse / "data"
        if data_dir.exists():
            count = 0
            for data_file in list(data_dir.glob("*.json"))[:50]:  # Limit for now
                try:
                    with open(data_file, 'r') as f:
                        data = json.load(f)
                    
                    manager.store(
                        blueprint={"dataset": data[:1000] if isinstance(data, list) else data},
                        task=f"Training data: {data_file.stem}",
                        intent_type="dataset",
                        tags=["dataset", "training", "rezsparse"]
                    )
                    count += 1
                except Exception as e:
                    pass
            
            print(f"   ✅ Imported {count} training datasets")
    
    def link_training_pipelines(self):
        """Create symbolic links to Rezsparse training pipelines"""
        
        # Create training bridge
        bridge_code = '''
"""
Rezsparse Training Bridge
Connects Rezhive memory to Rezsparse trainer
"""

import sys
from pathlib import Path

REZSPARSE_PATH = Path("G:/okiru-pure/rezsparse-trainer")
PHOENIX_PATH = Path("D:/Rezonic_Agentic/apps/phoenix-kernel")

sys.path.insert(0, str(PHOENIX_PATH))
sys.path.insert(0, str(REZSPARSE_PATH))

from memory_manager import SovereignMemoryManager
from rezstack import RezStack  # Assuming this exists in rezsparse

class TrainingBridge:
    """Bridge between Rezhive and Rezsparse trainer"""
    
    def __init__(self):
        self.memory = SovereignMemoryManager(PHOENIX_PATH / "data" / "memory")
        self.trainer = RezStack() if hasattr(RezStack, '__init__') else None
    
    def get_training_data(self, query: str):
        """Get relevant training data from memory"""
        results = self.memory.search(query, limit=20, intent_type="training")
        return [r.to_dict() for r in results]
    
    def store_training_result(self, result: dict):
        """Store training result in memory"""
        return self.memory.store(
            blueprint=result,
            task=f"Training result: {result.get('name', 'unknown')}",
            intent_type="training_result",
            tags=["training", "result"]
        )
'''
        
        bridge_path = self.phoenix / "memory" / "training_bridge.py"
        with open(bridge_path, 'w') as f:
            f.write(bridge_code)
        
        print(f"✅ Created training bridge: {bridge_path}")
    
    def copy_essential_modules(self):
        """Copy essential Rezsparse modules to Phoenix"""
        
        essential = [
            "constitutional_forensic_scanner.py",
            "elite_production_ui.py",
            "rtx3060_optimizer.py",
            "create_constitutional_model.py"
        ]
        
        target_dir = self.phoenix / "training"
        target_dir.mkdir(exist_ok=True)
        
        for file_name in essential:
            src = self.rezsparse / file_name
            if src.exists():
                dst = target_dir / file_name
                shutil.copy2(src, dst)
                print(f"   ✅ Copied {file_name}")
        
        print(f"✅ Copied {len(essential)} essential modules")

def main():
    print("🐝 Rezsparse + Rezhive Merger")
    print("=" * 50)
    
    try:
        merger = RezsparseMerger()
        merger.merge_training_data()
        merger.link_training_pipelines()
        merger.copy_essential_modules()
        
        print("\n✅ MERGE COMPLETE!")
        print("\n📊 Next Steps:")
        print("   1. Run: python -c 'from memory.training_bridge import TrainingBridge; tb = TrainingBridge()'")
        print("   2. Import constitutional models from Rezsparse")
        print("   3. Use training data for Hive cross-pollination")
        
    except Exception as e:
        print(f"❌ Merge failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()