# setup_desktop.ps1
# Run this from D:\Rezonic_Agentic\apps\phoenix-kernel\

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "🚀 Phoenix Desktop Integration Setup" -ForegroundColor Cyan

# 1. Create desktop folder
$desktopFolder = ".\desktop"
if (-not (Test-Path $desktopFolder)) {
    New-Item -ItemType Directory -Path $desktopFolder | Out-Null
    Write-Host "✅ Created desktop folder"
} else {
    Write-Host "✅ desktop folder already exists"
}

# 2. Create the five files with content
Write-Host "📝 Creating desktop module files..."

# --- client.py ---
$clientContent = @'
import httpx
import json
import logging

logger = logging.getLogger("PHOENIX.CLIENT")

class KernelClient:
    def __init__(self, base_url="http://127.0.0.1:8002", api_key="rez-hive-admin-key-2026"):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=120.0)
        self.headers = {"Content-Type": "application/json", "X-Hive-API-Key": api_key}

    async def check_health(self):
        try:
            r = await self.client.get(f"{self.base_url}/health", headers=self.headers)
            return r.status_code == 200
        except:
            return False

    async def send_task(self, task):
        async with self.client.stream("POST", f"{self.base_url}/kernel/stream", json={"task": task}, headers=self.headers) as resp:
            if resp.status_code != 200:
                return {"success": False, "error": f"HTTP {resp.status_code}"}
            full = []
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data.get("type") == "result":
                        full.append(data["content"])
                    elif data.get("type") == "error":
                        return {"success": False, "error": data["content"]}
            return {"success": True, "response": "".join(full)}

    async def close(self):
        await self.client.aclose()
'@
Set-Content -Path "$desktopFolder\client.py" -Value $clientContent -Encoding UTF8

# --- ui.py ---
$uiContent = @'
import tkinter as tk
import asyncio
import threading
import logging

logger = logging.getLogger("PHOENIX.UI")

class CommandOverlay:
    def __init__(self, kernel_client, loop):
        self.kernel = kernel_client
        self.loop = loop
        self.root = None
        self.entry = None

    def show(self):
        if self.root:
            self.root.destroy()
        self.root = tk.Tk()
        self.root.title("Phoenix Command")
        self.root.geometry("500x120")
        self.root.configure(bg='#1e1e1e')
        self.root.eval('tk::PlaceWindow . center')
        self.root.overrideredirect(True)

        label = tk.Label(self.root, text="🦊 What would you like me to do?",
                         bg='#1e1e1e', fg='#00e5ff', font=("Segoe UI", 12))
        label.pack(pady=(20, 10))

        self.entry = tk.Entry(self.root, font=("Segoe UI", 14), bg='#2d2d2d', fg='white',
                              insertbackground='white', relief='flat', width=45)
        self.entry.pack(pady=(0, 15), padx=20)
        self.entry.focus_set()

        self.entry.bind('<Return>', self.submit)
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        self.root.attributes('-topmost', True)

        self.root.mainloop()

    def submit(self, event):
        cmd = self.entry.get()
        if cmd:
            logger.info(f"Command: {cmd}")
            asyncio.run_coroutine_threadsafe(self.kernel.send_task(cmd), self.loop)
        self.root.destroy()
        self.root = None
'@
Set-Content -Path "$desktopFolder\ui.py" -Value $uiContent -Encoding UTF8

# --- presence.py ---
$presenceContent = @'
import asyncio
import threading
import pystray
from PIL import Image, ImageDraw
import keyboard
import logging
from .ui import CommandOverlay

logger = logging.getLogger("PHOENIX.DESKTOP")

