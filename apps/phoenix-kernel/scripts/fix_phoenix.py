# fix_phoenix.py
import re
import sys
from pathlib import Path

def fix_phoenix_kernel(filepath):
    print(f"🔧 Fixing: {filepath}")
    print("="*60)
    
    if not Path(filepath).exists():
        print(f"❌ File not found: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixes_applied = []
    
    # ========================================================================
    # FIX 1: Add DRIFT_THRESHOLD to Config class
    # ========================================================================
    if 'DRIFT_THRESHOLD' not in content:
        old_line = 'OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))'
        new_lines = '''OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))
    DRIFT_THRESHOLD = float(os.getenv("DRIFT_THRESHOLD", "0.3"))'''
        content = content.replace(old_line, new_lines)
        fixes_applied.append("✅ Added DRIFT_THRESHOLD to Config")
    else:
        fixes_applied.append("⚪ DRIFT_THRESHOLD already exists")
    
    # ========================================================================
    # FIX 2: Fix HiveBridge task['type'] -> task.type
    # ========================================================================
    if "task['type']" in content:
        content = content.replace("task['type']", "task.type")
        fixes_applied.append("✅ Fixed HiveBridge task.type reference")
    else:
        fixes_applied.append("⚪ HiveBridge task.type already fixed")
    
    # ========================================================================
    # FIX 3: Fix StreamingBridge undefined execution_results
    # ========================================================================
    if 'execution_results.items()' in content:
        old_pattern = "for worker_name, result in execution_results.items():"
        new_pattern = """tasks = kernel.intent_parser.parse(intent)
        for task in tasks:
            worker_name = kernel.hive_bridge._map_to_worker(task.type)"""
        content = content.replace(old_pattern, new_pattern)
        fixes_applied.append("✅ Fixed StreamingBridge undefined variables")
    else:
        fixes_applied.append("⚪ StreamingBridge already fixed")
    
    # ========================================================================
    # FIX 4: Add kernel parameter to StreamingBridge.stream_execution
    # ========================================================================
    old_sig = "async def stream_execution(self, intent: str, websocket: WebSocket):"
    new_sig = "async def stream_execution(self, intent: str, websocket: WebSocket, kernel):"
    if old_sig in content:
        content = content.replace(old_sig, new_sig)
        fixes_applied.append("✅ Added kernel parameter to StreamingBridge")
    else:
        fixes_applied.append("⚪ StreamingBridge signature already correct")
    
    # ========================================================================
    # FIX 5: Remove duplicate Constitution class
    # ========================================================================
    constitution_count = content.count('class Constitution:')
    if constitution_count > 1:
        lines = content.split('\n')
        new_lines = []
        skip_until_next_class = False
        constitution_found = False
        
        for i, line in enumerate(lines):
            if 'class Constitution:' in line:
                if not constitution_found:
                    constitution_found = True
                    # Check if this one has async validate method
                    has_validate = False
                    for j in range(i, min(i+30, len(lines))):
                        if 'async def validate' in lines[j]:
                            has_validate = True
                            break
                    if not has_validate:
                        skip_until_next_class = True
                        continue
            if skip_until_next_class:
                if line.strip().startswith('class ') and 'Constitution' not in line:
                    skip_until_next_class = False
                continue
            new_lines.append(line)
        
        content = '\n'.join(new_lines)
        fixes_applied.append("✅ Removed duplicate Constitution class")
    else:
        fixes_applied.append("⚪ No duplicate Constitution found")
    
    # ========================================================================
    # FIX 6: Ensure required worker classes exist before PhoenixKernel
    # ========================================================================
    required_workers = [
        'EnhancedFileSystemWorker',
        'SystemMonitorWorker', 
        'ClipboardWorker',
        'BrowserWorker',
        'CodeGenWorker',
        'RezSwarmWorker',
        'DuckDuckGoWorker',
        'SearXNGWorker'
    ]
    
    missing_workers = []
    for worker in required_workers:
        if f'class {worker}' not in content:
            missing_workers.append(worker)
    
    if missing_workers:
        print(f"⚠️  Missing worker classes: {missing_workers}")
        print("   These need to be added manually or imported from workers/")
    else:
        fixes_applied.append("✅ All required worker classes present")
    
    # ========================================================================
    # FIX 7: Ensure dataclasses are before SCERefiner
    # ========================================================================
    dataclass_pos = content.find('@dataclass')
    sce_pos = content.find('class SCERefiner:')
    if dataclass_pos > 0 and sce_pos > 0 and dataclass_pos > sce_pos:
        print("⚠️  WARNING: Dataclasses are AFTER SCERefiner - manual fix needed")
    else:
        fixes_applied.append("✅ Dataclasses correctly ordered")
    
    # ========================================================================
    # WRITE FIXED CONTENT
    # ========================================================================
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # ========================================================================
    # PRINT SUMMARY
    # ========================================================================
    print("\n" + "="*60)
    print("🔥 PHOENIX KERNEL - FIX SUMMARY")
    print("="*60)
    for fix in fixes_applied:
        print(f"  {fix}")
    print("="*60)
    print(f"\n📁 Fixed file: {filepath}")
    print("\n🚀 Next step: python {filepath}")
    print("="*60 + "\n")
    
    return True

if __name__ == "__main__":
    # Try to find the phoenix kernel file
    possible_files = [
        "phoenix_kernel_v13.3.0.py",
        "phoenix_kernel_v15.py", 
        "phoenix_kernel_v14e.py",
        "phoenix_ultimate_v13.3.0.py"
    ]
    
    target_file = None
    for f in possible_files:
        if Path(f).exists():
            target_file = f
            break
    
    if target_file:
        fix_phoenix_kernel(target_file)
    else:
        print("❌ No Phoenix kernel file found!")
        print("Available files:")
        for f in Path(".").glob("phoenix*.py"):
            print(f"  - {f.name}")
        print("\nUsage: python fix_phoenix.py <filename>")
        if len(sys.argv) > 1:
            fix_phoenix_kernel(sys.argv[1])