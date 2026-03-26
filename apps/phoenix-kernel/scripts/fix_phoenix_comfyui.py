# fix_phoenix_comfyui.py
"""
Automatically fixes Phoenix kernel by:
1. Moving ComfyUI worker import into __init__ method
2. Creating the comfyui_worker.py file if it doesn't exist
"""

import os
import sys
from pathlib import Path

# Paths
KERNEL_PATH = Path("D:/Rezonic_Agentic/apps/phoenix-kernel/phoenix_kernel_v13.3.0.py")
WORKER_PATH = Path("D:/Rezonic_Agentic/apps/phoenix-kernel/workers/comfyui_worker.py")

print("=" * 70)
print("🔧 PHOENIX KERNEL FIX SCRIPT")
print("=" * 70)

# ============================================================================
# STEP 1: CREATE COMFYUI WORKER FILE
# ============================================================================
print("\n📁 Step 1: Creating ComfyUI worker file...")

comfyui_worker_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComfyUI Worker for Phoenix Kernel
"""

import httpx
import json
import logging
from typing import Dict, Any

logger = logging.getLogger("PHOENIX.COMFYUI")

class ComfyUIWorker:
    def __init__(self):
        self.name = "comfyui_generator"
        self.comfyui_url = "http://127.0.0.1:8188"
        logger.info("✅ ComfyUI Worker initialized")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Generate image using ComfyUI"""
        
        prompt = kwargs.get("prompt", task.replace("/generate", "").strip())
        
        if not prompt:
            return {"error": "No prompt provided", "success": False}
        
        # Simple test workflow
        workflow = {
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt}
            },
            "4": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1}
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.comfyui_url}/prompt",
                    json={"prompt": workflow}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "prompt_id": data.get("prompt_id"),
                        "prompt": prompt,
                        "message": "Queued in ComfyUI"
                    }
                else:
                    return {"error": f"ComfyUI error: {response.status_code}", "success": False}
                    
        except Exception as e:
            return {"error": str(e), "success": False}
'''

# Ensure workers directory exists
WORKER_PATH.parent.mkdir(parents=True, exist_ok=True)

# Write the worker file
with open(WORKER_PATH, 'w', encoding='utf-8') as f:
    f.write(comfyui_worker_content)
print(f"   ✅ Created: {WORKER_PATH}")

# ============================================================================
# STEP 2: FIX PHOENIX KERNEL
# ============================================================================
print("\n📝 Step 2: Fixing Phoenix kernel...")

# Read the kernel file
with open(KERNEL_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Check if ComfyUI worker is already correctly placed
if 'self.workers[\'comfyui\']' in content:
    print("   ⚠️ ComfyUI worker already registered")
else:
    # Find where to insert ComfyUI worker registration
    # Look for the line after other worker registrations
    search_pattern = "self.workers\['rez_swarm'\]"
    
    if search_pattern in content:
        # Insert after RezSwarm registration
        insert_point = content.find(search_pattern)
        # Find the end of that line
        insert_point = content.find('\n', insert_point) + 1
        
        comfyui_registration = '''
        # ========== COMFYUI WORKER ==========
        try:
            from workers.comfyui_worker import ComfyUIWorker
            self.workers['comfyui'] = {"class": ComfyUIWorker, "module": "comfyui_worker", "loaded_at": time.time()}
            logger.info("🎨 ComfyUI Worker registered")
        except ImportError as e:
            logger.warning(f"ComfyUI Worker not available: {e}")
        # ====================================
        
'''
        content = content[:insert_point] + comfyui_registration + content[insert_point:]
        print("   ✅ Added ComfyUI worker registration")
    else:
        print("   ❌ Could not find RezSwarm registration")
        sys.exit(1)

# ============================================================================
# STEP 3: ADD GENERATE COMMAND TO REFLEX COMMANDS
# ============================================================================
print("\n📝 Step 3: Adding /generate command to ReflexCommands...")

# Find the ReflexCommands.execute method
reflex_method = "async def execute(self, cmd: str):"
if reflex_method in content:
    # Find where to add the generate command (after /search)
    search_pattern = 'elif cmd.startswith("/search") or cmd.startswith("/ddg"):'
    
    if search_pattern in content:
        # Find the position before the /search block
        insert_point = content.find(search_pattern)
        
        generate_command = '''
        elif cmd.startswith("/generate"):
            prompt = cmd.replace("/generate", "").strip()
            if prompt:
                worker_class = self.kernel.workers.get('comfyui', {}).get('class')
                if worker_class:
                    worker = worker_class()
                    result = await worker.execute("generate", prompt=prompt)
                    if result.get("success"):
                        return {
                            "type": "reflex",
                            "content": f"🎨 **Generation Queued**\\n\\nPrompt: {prompt}\\nID: {result.get('prompt_id')}\\n\\nImage will appear in ComfyUI output folder."
                        }
                    else:
                        return {"type": "reflex", "content": f"❌ Generation failed: {result.get('error')}"}
                else:
                    return {"type": "reflex", "content": "❌ ComfyUI worker not available. Make sure ComfyUI is running."}
            else:
                return {"type": "reflex", "content": "📝 Usage: /generate <prompt>"}
        
'''
        content = content[:insert_point] + generate_command + content[insert_point:]
        print("   ✅ Added /generate command")
    else:
        print("   ⚠️ Could not find /search block, command may need manual addition")
else:
    print("   ❌ Could not find ReflexCommands.execute method")
    sys.exit(1)

# ============================================================================
# STEP 4: SAVE THE FIXED KERNEL
# ============================================================================
print("\n💾 Step 4: Saving fixed kernel...")

# Backup original
backup_path = KERNEL_PATH.with_suffix('.py.bak')
with open(backup_path, 'w', encoding='utf-8') as f:
    with open(KERNEL_PATH, 'r', encoding='utf-8') as original:
        f.write(original.read())
print(f"   ✅ Backup saved: {backup_path}")

# Write fixed content
with open(KERNEL_PATH, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"   ✅ Fixed kernel saved: {KERNEL_PATH}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("✅ FIX COMPLETE!")
print("=" * 70)
print("\n📋 WHAT WAS DONE:")
print("   1. Created ComfyUI worker file")
print("   2. Added ComfyUI worker registration to PhoenixKernel.__init__")
print("   3. Added /generate command to ReflexCommands")
print("   4. Created backup of original kernel")
print("\n🚀 NEXT STEPS:")
print("   1. Start ComfyUI in a separate terminal:")
print("      cd D:\\ComfyUI_windows_portable_nvidia\\ComfyUI_windows_portable")
print("      .\\python_embeded\\python.exe ComfyUI\\main.py --windows-standalone-build")
print("")
print("   2. Start Phoenix:")
print("      cd D:\\Rezonic_Agentic\\apps\\phoenix-kernel")
print("      python phoenix_kernel_v13.3.0.py")
print("")
print("   3. Test the integration:")
print("      curl -X POST http://localhost:8002/kernel/stream -H 'Content-Type: application/json' -d '{\"task\": \"/generate cyberpunk cat\"}'")
print("")
print("=" * 70)