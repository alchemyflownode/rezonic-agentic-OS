import sys
import subprocess
import pkg_resources
from typing import List

# REQUIRED PACKAGES FOR THE HIVE
REQUIRED_PACKAGES = [
    'requests',
    'beautifulsoup4',
    'lxml',
    'scrapling'
]

def check_and_install():
    print("[GUARDIAN] Checking Sovereign Environment...")
    missing: List[str] = []
    
    for package in REQUIRED_PACKAGES:
        try:
            pkg_resources.get_distribution(package)
            print(f"[GUARDIAN] ✓ {package}")
        except pkg_resources.DistributionNotFound:
            print(f"[GUARDIAN] ✗ {package} (Missing)")
            missing.append(package)
    
    if missing:
        print(f"\n[GUARDIAN] Installing missing packages: {missing}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
            print("[GUARDIAN] ✓ All dependencies installed.")
        except subprocess.CalledProcessError as e:
            print(f"[GUARDIAN] Failed to install: {e}")
            sys.exit(1)

if __name__ == "__main__":
    check_and_install()
