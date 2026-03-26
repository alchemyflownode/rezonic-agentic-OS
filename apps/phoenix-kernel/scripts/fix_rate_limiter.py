#!/usr/bin/env python3
# AUTO-FIXED IMPORT PATH
import sys
from pathlib import Path
_workers_dir = Path(__file__).parent.resolve()
if str(_workers_dir) not in sys.path:
    sys.path.insert(0, str(_workers_dir))
# END AUTO-FIX
"""
Auto-fix script for Phoenix v14.0.0-OKIRU rate limiter issue
Replaces slowapi.Limiter with FallbackRateLimiter
"""

import re
from pathlib import Path

# Path to your kernel file
KERNEL_FILE = Path("phoenix_v14_omega_okiru.py")
BACKUP_FILE = Path("phoenix_v14_omega_okiru.py.backup_fixed")

def fix_rate_limiter():
    """Replace slowapi.Limiter with FallbackRateLimiter"""
    
    # Read the original file
    with open(KERNEL_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create backup
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Backup created: {BACKUP_FILE}")
    
    # Check if FallbackRateLimiter already exists
    if 'class FallbackRateLimiter' in content:
        print("⚠️ FallbackRateLimiter already exists in file")
    else:
        # Find location to insert FallbackRateLimiter class (after SecurityError class)
        security_error_pos = content.find('class SecurityError(Exception):')
        if security_error_pos != -1:
            # Find the end of SecurityError class (next class definition or end of section)
            next_class_pos = content.find('class ', security_error_pos + 10)
            if next_class_pos == -1:
                next_class_pos = content.find('def ', security_error_pos + 10)
            
            # Prepare the FallbackRateLimiter class
            fallback_class = '''
# ============================================================================
# FALLBACK RATE LIMITER (v14.0.0-FIX)
# ============================================================================
class FallbackRateLimiter:
    def __init__(self, calls_per_period: int = 100, period_seconds: int = 60):
        self.calls_per_period = calls_per_period
        self.period_seconds = period_seconds
        self.calls = defaultdict(list)
    
    async def check(self, client_id: str) -> bool:
        now = time.time()
        self.calls[client_id] = [t for t in self.calls[client_id] if now - t < self.period_seconds]
        if len(self.calls[client_id]) >= self.calls_per_period:
            return False
        self.calls[client_id].append(now)
        return True

'''
            
            # Insert the class
            content = content[:next_class_pos] + fallback_class + content[next_class_pos:]
            print("✅ FallbackRateLimiter class inserted")
    
    # Find and replace the rate_limiter initialization in __init__
    # Pattern to find the problematic lines
    pattern = r'self\.rate_limiter = None\s+if HAS_SLOWAPI:\s+self\.rate_limiter = Limiter\(key_func=get_remote_address, default_limits=\[f"{config\.RATE_LIMIT_CALLS}/{config\.RATE_LIMIT_PERIOD}"\]\)'
    
    replacement = '''self.rate_limiter = FallbackRateLimiter(config.RATE_LIMIT_CALLS, config.RATE_LIMIT_PERIOD)'''
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        print("✅ Replaced slowapi.Limiter with FallbackRateLimiter")
    else:
        # Alternative pattern (if formatting is different)
        alt_pattern = r'self\.rate_limiter = None'
        if re.search(alt_pattern, content):
            content = re.sub(alt_pattern, replacement, content)
            print("✅ Replaced self.rate_limiter = None with FallbackRateLimiter")
        else:
            print("⚠️ Could not find rate_limiter initialization. Manual check needed.")
    
    # Write the fixed content back
    with open(KERNEL_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ Fix applied! File saved: {KERNEL_FILE}")
    print("\n📝 Next steps:")
    print("1. Restart your kernel: python phoenix_v14_omega_okiru.py")
    print("2. Test with: Invoke-RestMethod -Uri 'http://localhost:8002/kernel/stream' -Method Post -Body '{\"task\":\"/health\"}' -ContentType 'application/json'")
    print("\n💾 Backup saved as:", BACKUP_FILE)

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Phoenix v14.0.0-OKIRU Rate Limiter Fix")
    print("=" * 60)
    
    if not KERNEL_FILE.exists():
        print(f"❌ Error: {KERNEL_FILE} not found!")
        print("Make sure you're running this script in the same directory as your kernel file.")
    else:
        fix_rate_limiter()