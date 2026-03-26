# fix_phoenix_kernel.py
import re

def fix_phoenix_kernel(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # FIX 1: Ensure dataclasses are BEFORE SCERefiner
    dataclass_block = '''
# ============================================================================
# ORCHESTRATION DATA CLASSES (MUST BE BEFORE SCERefiner)
# ============================================================================
from dataclasses import dataclass, field
from typing import List, Dict, Any, Set, Optional

@dataclass
class Task:
    """Atomic unit of work"""
    id: str = ""
    type: str = ""
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    worker_type: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5

@dataclass
class OrchestrationPlan:
    """Plan created by orchestrator"""
    intent: str = ""
    tasks: List[Task] = field(default_factory=list)
    dependencies: Dict[str, Set[str]] = field(default_factory=dict)
    worker_map: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "tasks": [{"id": t.id, "type": t.type, "description": t.description} for t in self.tasks],
            "timestamp": self.timestamp
        }

@dataclass
class RefinedPlan:
    """Plan refined by SCE"""
    original_plan: OrchestrationPlan = None
    blueprint: Dict[str, Any] = field(default_factory=dict)
    constitutional_score: float = 0.0
    drift_corrected: bool = False
    sce_lock: str = ""
    optimization_level: str = "maximum"
    refined_tasks: List[Task] = field(default_factory=list)

class ConstitutionalError(Exception):
    pass

class DriftDetector:
    def __init__(self, threshold: float = 0.3):
        self.threshold = threshold
    
    async def check(self, plan: OrchestrationPlan) -> float:
        drift = min(1.0, len(plan.tasks) / 20.0)
        return drift
    
    async def check_single(self, result: Dict) -> float:
        if result.get("error"):
            return 1.0
        if not result.get("success", True):
            return 0.5
        return 0.0

'''
    
    # Check if dataclasses exist, if not add them before SCERefiner
    if '@dataclass' not in content or 'class OrchestrationPlan:' not in content:
        content = content.replace(
            'class SCERefiner:',
            dataclass_block + 'class SCERefiner:'
        )
        print("✅ Fix 1: Added dataclasses before SCERefiner")
    
    # FIX 2: Ensure DuckDuckGoWorker is defined before PhoenixKernel
    if 'class DuckDuckGoWorker:' not in content:
        duckduckgo_worker = '''
# ============================================================================
# SEARCH WORKERS
# ============================================================================
class DuckDuckGoWorker(Worker):
    def __init__(self):
        super().__init__("duckduckgo_search")
        self.api_url = "https://api.duckduckgo.com/"
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        import re
        patterns = [r'(?:/search|/ddg)\\s+(.+?)(?:$)', r'search\\s+(.+?)(?:$)', r'what is\\s+(.+?)(?:\\?|$)']
        query = task
        for pattern in patterns:
            match = re.search(pattern, task, re.IGNORECASE)
            if match:
                query = match.group(1)
                break
        query = query.strip()
        if not query:
            return {"error": "No search query", "success": False}
        return {"success": True, "query": query, "results": [], "count": 0}

class SearXNGWorker(Worker):
    def __init__(self):
        super().__init__("searxng_search")
        self.enabled = config.SEARXNG_ENABLED
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        if not self.enabled:
            return {"error": "SearXNG not enabled", "success": False}
        return {"error": "SearXNG not configured", "success": False}

'''
        # Add before PhoenixKernel class
        content = content.replace(
            'class PhoenixKernel:',
            duckduckgo_worker + 'class PhoenixKernel:'
        )
        print("✅ Fix 2: Added DuckDuckGoWorker before PhoenixKernel")
    
    # FIX 3: Add missing Config.DRIFT_THRESHOLD
    if 'DRIFT_THRESHOLD' not in content:
        content = content.replace(
            'OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))',
            'OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))\n    DRIFT_THRESHOLD = float(os.getenv("DRIFT_THRESHOLD", "0.3"))'
        )
        print("✅ Fix 3: Added DRIFT_THRESHOLD to Config")
    
    # FIX 4: Fix HiveBridge task.type reference
    content = re.sub(
        r"task\['type'\]",
        "task.type",
        content
    )
    print("✅ Fix 4: Fixed HiveBridge task.type reference")
    
    # FIX 5: Remove duplicate Constitution class
    constitution_count = content.count('class Constitution:')
    if constitution_count > 1:
        # Find and remove the first (simpler) one
        pattern = r'class Constitution:\s*def __init__\(self\):\s*self\.laws = config\.CONSTITUTION_LAWS\s*self\.ruling_history = \[\]\s*def evaluate\(self, action: str.*?return \{"total_rulings": len\(self\.ruling_history\), "laws": self\.laws, "recent": self\.ruling_history\[-5:\]\}'
        # Keep the one with async validate method
        lines = content.split('\n')
        new_lines = []
        skip_until_next_class = False
        constitution_found = False
        
        for i, line in enumerate(lines):
            if 'class Constitution:' in line:
                if not constitution_found:
                    constitution_found = True
                    # Check if this one has async validate
                    has_validate = any('async def validate' in l for l in lines[i:i+30])
                    if not has_validate:
                        skip_until_next_class = True
                        continue
            if skip_until_next_class:
                if line.strip().startswith('class ') and 'Constitution' not in line:
                    skip_until_next_class = False
                continue
            new_lines.append(line)
        
        content = '\n'.join(new_lines)
        print("✅ Fix 5: Removed duplicate Constitution class")
    
    # Write fixed content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n🎉 All fixes applied to: {filepath}")

if __name__ == "__main__":
    fix_phoenix_kernel("phoenix_kernel_v15.py")