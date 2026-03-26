import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# backend/workers/vision_worker.py
import asyncio
import ollama
import mss
import mss.tools
import base64
import io
import os
import tempfile
import logging
from datetime import datetime
from PIL import Image
from base_worker import BaseWorker

logger = logging.getLogger(__name__)

class VisionWorker(BaseWorker):
    def __init__(self):
        super().__init__("vision")
        self.description = "Screen analysis and computer vision"
        self.model = "llava:7b"
        self.sct = mss.mss()
    
    def _capture_screen(self, monitor: int = 1) -> Image.Image:
        monitors = self.sct.monitors
        if monitor >= len(monitors):
            monitor = 1
        screenshot = self.sct.grab(monitors[monitor])
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return img
    
    def _image_to_base64(self, img: Image.Image) -> str:
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def _save_screenshot(self, img: Image.Image) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(tempfile.gettempdir(), f"screen_{timestamp}.png")
        img.save(filepath)
        return filepath
    
    async def analyze_screen(self, prompt: str, monitor: int = 1) -> str:
        logger.info(f"ðŸ‘ï¸ Capturing screen for analysis: {prompt}")
        img = await asyncio.to_thread(self._capture_screen, monitor)
        filepath = await asyncio.to_thread(self._save_screenshot, img)
        img_base64 = await asyncio.to_thread(self._image_to_base64, img)
        
        messages =[{"role": "user", "content": prompt, "images": [img_base64]}]
        response = await asyncio.to_thread(
            ollama.chat,
            model=self.model,
            messages=messages,
            options={"temperature": 0.2}
        )
        return response['message']['content']
    
    async def process(self, task: str, model: str = None, memory_bus=None) -> dict:
        self.set_memory_bus(memory_bus)
        task_lower = task.lower().strip()
        analysis_result = ""
        
        if task_lower in["describe screen", "what do you see", "look"]:
            analysis_result = await self.analyze_screen("Describe what you see on this screen in detail.")
            content = f"ðŸ‘ï¸ **Screen Analysis:**\n\n{analysis_result}"
            
        elif task_lower.startswith("find "):
            element = task[5:].strip()
            analysis_result = await self.analyze_screen(f"Look at this screen and tell me where I can find '{element}'. Describe its location.")
            content = f"ðŸ” **Looking for '{element}':**\n\n{analysis_result}"
            
        elif "read text" in task_lower or "ocr" in task_lower:
            analysis_result = await self.analyze_screen("Read all the text you can see on this screen. Just output the raw text.")
            content = f"ðŸ“ **Text detected:**\n\n{analysis_result}"
            
        elif task_lower.startswith("analyze:") or task_lower.startswith("vision:"):
            prompt = task.replace("analyze:", "").replace("vision:", "").strip()
            analysis_result = await self.analyze_screen(prompt)
            content = f"ðŸ‘ï¸ **Analysis:**\n\n{analysis_result}"
            
        elif task_lower in ["screenshot", "capture"]:
            img = await asyncio.to_thread(self._capture_screen)
            filepath = await asyncio.to_thread(self._save_screenshot, img)
            return {"content": f"ðŸ“¸ **Screenshot saved to:**\n`{filepath}`"}
            
        else:
            return {
                "content": "ðŸ‘ï¸ **Vision Worker Ready**\nCommands: `describe screen`, `find [element]`, `read text`, `analyze: [q]`, `screenshot`"
            }

        # ðŸ§  Publish what Vision saw to the Hive Mind
        if self.memory_bus and analysis_result:
            await self.publish(
                content=f"[VISION SAW]: {analysis_result}",
                metadata={"task": task}
            )
            logger.info("ðŸ‘ï¸ VisionWorker published insights to Sovereign Context Bus")

        return {"content": content}

    async def process(self, task: str, memory_bus=None):
        """Process task – auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}


