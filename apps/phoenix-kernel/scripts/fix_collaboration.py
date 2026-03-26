# AUTO-FIXED IMPORT PATH
import sys
from pathlib import Path
_workers_dir = Path(__file__).parent.resolve()
if str(_workers_dir) not in sys.path:
    sys.path.insert(0, str(_workers_dir))
# END AUTO-FIX
﻿#!/usr/bin/env python3
"""
PHOENIX v14.0.0-OKIRU - Collaboration Fix
"""

import re
import os
from pathlib import Path

# File paths
KERNEL_FILE = Path("D:/Rezonic_Agentic/apps/phoenix-kernel/phoenix_v14_omega_okiru.py")
BACKUP_FILE = Path("D:/Rezonic_Agentic/apps/phoenix-kernel/phoenix_v14_omega_okiru.py.backup_collab")

def fix_reflex_commands():
    print("🔧 PHOENIX Collaboration Fix")
    print("=" * 50)
    
    if not KERNEL_FILE.exists():
        print(f"❌ File not found: {KERNEL_FILE}")
        return False
    
    with open(KERNEL_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Backup created: {BACKUP_FILE}")
    
    # Add set_orchestrator method
    if 'def set_orchestrator' not in content:
        set_method = '''
    def set_orchestrator(self, orchestrator):
        """Set the orchestrator for collaboration commands"""
        self.orchestrator = orchestrator
        logger.info("✅ Orchestrator attached to ReflexCommands")
'''
        content = content.replace('class ReflexCommands:', 'class ReflexCommands:\n' + set_method)
        print("✅ Added set_orchestrator method")
    
    # Add orchestrator to kernel init
    if 'self.orchestrator = WorkerOrchestrator' not in content:
        orchestrator_init = '''
        # Initialize orchestrator for collaboration
        self.orchestrator = WorkerOrchestrator(self)
        self.reflex.set_orchestrator(self.orchestrator)
        logger.info("✅ Worker Orchestrator initialized")'''
        content = content.replace('self.reflex = ReflexCommands(self)', 'self.reflex = ReflexCommands(self)\n' + orchestrator_init)
        print("✅ Added orchestrator to kernel init")
    
    # Save
    with open(KERNEL_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ File saved: {KERNEL_FILE}")
    
    print("\n🎉 FIX COMPLETE! Restart Phoenix and test /collaborate")
    return True

if __name__ == "__main__":
    fix_reflex_commands()
