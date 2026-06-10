import subprocess
import asyncio
import pyperclip
import time
from typing import Dict, Any

class ClipboardWorker:
    """Manage clipboard, text operations, automation"""
    
    def __init__(self):
        self.name = "clipboard"
        self.history = []
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        task_lower = task.lower()
        
        # Copy text
        if "copy" in task_lower:
            text = kwargs.get("text", "")
            return await self._copy_text(text)
        
        # Paste text
        elif "paste" in task_lower or "get clipboard" in task_lower:
            return await self._paste_text()
        
        # Type text
        elif "type" in task_lower:
            text = kwargs.get("text", "")
            return await self._type_text(text)
        
        # Save clipboard
        elif "save" in task_lower:
            return await self._save_clipboard()
        
        # Recall clipboard
        elif "recall" in task_lower or "history" in task_lower:
            index = kwargs.get("index", 0)
            return await self._recall_clipboard(index)
        
        return {"error": f"Unknown clipboard operation: {task}", "success": False}
    
    async def _copy_text(self, text: str) -> Dict[str, Any]:
        try:
            pyperclip.copy(text)
            self.history.append({"text": text[:100], "timestamp": time.time()})
            if len(self.history) > 50:
                self.history.pop(0)
            return {"success": True, "message": f"Copied: {text[:50]}...", "length": len(text)}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _paste_text(self) -> Dict[str, Any]:
        try:
            text = pyperclip.paste()
            return {"success": True, "text": text, "length": len(text)}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _type_text(self, text: str) -> Dict[str, Any]:
        try:
            # Simulate typing using pyautogui
            import pyautogui
            pyautogui.write(text, interval=0.05)
            return {"success": True, "message": f"Typed: {text[:50]}...", "length": len(text)}
        except ImportError:
            return {"error": "pyautogui not installed. Run: pip install pyautogui", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _save_clipboard(self) -> Dict[str, Any]:
        try:
            text = pyperclip.paste()
            filename = f"clipboard_{int(time.time())}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text)
            return {"success": True, "saved_to": filename, "size": len(text)}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _recall_clipboard(self, index: int = 0) -> Dict[str, Any]:
        try:
            if not self.history:
                return {"error": "No clipboard history", "success": False}
            item = self.history[-index-1] if index < len(self.history) else self.history[-1]
            pyperclip.copy(item["text"])
            return {"success": True, "message": f"Recalled from history", "text": item["text"][:100]}
        except Exception as e:
            return {"error": str(e), "success": False}