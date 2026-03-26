import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
"""
Voice Worker - Speech-to-text using OpenAI Whisper
"""

import asyncio
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
import tempfile
import os
import logging
import whisper
import time

logger = logging.getLogger(__name__)

class VoiceWorker:
    def __init__(self):
        self.name = "voice"
        self.description = "Speech-to-text using Whisper"
        self.model = None
        self.sample_rate = 16000
    
    def _load_model(self):
        if self.model is None:
            logger.info("?? Loading Whisper model...")
            self.model = whisper.load_model("base")
            logger.info("? Whisper model loaded")
    
    async def listen(self, duration: int = 5) -> str:
        self._load_model()
        logger.info(f"?? Listening for {duration} seconds...")
        
        recording = await asyncio.to_thread(
            sd.rec,
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32'
        )
        
        for i in range(duration):
            print(f"??  Listening... {duration-i}s remaining", end='\r')
            await asyncio.sleep(1)
        print(" " * 40, end='\r')
        
        await asyncio.to_thread(sd.wait)
        audio_int16 = (recording * 32767).astype(np.int16)
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_file = f.name
            await asyncio.to_thread(wav.write, temp_file, self.sample_rate, audio_int16)
        
        try:
            logger.info("?? Transcribing...")
            result = await asyncio.to_thread(
                self.model.transcribe,
                temp_file,
                language="en"
            )
            text = result["text"].strip()
            logger.info(f"? Transcribed: '{text}'")
            return text
        finally:
            os.unlink(temp_file)
    
    async def process(self, task: str, model: str = None) -> dict:
        task_lower = task.lower().strip()
        
        if task_lower == "listen" or task_lower == "start listening":
            text = await self.listen(duration=5)
            return {"content": f"?? **I heard:**\n\n> {text}"}
        
        elif task_lower.startswith("listen "):
            try:
                duration = int(task_lower.replace("listen", "").strip())
                duration = min(max(duration, 1), 30)
                text = await self.listen(duration=duration)
                return {"content": f"?? **I heard:**\n\n> {text}"}
            except:
                return {"content": "?? Please specify seconds: `listen 5`"}
        
        elif task_lower == "test mic" or task_lower == "test microphone":
            text = await self.listen(duration=2)
            return {"content": f"?? **Microphone test:**\n\n> {text}"}
        
        else:
            return {
                "content": """?? **Voice Worker Ready**

**Commands:**
â€¢ `listen` - Record 5 seconds
â€¢ `listen 10` - Record 10 seconds
â€¢ `test mic` - Quick 2-second test"""
            }


    async def process(self, task: str, memory_bus=None):
        """Process task â€“ auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}


