# fix_kill_status.py
import re

def add_kill_status():
    file_path = "rezonic_unified_v15.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if it already exists
    if '@self.app.get("/kill/status")' in content:
        print("✅ /kill/status already exists!")
        return
    
    # Find the kill endpoints section
    pattern = r'(@self\.app\.post\("/kill"\))'
    
    # The endpoint to add
    new_endpoint = '''        @self.app.get("/kill/status")
        async def kill_status():
            """Get kill switch status"""
            return kill_switch.status()

'''
    
    # Insert before the POST /kill
    if re.search(pattern, content):
        content = re.sub(pattern, new_endpoint + r'\1', content)
        print("✅ Added /kill/status endpoint")
    else:
        print("❌ Could not find @self.app.post('/kill')")
        # Alternative: search for kill-reset
        alt_pattern = r'(@self\.app\.post\("/kill/reset"\))'
        if re.search(alt_pattern, content):
            content = re.sub(alt_pattern, new_endpoint + r'\1', content)
            print("✅ Added /kill/status endpoint (alternative)")
        else:
            print("❌ Could not find any kill endpoints")
            return
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ Fixed! Restart kernel and test.")

if __name__ == "__main__":
    add_kill_status()