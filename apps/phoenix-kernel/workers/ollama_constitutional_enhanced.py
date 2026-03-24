# ollama_constitutional_enhanced.py - FIXED
from typing import Dict, Any, Optional, AsyncGenerator
import asyncio
import httpx
import json
import logging

logger = logging.getLogger("PHOENIX_ULTIMATE")

class OllamaConstitutionalWorker:
    """Enhanced Ollama worker with constitutional safeguards"""
    
    def __init__(self):
        self.name = "OllamaConstitutionalWorker"
        self.ollama_url = "http://localhost:11434"
        self.default_model = "llama3.2:latest"
        self.constitution = [
            "No harmful content",
            "No personal information",
            "Stay within bounds",
            "Be truthful",
            "Be helpful"
        ]
        self.interactions = []
        logger.info(f"✅ {self.name} initialized")
    
    async def execute(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Generate response with constitutional checks"""
        
        # Constitutional check
        constitutional_violations = []
        for law in self.constitution:
            if law == "No harmful content" and any(
                word in prompt.lower() for word in ['hack', 'exploit', 'malware']
            ):
                constitutional_violations.append(law)
        
        if constitutional_violations:
            return {
                "worker": self.name,
                "error": "Constitutional violation",
                "violations": constitutional_violations,
                "original_prompt": prompt[:100]
            }
        
        # Call Ollama
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model or self.default_model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = {
                        "response": data.get('response', ''),
                        "model": model or self.default_model,
                        "constitution_applied": True
                    }
                else:
                    result = {
                        "error": f"Ollama error: {response.status_code}",
                        "response": "Ollama service unavailable"
                    }
        except Exception as e:
            result = {
                "error": str(e),
                "response": "Failed to connect to Ollama"
            }
        
        interaction = {
            "timestamp": asyncio.get_event_loop().time(),
            "prompt": prompt[:100],
            "result": result
        }
        self.interactions.append(interaction)
        
        return {
            "worker": self.name,
            "result": result,
            "constitutional_check": "passed" if not constitutional_violations else "failed",
            "interaction_count": len(self.interactions)
        }
    
    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream response from Ollama"""
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.default_model,
                    "prompt": prompt,
                    "stream": True
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            yield data.get('response', '')
                        except:
                            continue
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "interactions": len(self.interactions),
            "model": self.default_model,
            "constitution": self.constitution,
            "ollama_url": self.ollama_url
        }
