# Create archive structure
$archiveRoot = "D:\Rezonic_Agentic\archive"
$folders = @(
    "constitution", "architecture", "sdk", "sdk/docs", 
    "workers/krita-ai-bridge", "workers/rezsketch-governance", 
    "workers/motion-godmode", "workers/arcadia-sim", "workers/kinetic-ad-synth",
    "rezstack/docs", "analysis"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Path "$archiveRoot\$folder" -Force | Out-Null
}

Write-Host "📁 Archive structure created at $archiveRoot" -ForegroundColor Green

# 1. Constitution
Copy-Item "D:\okiru-os\CONSTITUTIONAL_DECLARATION.md" "$archiveRoot\constitution\" -Force -ErrorAction SilentlyContinue
Copy-Item "D:\okiru-os\rezonix-principles.md" "$archiveRoot\constitution\" -Force -ErrorAction SilentlyContinue
Copy-Item "D:\okiru-os\RezHiveOS\REZHIVE_CONSTITUTIONAL.MD" "$archiveRoot\constitution\REZHIVE_CONSTITUTIONAL.md" -Force -ErrorAction SilentlyContinue
Copy-Item "D:\okiru-os\RezHiveOS\SCE_MANIFESTO.md" "$archiveRoot\constitution\" -Force -ErrorAction SilentlyContinue
Copy-Item "D:\okiru-os\RezHiveOS\AGENTS.md" "$archiveRoot\constitution\" -Force -ErrorAction SilentlyContinue
Copy-Item "D:\okiru-os\RezHiveOS\MANIFESTO.md" "$archiveRoot\constitution\" -Force -ErrorAction SilentlyContinue

# 2. Architecture
Copy-Item "D:\okiru-os\RezHive V12\V13_STRUCTURE.md" "$archiveRoot\architecture\" -Force -ErrorAction SilentlyContinue
Copy-Item "D:\okiru-os\RezHive V12\README.md" "$archiveRoot\architecture\REZHIVE_V12_README.md" -Force -ErrorAction SilentlyContinue
if (Test-Path "D:\okiru-os\RezHive V12\cognitive_imports") {
    Copy-Item "D:\okiru-os\RezHive V12\cognitive_imports\*" "$archiveRoot\architecture\cognitive_imports\" -Recurse -Force -ErrorAction SilentlyContinue
}
Copy-Item "D:\okiru-os\RezHiveOS\ROADMAP.md" "$archiveRoot\architecture\" -Force -ErrorAction SilentlyContinue
Copy-Item "D:\okiru-os\RezHiveOS\progress-notes.md" "$archiveRoot\architecture\" -Force -ErrorAction SilentlyContinue

# 3. SDK
Copy-Item "D:\okiru-os\sovereign-sdk\*.md" "$archiveRoot\sdk\" -Force -ErrorAction SilentlyContinue
if (Test-Path "D:\okiru-os\sovereign-sdk\docs") {
    Copy-Item "D:\okiru-os\sovereign-sdk\docs\*" "$archiveRoot\sdk\docs\" -Recurse -Force -ErrorAction SilentlyContinue
}

# 4. Alchemy Suite Workers
if (Test-Path "D:\okiru-os\apps\alchemy-suite\krita-ai-bridge") {
    Copy-Item "D:\okiru-os\apps\alchemy-suite\krita-ai-bridge\*" "$archiveRoot\workers\krita-ai-bridge\" -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path "D:\okiru-os\apps\alchemy-suite\rezsketch-governance") {
    Copy-Item "D:\okiru-os\apps\alchemy-suite\rezsketch-governance\*" "$archiveRoot\workers\rezsketch-governance\" -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path "D:\okiru-os\apps\alchemy-suite\motion-godmode") {
    Copy-Item "D:\okiru-os\apps\alchemy-suite\motion-godmode\*" "$archiveRoot\workers\motion-godmode\" -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path "D:\okiru-os\apps\alchemy-suite\arcadia-sim") {
    Copy-Item "D:\okiru-os\apps\alchemy-suite\arcadia-sim\*" "$archiveRoot\workers\arcadia-sim\" -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path "D:\okiru-os\apps\alchemy-suite\kinetic-ad-synth") {
    Copy-Item "D:\okiru-os\apps\alchemy-suite\kinetic-ad-synth\*" "$archiveRoot\workers\kinetic-ad-synth\" -Recurse -Force -ErrorAction SilentlyContinue
}

# 5. RezStack OS
if (Test-Path "D:\okiru-os\The Reztack OS\docs") {
    Copy-Item "D:\okiru-os\The Reztack OS\docs\*" "$archiveRoot\rezstack\docs\" -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path "D:\okiru-os\The Reztack OS\src\STRUCTURE.md") {
    Copy-Item "D:\okiru-os\The Reztack OS\src\STRUCTURE.md" "$archiveRoot\rezstack\" -Force -ErrorAction SilentlyContinue
}

# 6. Analysis Reports
Copy-Item "D:\okiru-os\RezHiveOS\scan_results\*" "$archiveRoot\analysis\" -Force -ErrorAction SilentlyContinue
Copy-Item "D:\okiru-os\The Reztack OS\docs\PRODUCTION_AUDIT_REPORT.md" "$archiveRoot\analysis\" -Force -ErrorAction SilentlyContinue

Write-Host "`n✅ ARCHIVE COMPLETE!" -ForegroundColor Green
Write-Host "📁 Location: $archiveRoot" -ForegroundColor Cyan

# Show summary
Write-Host "`n📊 ARCHIVE SUMMARY:" -ForegroundColor Yellow
Get-ChildItem $archiveRoot -Recurse -File | Group-Object Directory | ForEach-Object {
    $count = $_.Count
    $name = Split-Path $_.Name -Parent
    Write-Host "   $name : $count files"
}