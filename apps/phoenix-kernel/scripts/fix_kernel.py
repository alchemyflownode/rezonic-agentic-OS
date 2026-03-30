# fix_kernel.py
import re

def fix_kernel():
    """Automatically fix missing /kill/status endpoint"""
    
    file_path = "rezonic_unified_v15.py"
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Backup
    with open("rezonic_unified_v15_backup.py", 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("✅ Backup saved")
    
    # Find where to insert
    insert_index = -1
    for i, line in enumerate(lines):
        # Look for kill endpoints section
        if '@self.app.post("/kill")' in line:
            insert_index = i
            print(f"Found kill endpoint at line {i+1}")
            break
    
    if insert_index != -1:
        # The endpoint to add
        new_endpoint = [
            '\n',
            '        @self.app.get("/kill/status")\n',
            '        async def kill_status():\n',
            '            """Get kill switch status"""\n',
            '            return kill_switch.status()\n',
            '\n'
        ]
        
        # Insert before the kill post endpoint
        for offset, line in enumerate(new_endpoint):
            lines.insert(insert_index + offset, line)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✅ Added /kill/status endpoint")
    else:
        print("⚠️ Could not find @self.app.post('/kill')")
        print("Searching for alternative location...")
        
        # Alternative: search for any kill related line
        for i, line in enumerate(lines):
            if '/kill' in line and 'post' in line.lower():
                print(f"Found: line {i+1}: {line.strip()}")
                insert_index = i
                break
        
        if insert_index != -1:
            new_endpoint = [
                '\n',
                '        @self.app.get("/kill/status")\n',
                '        async def kill_status():\n',
                '            """Get kill switch status"""\n',
                '            return kill_switch.status()\n',
                '\n'
            ]
            for offset, line in enumerate(new_endpoint):
                lines.insert(insert_index + offset, line)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print("✅ Added /kill/status endpoint (alternative method)")
    
    print("\n" + "="*50)
    print("✅ Fix complete!")
    print("="*50)
    print("🔄 Restart your kernel:")
    print("   python rezonic_unified_v15.py")
    print("\n🧪 Test:")
    print("   curl http://127.0.0.1:8002/kill/status")

if __name__ == "__main__":
    fix_kernel()