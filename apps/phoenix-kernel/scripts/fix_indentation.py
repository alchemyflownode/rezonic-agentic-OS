# fix_indentation.py
"""
Fix indentation in Phoenix kernel
"""

import re
from pathlib import Path

file_path = Path("D:/Rezonic_Agentic/apps/phoenix-kernel/phoenix_kernel_v13.3.0.py")

print("🔧 Fixing indentation in ReflexCommands...")

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the ReflexCommands.execute method
# We need to properly indent the /generate command

# The issue: /generate command was inserted with wrong indentation
# Let's find the pattern and fix it

# Find the /search block location
search_pattern = 'elif cmd.startswith("/search") or cmd.startswith("/ddg"):'

if search_pattern in content:
    # We need to ensure /generate is properly indented before /search
    # Let's rebuild the ReflexCommands.execute method correctly
    
    # Find the method
    method_start = content.find('async def execute(self, cmd: str):')
    if method_start == -1:
        print("❌ Could not find execute method")
        exit(1)
    
    # Find the end of the method (next method or class end)
    # Look for next method or end of class
    next_method = content.find('def _format_', method_start)
    if next_method == -1:
        next_method = content.find('    async def run', method_start)
    
    # Extract the method content
    method_content = content[method_start:next_method]
    
    # Fix the method by ensuring proper indentation
    # The proper structure should be:
    # async def execute(self, cmd: str):
    #     if cmd.startswith("/memory"):
    #         ...
    #     cmd = cmd.strip().lower()
    #     
    #     if cmd == "/health":
    #         ...
    #     elif cmd == "/workers":
    #         ...
    #     elif cmd.startswith("/code"):
    #         ...
    #     elif cmd.startswith("/generate"):   <-- ADD THIS
    #         ...
    #     elif cmd.startswith("/search") or cmd.startswith("/ddg"):
    #         ...
    #     return None
    
    # Create properly indented generate command
    generate_block = '''
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
    
    # Find where to insert (before /search)
    search_pos = method_content.find('elif cmd.startswith("/search")')
    
    if search_pos != -1:
        # Insert the generate block before /search
        fixed_method = method_content[:search_pos] + generate_block + method_content[search_pos:]
        
        # Replace in content
        content = content[:method_start] + fixed_method + content[next_method:]
        
        # Save the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Fixed indentation and added /generate command")
    else:
        print("⚠️ Could not find /search command location")
else:
    print("❌ Could not find /search pattern in file")

print("\n🚀 Now run: python phoenix_kernel_v13.3.0.py")