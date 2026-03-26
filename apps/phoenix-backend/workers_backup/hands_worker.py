from .base_worker import BaseWorker
﻿import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
"""Hands Worker - Gives the Symbiote physical control over the PC"""

import os
import sys
import asyncio
import subprocess
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import GUI libraries with graceful fallback
try:
    import pyautogui
    import pygetwindow as gw
    # CRITICAL SAFETY: Move mouse to any corner to abort
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.5  # Pause between actions
    GUI_AVAILABLE = True
    logger.info("âœ… PyAutoGUI loaded - Symbiote has physical hands!")
except ImportError:
    GUI_AVAILABLE = False
    logger.warning("âš ï¸ PyAutoGUI not installed. Run: pip install pyautogui pygetwindow pillow")

class HandsWorker(BaseWorker):
    """
    The Digital Poltergeist - Grants the Symbiote direct control over the host OS.
    Can open apps, type text, press hotkeys, and capture screens.
    """
    
    def __init__(self, memory_bus=None, hive_bus=None):
        self.memory_bus = memory_bus
        super().__init__('hands', hive_bus)
        self.name = "HandsWorker"
        logger.info("ðŸ¦¾ Digital Hands mounted and ready.")
    
    def set_memory_bus(self, memory_bus):
        self.memory_bus = memory_bus
    
    async def process(self, task: str, model: str = None, memory_bus=None) -> dict:
        """Main entry point for hand commands"""
        if memory_bus:
            self.set_memory_bus(memory_bus)
        
        # Parse command
        if task.startswith("/hands"):
            command = task.replace("/hands", "").strip()
            return await self._route_command(command)
        else:
            return {"content": self._get_help()}
    
    async def _route_command(self, command: str) -> dict:
        """Route to appropriate hand action"""
        parts = command.split(" ", 1)
        if not parts:
            return {"content": self._get_help()}
        
        action = parts[0].lower()
        payload = parts[1] if len(parts) > 1 else ""
        
        if action == "open":
            return await self._open_application(payload)
        elif action == "type":
            return await self._type_text(payload)
        elif action == "hotkey":
            return await self._press_hotkey(payload)
        elif action == "screenshot":
            return await self._take_screenshot()
        elif action == "click":
            return await self._click()
        elif action == "move":
            return await self._move_mouse(payload)
        else:
            return {"content": f"âŒ Unknown action: {action}\n\n{self._get_help()}"}
    
    async def _open_application(self, app_name: str) -> dict:
        """Open an application"""
        logger.info(f"ðŸ¦¾ Opening: {app_name}")
        try:
            if sys.platform == "win32":
                # Windows: use 'start' command
                subprocess.Popen(f'start {app_name}', shell=True)
                return {"content": f"âœ… Opened {app_name}"}
            elif sys.platform == "darwin":
                subprocess.Popen(['open', '-a', app_name])
                return {"content": f"âœ… Opened {app_name}"}
            else:
                subprocess.Popen([app_name])
                return {"content": f"âœ… Launched {app_name}"}
        except Exception as e:
            return {"content": f"âŒ Failed to open {app_name}: {str(e)}"}
    
    async def _type_text(self, text: str) -> dict:
        """Type text as if human"""
        if not GUI_AVAILABLE:
            return {"content": "âŒ PyAutoGUI not installed. Run: pip install pyautogui"}
        
        logger.info(f"ðŸ¦¾ Typing: {text[:30]}...")
        # Run in thread to not block asyncio
        await asyncio.to_thread(pyautogui.write, text, interval=0.05)
        return {"content": f"âœ… Typed {len(text)} characters"}
    
    async def _press_hotkey(self, keys_str: str) -> dict:
        """Press hotkey combination (e.g., 'ctrl,c' for copy)"""
        if not GUI_AVAILABLE:
            return {"content": "âŒ PyAutoGUI not installed"}
        
        keys =[k.strip().lower() for k in keys_str.split(',')]
        logger.info(f"ðŸ¦¾ Pressing hotkey: {keys}")
        await asyncio.to_thread(pyautogui.hotkey, *keys)
        return {"content": f"âœ… Pressed: {keys_str}"}
    
    async def _take_screenshot(self) -> dict:
        """Capture screenshot"""
        if not GUI_AVAILABLE:
            return {"content": "âŒ PyAutoGUI not installed"}
        
        # Ensure directory exists
        screenshot_dir = Path("hive_memory/screenshots")
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        filename = screenshot_dir / f"screenshot_{int(time.time())}.png"
        
        # Take screenshot
        screenshot = await asyncio.to_thread(pyautogui.screenshot)
        screenshot.save(str(filename))
        
        # Store in memory if available
        if self.memory_bus:
            await self.memory_bus.store(
                content=f"Screenshot taken at {time.ctime()}",
                metadata={"type": "screenshot", "path": str(filename)}
            )
        
        return {"content": f"âœ… Screenshot saved to {filename}"}
    
    async def _click(self) -> dict:
        """Click at current mouse position"""
        if not GUI_AVAILABLE:
            return {"content": "âŒ PyAutoGUI not installed"}
        
        await asyncio.to_thread(pyautogui.click)
        return {"content": "âœ… Clicked"}
    
    async def _move_mouse(self, coords: str) -> dict:
        """Move mouse to coordinates (x,y)"""
        if not GUI_AVAILABLE:
            return {"content": "âŒ PyAutoGUI not installed"}
        
        try:
            x, y = map(int, coords.split(','))
            await asyncio.to_thread(pyautogui.moveTo, x, y, duration=0.5)
            return {"content": f"âœ… Moved mouse to ({x}, {y})"}
        except:
            return {"content": "âŒ Invalid coordinates. Use: move x,y"}
    
    def _get_help(self) -> str:
        return """ðŸ¦¾ **HANDS WORKER - Physical Control**

Commands:
  /hands open <app>      - Open application (notepad, chrome, spotify)
  /hands type <text>     - Type text (click first to focus)
  /hands hotkey <keys>   - Press hotkey (ctrl,c for copy)
  /hands screenshot      - Take screenshot
  /hands click           - Click at current position
  /hands move x,y        - Move mouse to coordinates

Examples:
  /hands open notepad
  /hands type Hello from Symbiote!
  /hands hotkey ctrl,s
  /hands screenshot

âš ï¸ SAFETY: Move mouse to any corner to abort!
"""

    async def process(self, task: str, memory_bus=None):
        """Process task – auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}

