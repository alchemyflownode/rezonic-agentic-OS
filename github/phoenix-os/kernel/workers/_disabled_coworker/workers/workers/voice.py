"""
Voice Worker for Phoenix Coworker

Handles text-to-speech and speech-to-text.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from .base import BaseWorker


class VoiceWorker(BaseWorker):
    """
    Voice worker for audio interactions.
    
    Provides:
    - Text-to-speech (TTS)
    - Speech-to-text (STT) / Voice recognition
    """
    
    def __init__(self, kernel: Any):
        super().__init__(kernel, "voice")
        
        # Try to import optional dependencies
        try:
            import pyttsx3
            self._tts_available = True
            self._tts_engine = None
        except ImportError:
            self._tts_available = False
            self._tts_engine = None
        
        try:
            import speech_recognition as sr
            self._stt_available = True
            self._recognizer = sr.Recognizer()
        except ImportError:
            self._stt_available = False
            self._recognizer = None
    
    def _init_tts(self):
        """Initialize TTS engine"""
        if self._tts_available and self._tts_engine is None:
            try:
                import pyttsx3
                self._tts_engine = pyttsx3.init()
                # Configure voice properties
                self._tts_engine.setProperty('rate', 150)  # Speed
                self._tts_engine.setProperty('volume', 0.9)  # Volume
            except Exception as e:
                print(f"Could not initialize TTS: {e}")
                self._tts_available = False
    
    async def run(self):
        """Voice worker doesn't need a continuous loop"""
        while self._running:
            await asyncio.sleep(1)
    
    async def process(self, command: str, context: Dict = None) -> Dict:
        """Process a voice command"""
        context = context or {}
        
        words = command.lower().split()
        if not words:
            return {"success": False, "error": "Empty command"}
        
        action = words[0]
        
        if action in ["speak", "say", "tts"]:
            text = context.get("text") or " ".join(words[1:])
            return await self.speak(text)
        
        elif action in ["listen", "hear", "stt"]:
            return await self.listen()
        
        return {"success": False, "error": f"Unknown voice action: {action}"}
    
    async def speak(self, text: str) -> Dict:
        """
        Convert text to speech.
        
        Args:
            text: Text to speak
        
        Returns:
            TTS result
        """
        if not self._tts_available:
            return {
                "success": False,
                "error": "TTS not available. Install with: pip install pyttsx3"
            }
        
        try:
            self._init_tts()
            
            if self._tts_engine:
                self._tts_engine.say(text)
                self._tts_engine.runAndWait()
                
                return {
                    "success": True,
                    "text": text,
                    "spoken": True
                }
            else:
                return {
                    "success": False,
                    "error": "TTS engine not initialized"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def listen(self, duration: int = 5) -> Dict:
        """
        Listen for voice input and convert to text.
        
        Args:
            duration: Maximum listening duration in seconds
        
        Returns:
            STT result with transcribed text
        """
        if not self._stt_available:
            return {
                "success": False,
                "error": "STT not available. Install with: pip install SpeechRecognition"
            }
        
        try:
            import speech_recognition as sr
            
            with sr.Microphone() as source:
                print(f"Listening for {duration} seconds...")
                
                # Adjust for ambient noise
                self._recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Listen
                audio = self._recognizer.listen(source, timeout=duration)
                
                print("Processing speech...")
                
                # Try to recognize
                try:
                    text = self._recognizer.recognize_google(audio)
                    return {
                        "success": True,
                        "text": text,
                        "confidence": "high"
                    }
                except sr.UnknownValueError:
                    return {
                        "success": False,
                        "error": "Could not understand audio"
                    }
                except sr.RequestError as e:
                    return {
                        "success": False,
                        "error": f"STT service error: {e}"
                    }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def transcribe_file(self, audio_path: str) -> Dict:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Transcription result
        """
        if not self._stt_available:
            return {
                "success": False,
                "error": "STT not available"
            }
        
        try:
            import speech_recognition as sr
            
            path = Path(audio_path).expanduser()
            
            if not path.exists():
                return {"success": False, "error": f"File not found: {audio_path}"}
            
            with sr.AudioFile(str(path)) as source:
                audio = self._recognizer.record(source)
                
                try:
                    text = self._recognizer.recognize_google(audio)
                    return {
                        "success": True,
                        "text": text,
                        "source": str(path)
                    }
                except sr.UnknownValueError:
                    return {
                        "success": False,
                        "error": "Could not understand audio"
                    }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
