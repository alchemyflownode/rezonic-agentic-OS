import re
from pathlib import Path

kernel_path = Path("kernel.py")

# Read the file
content = kernel_path.read_text(encoding="utf-8")

# Find where the class ends (right before if __name__)
end_of_class = content.find('if __name__ == "__main__":')

if end_of_class == -1:
    print("⚠️ Could not find main block")
else:
    # Keep everything up to that point
    clean_content = content[:end_of_class]
    
    # Also remove any trailing junk
    clean_content = clean_content.rstrip()
    
    # Add back the main block if it exists
    main_block = content[end_of_class:]
    
    # Check if there are any @app references outside the class
    if re.search(r'^@app\.', main_block, re.MULTILINE):
        print("⚠️ Found @app references outside class - removing them")
        # Remove lines that start with @app or are from trading consciousness
        lines = main_block.split('\n')
        filtered_lines = []
        skip = False
        for line in lines:
            if 'trading_consciousness' in line or line.strip().startswith('@app.'):
                skip = True
                continue
            if skip and (line.strip() == '' or line.strip().startswith('def ')):
                skip = False
            if not skip:
                filtered_lines.append(line)
        main_block = '\n'.join(filtered_lines)
    
    # Write back
    kernel_path.write_text(clean_content + '\n' + main_block, encoding="utf-8")
    print("✅ Fixed kernel.py - removed orphaned @app references")
    
    # Show what was removed
    print("\n📋 Removed sections:")
    for line in main_block.split('\n'):
        if 'trading_consciousness' in line or '@app' in line:
            print(f"  • {line[:80]}")