class DesktopPresence:
    def __init__(self, kernel_client, loop):
        self.kernel_client = kernel_client
        self.loop = loop
        self.icon = None
        self.is_paused = False
        self.ui = CommandOverlay(kernel_client, loop)

    def create_icon_image(self):
        size = (64, 64)
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([8, 8, 56, 56], fill=(0, 229, 255, 255))
        draw.ellipse([16, 16, 48, 48], fill=(155, 114, 203, 255))
        draw.polygon([(32, 16), (24, 36), (36, 36), (28, 52), (40, 28), (28, 28)], fill=(255, 255, 255, 255))
        return img

    def show_status(self):
        logger.info(f"Status: {'Paused' if self.is_paused else 'Active'}")

    def quick_command(self):
        logger.info("Opening command overlay...")
        threading.Thread(target=self.ui.show, daemon=True).start()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        logger.info(f"Phoenix {'paused' if self.is_paused else 'resumed'}")

    def exit_app(self):
        logger.info("Shutting down desktop presence...")
        if self.icon:
            self.icon.stop()
        keyboard.unhook_all()

    def setup_hotkeys(self):
        keyboard.add_hotkey('ctrl+shift+space', self.quick_command, suppress=False)
        keyboard.add_hotkey('ctrl+shift+p', self.toggle_pause, suppress=False)
        logger.info("Hotkeys registered: Ctrl+Shift+Space (command), Ctrl+Shift+P (pause)")

    def create_menu(self):
        return pystray.Menu(
            pystray.MenuItem("Status", self.show_status),
            pystray.MenuItem("Quick Command", self.quick_command),
            pystray.MenuItem("Pause/Resume", self.toggle_pause),
            pystray.MenuItem("─" * 10, None, enabled=False),
            pystray.MenuItem("Exit", self.exit_app),
        )

    def run(self):
        self.setup_hotkeys()
        self.icon = pystray.Icon("phoenix_coworker", self.create_icon_image(),
                                 "Phoenix OS - Personal Coworker", self.create_menu())
        threading.Thread(target=self.icon.run, daemon=True).start()
        logger.info("Desktop presence started (system tray + hotkeys)")

    def stop(self):
        if self.icon:
            self.icon.stop()
        keyboard.unhook_all()
'@
Set-Content -Path "$desktopFolder\presence.py" -Value $presenceContent -Encoding UTF8

# --- watcher.py ---
$watcherContent = @'
import asyncio
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger("PHOENIX.WATCHER")

class PhoenixFileHandler(FileSystemEventHandler):
    def __init__(self, kernel_client):
        super().__init__()
        self.kernel = kernel_client
        self.watch_folders = [
            str(Path.home() / "Downloads"),
            str(Path.home() / "Documents" / "Notes"),
        ]
        self.ignore = ['*.tmp', '*.partial', '~$*']

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if any(path.match(p) for p in self.ignore):
            return
        time.sleep(0.5)  # let file finish writing
        if not path.exists():
            return

        ext = path.suffix.lower()
        if ext == '.pdf':
            asyncio.create_task(self.kernel.send_task(f"Summarize PDF: {event.src_path}"))
        elif ext in ['.zip', '.rar', '.7z']:
            asyncio.create_task(self.kernel.send_task(f"Extract archive: {event.src_path}"))
        elif ext in ['.txt', '.md']:
            asyncio.create_task(self.kernel.send_task(f"Index document: {event.src_path}"))
        elif ext in ['.py', '.js', '.ts']:
            asyncio.create_task(self.kernel.send_task(f"Analyze code: {event.src_path}"))

    def start(self):
        observer = Observer()
        for folder in self.watch_folders:
            p = Path(folder)
            if p.exists():
                observer.schedule(self, str(p), recursive=False)
                logger.info(f"Watching: {p}")
            else:
                logger.warning(f"Folder not found: {p}")
        observer.start()
        return observer

    def stop(self):
        logger.info("File watcher stopped")
'@
Set-Content -Path "$desktopFolder\watcher.py" -Value $watcherContent -Encoding UTF8

# --- __init__.py (empty) ---
New-Item -Path "$desktopFolder\__init__.py" -ItemType File -Force | Out-Null

Write-Host "✅ Desktop module files created"

# 3. Backup original zyphoenix5.py
if (Test-Path "zyphoenix5.py") {
    $backupName = "zyphoenix5_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').py"
    Copy-Item "zyphoenix5.py" $backupName
    Write-Host "✅ Backed up original zyphoenix5.py to $backupName"
} else {
    Write-Host "❌ zyphoenix5.py not found in current directory. Make sure you're in D:\Rezonic_Agentic\apps\phoenix-kernel"
    exit 1
}

# 4. Patch zyphoenix5.py
Write-Host "📝 Patching zyphoenix5.py..."

$filePath = "zyphoenix5.py"
$content = Get-Content $filePath -Raw

# --- Add imports after existing imports ---
$importBlock = @'
# Desktop coworker imports
from desktop.client import KernelClient
from desktop.presence import DesktopPresence
from desktop.watcher import PhoenixFileHandler

'@
# Insert after the block of imports. We'll look for a line that starts with "from " or "import " and insert after last import.
# Simpler: Insert after the line that says "# =======================================================================" after imports? We'll find the last import line.
# We'll use regex to find the last import line and insert after it.
$importPattern = '(?m)^(from|import)\s+.*$'
$lastImport = [regex]::Matches($content, $importPattern) | Select-Object -Last 1
if ($lastImport) {
    $insertPos = $lastImport.Index + $lastImport.Length
    $content = $content.Insert($insertPos, "`n" + $importBlock)
} else {
    Write-Host "⚠️ Could not find import lines, inserting at top."
    $content = $importBlock + $content
}

