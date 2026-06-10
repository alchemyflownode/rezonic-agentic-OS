"""
Vision Worker for Phoenix Coworker

Handles screen capture and image analysis.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from .base import BaseWorker


class VisionWorker(BaseWorker):
    """
    Vision worker for screen capture and image analysis.
    
    Provides:
    - Screenshot capture
    - Image analysis (via LLM)
    - Screen region extraction
    """
    
    def __init__(self, kernel: Any):
        super().__init__(kernel, "vision")
        
        # Try to import optional dependencies
        try:
            import PIL.ImageGrab
            self._pil_available = True
        except ImportError:
            self._pil_available = False
        
        try:
            import pyautogui
            self._pyautogui_available = True
        except ImportError:
            self._pyautogui_available = False
    
    async def run(self):
        """Vision worker doesn't need a continuous loop"""
        while self._running:
            await asyncio.sleep(1)
    
    async def process(self, command: str, context: Dict = None) -> Dict:
        """Process a vision command"""
        context = context or {}
        
        words = command.lower().split()
        if not words:
            return {"success": False, "error": "Empty command"}
        
        action = words[0]
        
        if action in ["screenshot", "capture", "screen"]:
            return await self.capture_screen()
        
        elif action in ["analyze", "describe"]:
            image_path = context.get("image_path") or (words[1] if len(words) > 1 else None)
            if image_path:
                return await self.analyze_image(image_path)
            return {"success": False, "error": "No image specified"}
        
        return {"success": False, "error": f"Unknown vision action: {action}"}
    
    async def capture_screen(self, region: tuple = None) -> Dict:
        """
        Capture a screenshot.
        
        Args:
            region: Optional (left, top, right, bottom) tuple
        
        Returns:
            Screenshot result with path
        """
        if not self._pil_available:
            return {
                "success": False,
                "error": "PIL not available. Install with: pip install Pillow"
            }
        
        try:
            from PIL import ImageGrab
            
            # Capture screen
            screenshot = ImageGrab.grab(bbox=region)
            
            # Save to file
            screenshot_dir = self.kernel.config.data_dir / "screenshots"
            screenshot_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = screenshot_dir / f"screenshot_{timestamp}.png"
            
            screenshot.save(path)
            
            return {
                "success": True,
                "path": str(path),
                "size": screenshot.size,
                "region": region
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_image(self, image_path: str) -> Dict:
        """
        Analyze an image using the brain worker.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Analysis result
        """
        try:
            path = Path(image_path).expanduser()
            
            if not path.exists():
                return {"success": False, "error": f"Image not found: {image_path}"}
            
            # For now, just return basic info
            # In a full implementation, this would use the brain worker with vision capabilities
            from PIL import Image
            
            img = Image.open(path)
            
            # Get brain worker to describe
            brain = self.kernel.get_worker("brain")
            if brain:
                prompt = f"Describe what you might see in an image of size {img.size} with mode {img.mode}"
                result = await brain.process(prompt, {})
                description = result.get("response", "Could not analyze image")
            else:
                description = f"Image: {img.size[0]}x{img.size[1]}, mode: {img.mode}"
            
            return {
                "success": True,
                "path": str(path),
                "size": img.size,
                "mode": img.mode,
                "description": description
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def find_on_screen(self, image_path: str) -> Dict:
        """
        Find an image on the screen.
        
        Args:
            image_path: Path to template image
        
        Returns:
            Location if found
        """
        if not self._pyautogui_available:
            return {
                "success": False,
                "error": "pyautogui not available"
            }
        
        try:
            import pyautogui
            
            location = pyautogui.locateOnScreen(image_path)
            
            if location:
                return {
                    "success": True,
                    "found": True,
                    "location": (location.left, location.top, location.width, location.height),
                    "center": (location.left + location.width // 2, location.top + location.height // 2)
                }
            else:
                return {
                    "success": True,
                    "found": False
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
