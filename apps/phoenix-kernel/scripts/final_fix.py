# final_fix.py
import re

def apply_fixes(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Add DRIFT_THRESHOLD
    if 'DRIFT_THRESHOLD' not in content:
        content = content.replace(
            'OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))',
            'OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))\n    DRIFT_THRESHOLD = float(os.getenv("DRIFT_THRESHOLD", "0.3"))'
        )
        print("✅ Fix 1: Added DRIFT_THRESHOLD")
    
    # Fix 2: Fix HiveBridge task.type
    content = re.sub(r"task\['type'\]", "task.type", content)
    print("✅ Fix 2: Fixed HiveBridge task.type")
    
    # Fix 3: Fix StreamingBridge - replace the broken method
    old_streaming = '''async def stream_execution(self, intent: str, websocket: WebSocket):
        """Stream execution progress to frontend"""
        # Phase 1: Parsing
        await websocket.send_json({
            'type': 'orchestrating',
            'content': 'Parsing intent...',
            'timestamp': time.time()
        })
        
        # Phase 2: SCE validation
        await websocket.send_json({
            'type': 'sce',
            'content': 'Constitutional validation...',
            'timestamp': time.time()
        })
        
        # Phase 3: Worker execution
        for worker_name, result in execution_results.items():
            await websocket.send_json({
                'type': 'worker_start',
                'worker': worker_name,
                'timestamp': time.time()
            })
            await websocket.send_json({
                'type': 'worker_result',
                'worker': worker_name,
                'result': result,
                'timestamp': time.time()
            })
        
        # Phase 4: Complete
        await websocket.send_json({
            'type': 'complete',
            'sce_lock': blueprint['master_drift_lock'],
            'timestamp': time.time()
        })'''
    
    new_streaming = '''async def stream_execution(self, intent: str, websocket: WebSocket, kernel):
        """Stream execution progress to frontend"""
        try:
            await websocket.send_json({
                'type': 'orchestrating',
                'content': 'Parsing intent...',
                'timestamp': time.time()
            })
            await websocket.send_json({
                'type': 'sce',
                'content': 'Constitutional validation...',
                'timestamp': time.time()
            })
            tasks = kernel.intent_parser.parse(intent)
            for task in tasks:
                worker_name = kernel.hive_bridge._map_to_worker(task.get('type', 'SEARCH'))
                await websocket.send_json({
                    'type': 'worker_start',
                    'worker': worker_name,
                    'timestamp': time.time()
                })
            await websocket.send_json({
                'type': 'complete',
                'timestamp': time.time()
            })
        except Exception as e:
            await websocket.send_json({
                'type': 'error',
                'content': str(e),
                'timestamp': time.time()
            })'''
    
    if 'execution_results.items()' in content:
        content = content.replace(old_streaming, new_streaming)
        print("✅ Fix 3: Fixed StreamingBridge undefined variables")
    
    # Fix 4: Remove duplicate Constitution (keep the one with async validate)
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
        print("✅ Fix 4: Removed duplicate Constitution class")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n🎉 All fixes applied!")

if __name__ == "__main__":
    apply_fixes("phoenix_kernel_v15.py")
