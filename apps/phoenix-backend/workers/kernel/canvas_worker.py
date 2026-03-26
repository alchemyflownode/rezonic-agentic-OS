"""
Canvas Worker - ComfyUI Integration
Handles image and video generation via ComfyUI API
"""

import asyncio
import json
import aiohttp
import random
import time
from typing import Dict, Any, Optional
from pathlib import Path

from .base_worker import BaseWorker

class CanvasWorker(BaseWorker):
    def __init__(self):
        super().__init__("canvas", "AI Image/Video Generation via ComfyUI")
        self.comfy_url = "http://127.0.0.1:8188"
        self.is_ready = True
        self.workflows_path = Path("./workflows")
        self.workflows_path.mkdir(exist_ok=True)
        
    async def process(self, task: str, **kwargs) -> Dict[str, Any]:
        """Generate image or video"""
        return await self.track_processing(self._generate, task, **kwargs)
    
    async def _generate(self, task: str, mode: str = "image", **kwargs) -> Dict[str, Any]:
        self.log("info", f"Generating {mode}: {task[:50]}...")
        
        # Check if task contains mode prefix
        if task.startswith("video:"):
            mode = "video"
            task = task[6:]
        elif task.startswith("image:"):
            mode = "image"
            task = task[6:]
        
        # Load appropriate workflow
        workflow_file = self.workflows_path / f"{mode}_workflow_api.json"
        
        # Simulate ComfyUI API call
        await asyncio.sleep(1.5)  # Simulate generation time
        
        # Mock response - FIXED HERE
        output_filename = f"{mode}_{int(time.time())}.png"
        if mode == "video":
            output_filename = output_filename.replace(".png", ".mp4")
        
        # Create mock output
        output_url = f"http://localhost:8001/output/{output_filename}"
        
        # Generate prompt weights from task
        prompt_weights = {}
        words = task.split()[:5]
        for word in words:
            if len(word) > 3:
                prompt_weights[word] = round(random.uniform(0.8, 1.5), 1)
        
        return {
            "status": "success",
            "mode": mode,
            "prompt": task,
            "output_url": output_url,
            "filename": output_filename,
            "prompt_weights": prompt_weights,
            "generation_time": 1.5,
            "seed": random.randint(1000000, 9999999)
        }
    
    async def check_comfyui_status(self) -> bool:
        """Check if ComfyUI is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.comfy_url}/system_stats", timeout=2) as resp:
                    return resp.status == 200
        except:
            return False