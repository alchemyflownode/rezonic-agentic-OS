"""Hands Worker - Physical Control"""
import logging

logger = logging.getLogger(__name__)

class HandsWorker:
    def __init__(self, hive_bus=None):
        self.hive_bus = hive_bus
        logger.info("  🦾 HandsWorker initialized")
    
    async def health_check(self):
        return {"healthy": True, "worker": "hands"}
    
    async def process(self, task):
        return {"content": self._get_help()}
    
    async def process_stream(self, task):
        yield self._get_help()
    
    def _get_help(self):
        return """
🦾 **HANDS WORKER - Physical Control**

Commands:
  /hands open <app>      - Open application (notepad, chrome, spotify)
  /hands type <text>     - Type text (click first to focus)
  /hands hotkey <keys>   - Press hotkey (ctrl,c for copy)
  /hands screenshot      - Take screenshot
  /hands click           - Click at current position
  /hands move x,y        - Move mouse to coordinates
  /hands position        - Get current mouse position

Examples:
  /hands open notepad
  /hands type Hello from Symbiote!
  /hands hotkey ctrl,s
  /hands screenshot

⚠️ SAFETY: Move mouse to any corner to abort!
"""
