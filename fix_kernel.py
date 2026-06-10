import re
import sys

# Read the kernel file
kernel_file = r"D:\Rezonic_Agentic\apps\phoenix-kernel\rezonic_unified_v15.py"
with open(kernel_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Add import at top if not exists
if 'from api_trade import router' not in content:
    content = 'from api_trade import router\n\n' + content
    print("✓ Added import")

# Find app = FastAPI() and add router registration after it
pattern = r'(app = FastAPI\([^)]*\))\s*\n'
match = re.search(pattern, content)
if match:
    app_line = match.group(1)
    registration = f'''{app_line}

# API v1 routes - Constitutional Trading
app.include_router(router)
'''
    content = content.replace(app_line, registration)
    print("✓ Added router registration")
else:
    print("⚠ Could not find app = FastAPI()")

# Save the file
with open(kernel_file, 'w', encoding='utf-8') as f:
    f.write(content)
print("✓ Saved file")

# Verify syntax
import py_compile
try:
    py_compile.compile(kernel_file, doraise=True)
    print("✓ Syntax is valid!")
except Exception as e:
    print(f"✗ Syntax error: {e}")
