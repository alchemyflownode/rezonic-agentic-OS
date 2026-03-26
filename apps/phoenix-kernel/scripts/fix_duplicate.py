# fix_duplicate.py
import re

file_path = r"D:\Rezonic_Agentic\apps\phoenix-kernel\phoenix_kernel_v14e.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the FIRST Constitution class (the one WITHOUT validate method)
# Pattern matches the old Constitution section
old_constitution_pattern = r'# ============================================================================\n# CONSTITUTION & MEMORY\n# ============================================================================\n\nclass Constitution:\n    def __init__\(self\):\n        self\.laws = config\.CONSTITUTION_LAWS\n        self\.ruling_history = \[\]\n    def evaluate\(self, action: str, context: Optional\[Dict\] = None\) -> dict:\n        action_lower = action\.lower\(\)\n        dangerous = \[\'rm -rf\', \'format\', \'del \', \'shutdown\', \'reboot\', \'mkfs\'\]\n        if any\(d in action_lower for d in dangerous\):\n            return \{"approved": False, "reason": "Safety Violation", "score": 0\}\n        return \{"approved": True, "reason": "Constitution Satisfied", "score": 90\}\n    async def record_ruling\(self, action, ruling\):\n        self\.ruling_history\.append\(\{"action": action\[:100\], "ruling": ruling, "timestamp": time\.time\(\)\}\)\n    def get_stats\(self\):\n        return \{"total_rulings": len\(self\.ruling_history\), "laws": self\.laws, "recent": self\.ruling_history\[-5:\]\}\n\nclass SovereignMemory:'

# Alternative: simpler approach - remove the entire old Constitution section
# Find the line numbers (approximate)
lines = content.split('\n')

new_lines = []
skip_old_constitution = False
found_old_constitution = False

for i, line in enumerate(lines):
    # Detect start of old Constitution section
    if '# ============================================================================' in line and i < 500:
        # Check next few lines for the old Constitution pattern
        if i + 3 < len(lines) and 'class Constitution:' in lines[i+2]:
            # This might be the old one
            skip_old_constitution = True
            found_old_constitution = True
            continue
    
    # Detect end of old Constitution section (when we hit SovereignMemory)
    if skip_old_constitution and 'class SovereignMemory:' in line:
        skip_old_constitution = False
        # Add the enhanced Constitution here instead
        enhanced = '''
# ============================================================================
# CONSTITUTION (ENHANCED WITH VALIDATE METHOD)
# ============================================================================

class Constitution:
    def __init__(self):
        self.laws = config.CONSTITUTION_LAWS
        self.ruling_history = []
    
    def evaluate(self, action: str, context: Optional[Dict] = None) -> dict:
        action_lower = action.lower()
        dangerous = ['rm -rf', 'format', 'del ', 'shutdown', 'reboot', 'mkfs']
        if any(d in action_lower for d in dangerous):
            return {"approved": False, "reason": "Safety Violation", "score": 0}
        return {"approved": True, "reason": "Constitution Satisfied", "score": 90}
    
    async def validate(self, plan: OrchestrationPlan) -> Dict[str, Any]:
        """Validate plan against constitution"""
        for task in plan.tasks:
            result = self.evaluate(task.description)
            if not result["approved"]:
                return {"approved": False, "reason": result["reason"], "score": 0}
        return {"approved": True, "reason": "All tasks approved", "score": 85}
    
    async def record_ruling(self, action, ruling):
        self.ruling_history.append({"action": action[:100], "ruling": ruling, "timestamp": time.time()})
    
    def get_stats(self):
        return {"total_rulings": len(self.ruling_history), "laws": self.laws, "recent": self.ruling_history[-5:]}
'''
        new_lines.append(enhanced)
        new_lines.append(line)
        continue
    
    if not skip_old_constitution:
        new_lines.append(line)

# Write fixed file
with open(file_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print(f"✅ Fixed! Removed duplicate Constitution class")
print(f"📁 File: {file_path}")