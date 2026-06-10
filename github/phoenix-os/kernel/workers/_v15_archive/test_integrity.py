#!/usr/bin/env python3
"""Test RezCoder's file integrity features"""

import subprocess
import os
from pathlib import Path


def test_integrity():
    # Create test directory
    test_dir = Path("test_integrity_files")
    test_dir.mkdir(exist_ok=True)
    
    # Create test files
    test_files = [
        ("empty.py", ""),
        ("tiny.py", "x"),
        ("mixed_ending.txt", "Line1\r\nLine2\nLine3\r\n"),
    ]
    
    print("\n" + "="*70)
    print("  ðŸ§ª TESTING FILE INTEGRITY FEATURES")
    print("="*70)
    
    # Set UTF-8 encoding for subprocess
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    for name, content in test_files:
        filepath = test_dir / name
        filepath.write_text(content, encoding='utf-8', errors='replace')
        print(f"\nðŸ“ Testing: {name}")
        print("â”€" * 60)
        
        # Run code-worker.py on the test file
        result = subprocess.run(
            ["python", "code-worker.py", str(filepath), "--verbose"],
            capture_output=True,
            text=True,
            env=env,
            encoding='utf-8'
        )
        
        print(result.stdout)
        if result.returncode != 0 and result.stderr:
            print("Error output:")
            print(result.stderr)
    
    # Clean up
    print("\n" + "="*70)
    print("  ðŸ§¹ CLEANING UP TEST FILES")
    print("="*70)
    for name, _ in test_files:
        filepath = test_dir / name
        filepath.unlink(missing_ok=True)
        print(f"   Removed: {name}")
    
    # Clean up report files
    import glob
    for report in glob.glob(str(test_dir / "*.md")):
        Path(report).unlink(missing_ok=True)
        print(f"   Removed: {Path(report).name}")
    
    for report in glob.glob(str(test_dir / "*.bak")):
        Path(report).unlink(missing_ok=True)
        print(f"   Removed: {Path(report).name}")
    
    test_dir.rmdir()
    print(f"\n   Removed test directory: {test_dir}")
    
    print("\n" + "="*70)
    print("  âœ… TEST COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    test_integrity()

