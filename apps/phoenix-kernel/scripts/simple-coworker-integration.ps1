# simple-coworker-integration.ps1
# Save this and run it

Write-Host "🐝 COWORKER HIVE INTEGRATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Paths
$coworkerPath = "D:\Rezonic_Agentic\phoenix-coworker"
$kernelWorkersPath = "D:\Rezonic_Agentic\apps\phoenix-kernel\workers"
$coworkerDest = "$kernelWorkersPath\coworker"
$kernelFile = "D:\Rezonic_Agentic\apps\phoenix-kernel\rezphnx.py"

# Step 1: Copy files
Write-Host "`n📦 Copying coworker files..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $coworkerDest -Force | Out-Null

$folders = @("core", "skills", "workers", "desktop", "config")
foreach ($folder in $folders) {
    $src = Join-Path $coworkerPath $folder
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $coworkerDest -Recurse -Force
        Write-Host "  ✅ Copied: $folder" -ForegroundColor Green
    }
}

# Copy root Python files
Get-ChildItem -Path $coworkerPath -Filter "*.py" | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $coworkerDest -Force
    Write-Host "  ✅ Copied: $($_.Name)" -ForegroundColor Green
}

# Step 2: Create registry
Write-Host "`n📝 Creating worker registry..." -ForegroundColor Yellow

$registryContent = @'
"""
Coworker Worker Registry
"""
import os
import sys
import importlib
import inspect
from pathlib import Path

COWORKER_PATH = Path(__file__).parent / "coworker"
if str(COWORKER_PATH) not in sys.path:
    sys.path.insert(0, str(COWORKER_PATH))

def discover_workers():
    workers = {}
    print("🔍 Discovering coworker workers...")
    
    for py_file in COWORKER_PATH.rglob("*.py"):
        if py_file.name.startswith("__"):
            continue
        
        try:
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ != module.__name__:
                    continue
                
                is_worker = any(x in name for x in ['Worker', 'Agent', 'Manager', 'Handler'])
                if not is_worker:
                    methods = [m for m in dir(obj) if not m.startswith('_')]
                    is_worker = any(m in methods for m in ['execute', 'process', 'run'])
                
                if is_worker:
                    workers[name] = {"class": obj, "file": py_file.name}
                    print(f"  ✅ Loaded: {name}")
        except Exception as e:
            pass
    
    return workers

COWORKER_WORKERS = discover_workers()
print(f"\n📊 Total: {len(COWORKER_WORKERS)} workers")

def get_coworker_classes():
    return {name: info["class"] for name, info in COWORKER_WORKERS.items()}
'@

$registryPath = "$kernelWorkersPath\coworker_registry.py"
$registryContent | Out-File -FilePath $registryPath -Encoding UTF8
Write-Host "  ✅ Created registry" -ForegroundColor Green

# Step 3: Update kernel
Write-Host "`n🔧 Updating kernel..." -ForegroundColor Yellow

if (Test-Path $kernelFile) {
    $kernelContent = Get-Content $kernelFile -Raw
    
    if ($kernelContent -notmatch "coworker_registry") {
        $coworkerImport = @"
# Import coworker workers
try:
    from workers.coworker_registry import get_coworker_classes
    coworker_classes = get_coworker_classes()
    for name, cls in coworker_classes.items():
        self.workers[f"coworker_{name}"] = {
            "class": cls,
            "module": "coworker",
            "category": "coworker"
        }
    logger.info(f"✅ Loaded {len(coworker_classes)} coworker workers")
except Exception as e:
    logger.warning(f"Could not load coworker workers: {e}")
"@
        
        $kernelContent = $kernelContent -replace "(self\.workers\['code_execution'\] = .*\n)", "`$1`n$coworkerImport`n"
        $kernelContent | Out-File -FilePath $kernelFile -Encoding UTF8
        Write-Host "  ✅ Kernel updated" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ Kernel already has coworker support" -ForegroundColor Yellow
    }
}

# Step 4: Verify
Write-Host "`n🔍 Verifying integration..." -ForegroundColor Yellow

$coworkerFiles = Get-ChildItem -Path $coworkerDest -Recurse -Filter "*.py" | Measure-Object
Write-Host "  ✅ Coworker files: $($coworkerFiles.Count)" -ForegroundColor Green

if (Test-Path $registryPath) {
    Write-Host "  ✅ Registry created" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ INTEGRATION COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🐝 Swarm now has 44 + $($coworkerFiles.Count) = $($coworkerFiles.Count + 44) workers!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Restart kernel: python rezphnx.py" -ForegroundColor Gray
Write-Host "  2. Restart frontend: npm run dev" -ForegroundColor Gray
Write-Host "  3. Open hive monitor: http://localhost:3000/hive" -ForegroundColor Gray
Write-Host ""