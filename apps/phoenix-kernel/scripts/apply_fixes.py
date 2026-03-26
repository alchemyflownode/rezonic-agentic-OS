# apply_fixes.py
import re

def apply_fixes(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixes_applied = []
    
    # Fix 1: Add DRIFT_THRESHOLD to Config
    if 'DRIFT_THRESHOLD' not in content:
        content = content.replace(
            'OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))',
            'OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))\n    DRIFT_THRESHOLD = float(os.getenv("DRIFT_THRESHOLD", "0.3"))'
        )
        fixes_applied.append("Added DRIFT_THRESHOLD to Config")
    
    # Fix 2: Fix HiveBridge task['type'] -> task.type
    if "task['type']" in content:
        content = content.replace("task['type']", "task.type")
        fixes_applied.append("Fixed HiveBridge task.type reference")
    
    # Fix 3: Fix StreamingBridge - replace execution_results reference
    if 'execution_results.items()' in content:
        content = content.replace(
            'for worker_name, result in execution_results.items():',
            'tasks = kernel.intent_parser.parse(intent)\n        for task in tasks:\n            worker_name = kernel.hive_bridge._map_to_worker(task.type)'
        )
        fixes_applied.append("Fixed StreamingBridge undefined variables")
    
    # Fix 4: Add kernel parameter to stream_execution
    if 'async def stream_execution(self, intent: str, websocket: WebSocket):' in content:
        content = content.replace(
            'async def stream_execution(self, intent: str, websocket: WebSocket):',
            'async def stream_execution(self, intent: str, websocket: WebSocket, kernel):'
        )
        fixes_applied.append("Added kernel parameter to StreamingBridge")
    
    # Fix 5: Remove duplicate Constitution class
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
        fixes_applied.append("Removed duplicate Constitution class")
    
    # Write fixed content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n" + "="*60)
    print("PHOENIX KERNEL - FIXES APPLIED")
    print("="*60)
    for fix in fixes_applied:
        print(f"  [OK] {fix}")
    print("="*60)
    print(f"\nFile: {filepath}")
    print("\nReady to run: python {filepath}\n")

if __name__ == "__main__":
    apply_fixes("phoenix_kernel_v13.3.0.py")