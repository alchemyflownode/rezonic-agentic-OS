# apply_memory_patch.py
# Automatically patches PHOENIX v13.3.0 with Sovereign Memory

import re
import sys
from pathlib import Path

KERNEL_FILE = Path("phoenix_kernel_v14c.py")

def apply_patch():
    if not KERNEL_FILE.exists():
        print(f"❌ Kernel file not found: {KERNEL_FILE}")
        return False
    
    with open(KERNEL_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Add import if not present
    if "from memory_manager import" not in content:
        import_line = "\nfrom memory_manager import SovereignMemoryManager, MemoryCommandHandler\n"
        # Find a good place to add import (after other imports)
        insert_pos = content.find("import logging")
        if insert_pos != -1:
            insert_pos = content.find("\n", insert_pos) + 1
            content = content[:insert_pos] + import_line + content[insert_pos:]
    
    # 2. Add memory manager initialization after config
    if "self.memory_manager = SovereignMemoryManager" not in content:
        init_line = '\n        # Initialize Sovereign Memory Manager\n        self.memory_manager = SovereignMemoryManager(config.MEMORY_DIR)\n        self.memory_commands = MemoryCommandHandler(self.memory_manager)\n        logger.info(f"🧠 Sovereign Memory Manager initialized: {len(self.memory_manager.entries)} entries")\n'
        # Find the end of __init__ method
        insert_pos = content.find("self.reflex = ReflexCommands(self)")
        if insert_pos != -1:
            content = content[:insert_pos] + init_line + content[insert_pos:]
    
    # 3. Add memory command handling in ReflexCommands.execute
    if "if cmd.startswith(\"/memory\"):" not in content:
        memory_handler = '''
        # Check memory commands first
        if cmd.startswith("/memory"):
            result = await self.kernel.memory_commands.handle(cmd)
            if result:
                return result
        
'''
        insert_pos = content.find("async def execute(self, cmd: str):")
        if insert_pos != -1:
            insert_pos = content.find("\n", insert_pos) + 1
            content = content[:insert_pos] + memory_handler + content[insert_pos:]
    
    # 4. Add memory API endpoints
    if "@self.app.get(\"/memory/stats\")" not in content:
        api_endpoints = '''

        @self.app.get("/memory/stats")
        async def memory_stats():
            return self.kernel.memory_manager.get_stats()

        @self.app.get("/memory/search")
        async def memory_search(query: str, limit: int = 10):
            results = self.kernel.memory_manager.search(query, limit=limit)
            return [r.to_dict() for r in results]
'''
        insert_pos = content.find("@self.app.get(\"/health\")")
        if insert_pos != -1:
            # Find the end of the health endpoint
            insert_pos = content.find("return {", insert_pos)
            insert_pos = content.find("\n", content.find("\n", insert_pos) + 1) + 1
            content = content[:insert_pos] + api_endpoints + content[insert_pos:]
    
    # Write back
    with open(KERNEL_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Patch applied successfully!")
    return True

if __name__ == "__main__":
    apply_patch()