# --- Add desktop attributes in __init__ ---
# Find the line with "self.background_tasks = []"
$initPattern = '(?s)(self\.background_tasks\s*=\s*\[\])'
if ($content -match $initPattern) {
    $insertion = @'
        
        # Desktop presence components (will be started in startup)
        self.desktop_presence = None
        self.desktop_watcher = None
        self.desktop_observer = None
        self.desktop_client = None
'@
    $content = $content -replace $initPattern, "`$&$insertion"
} else {
    Write-Host "⚠️ Could not find self.background_tasks line, skipping attribute addition"
}

# --- Add desktop startup code in startup() ---
$startupMethodPattern = '(?s)(async def startup\(self\):.*?)(?=^    async def shutdown\(self\):|\Z)'
if ($content -match $startupMethodPattern) {
    $startupBody = $matches[1]
    # Find the end of the method (the line before shutdown or end of file)
    # We'll insert before the final print lines? Better insert before the last "print" in startup.
    $startupEndPattern = '(?s)(.*?)(\n        print\("="\*70\)\s*\n        print\(f"📡 API: http://.*?)'
    if ($startupBody -match $startupEndPattern) {
        $startupBeforePrint = $matches[1]
        $printLines = $matches[2]
        $newStartup = $startupBeforePrint + @'

        # Start desktop presence and file watcher
        try:
            loop = asyncio.get_running_loop()
            self.desktop_client = KernelClient(base_url=f"http://{settings.host}:{settings.port}")
            self.desktop_presence = DesktopPresence(self.desktop_client, loop)
            self.desktop_presence.run()
            self.desktop_watcher = PhoenixFileHandler(self.desktop_client)
            self.desktop_observer = self.desktop_watcher.start()
            logger.info("✅ Desktop coworker started (tray, hotkeys, file watcher)")
        except Exception as e:
            logger.error(f"Failed to start desktop components: {e}")

'@ + $printLines
        $content = $content -replace $startupMethodPattern, "async def startup(self):`n$newStartup"
    } else {
        Write-Host "⚠️ Could not find print lines in startup, skipping"
    }
} else {
    Write-Host "⚠️ Could not find startup method, skipping"
}

# --- Add shutdown cleanup in shutdown() ---
$shutdownMethodPattern = '(?s)(async def shutdown\(self\):.*?)(?=^    async def run\(self\):|\Z)'
if ($content -match $shutdownMethodPattern) {
    $shutdownBody = $matches[1]
    # Find the line before the final return? We'll insert before the final "logger.info("Shutdown complete")" line.
    $shutdownEndPattern = '(?s)(.*?)(logger\.info\("Shutdown complete"\)\s*$)'
    if ($shutdownBody -match $shutdownEndPattern) {
        $shutdownBefore = $matches[1]
        $lastLine = $matches[2]
        $newShutdown = $shutdownBefore + @'

        # Stop desktop components
        if (Get-Member -InputObject $self -Name desktop_observer) {
            if ($self.desktop_observer) {
                $self.desktop_observer.stop()
                $self.desktop_observer.join()
            }
        }
        if (Get-Member -InputObject $self -Name desktop_presence) {
            if ($self.desktop_presence) {
                $self.desktop_presence.stop()
            }
        }
        if (Get-Member -InputObject $self -Name desktop_client) {
            if ($self.desktop_client) {
                await $self.desktop_client.close()
            }
        }

'@ + "        $lastLine"
        $content = $content -replace $shutdownMethodPattern, "async def shutdown(self):`n$newShutdown"
    } else {
        Write-Host "⚠️ Could not find shutdown final line, skipping"
    }
} else {
    Write-Host "⚠️ Could not find shutdown method, skipping"
}

# --- Write patched file ---
$content | Set-Content -Path $filePath -Encoding UTF8

Write-Host "✅ Patched zyphoenix5.py"

Write-Host ""
Write-Host "🎉 Desktop integration complete!" -ForegroundColor Green
Write-Host "You can now run 'python zyphoenix5.py' and the desktop coworker will start automatically."
Write-Host "Make sure you have installed the dependencies:"
Write-Host "   pip install pystray pillow keyboard watchdog pyautogui pygetwindow"
Write-Host ""
Write-Host "If you encounter any issues, the original file was backed up as $backupName"