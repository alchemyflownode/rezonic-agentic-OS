import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import os
from modulefinder import ModuleFinder

backend_dir = r"D:\okiru-os\RezHiveOS\backend"
main_script = os.path.join(backend_dir, "main.py")

# 1. Get ALL Python files in the backend folder
all_py_files = set()
for root, dirs, files in os.walk(backend_dir):
    # Ignore cache and virtual environment folders
    if "__pycache__" in root or ".venv" in root or "venv" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            all_py_files.add(os.path.join(root, file))

# 2. Find all USED Python files starting from main.py
print("Tracing imports from main.py... (this might take a few seconds)")
finder = ModuleFinder(path=[backend_dir])
finder.run_script(main_script)

used_py_files = set()
used_py_files.add(main_script) # Add main.py itself

for name, mod in finder.modules.items():
    if mod.__file__ and mod.__file__.startswith(backend_dir) and mod.__file__.endswith('.py'):
        used_py_files.add(mod.__file__)

# 3. Find UNUSED files (All - Used)
unused_files = all_py_files - used_py_files

print(f"\n--- RESULTS ---")
print(f"Total .py files found: {len(all_py_files)}")
print(f"Total .py files actively imported: {len(used_py_files)}")
print(f"\n--- POTENTIALLY UNUSED FILES ({len(unused_files)}) ---")
for f in sorted(unused_files):
    # Print a clean relative path
    print(os.path.relpath(f, backend_dir))
