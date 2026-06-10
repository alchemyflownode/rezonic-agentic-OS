import asyncio
import json
import urllib.request
from typing import Dict, Any
from base_worker import Worker

class BrainWorker(Worker):
    def __init__(self, bus=None, model="llama3.2"):
        super().__init__("brain_worker")
        self.bus = bus
        self.model = model
        self.ollama_url = "http://localhost:11434/api/generate"

    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        system_prompt = (
            "You are an intent extraction engine. Extract the asset and action from the thought. "
            "Output ONLY valid JSON with keys: 'asset' (e.g. 'BTC', 'AAPL', 'NONE') and 'action' (e.g. 'ANALYZE', 'BUY', 'NONE')."
        )
        
        payload = json.dumps({
            "model": self.model,
            "prompt": f"{system_prompt}\n\nThought: {task}",
            "stream": False,
            "format": "json"
        }).encode('utf-8')

        loop = asyncio.get_running_loop()
        try:
            print(f"[BRAIN] Thinking about: '{task}'")
            response = await loop.run_in_executor(None, self._call_ollama, payload)
            structured_intent = json.loads(response)
            
            print(f"[BRAIN] SCE Output: {structured_intent}")
            
            if self.bus:
                await self.bus.publish("trade_signal", structured_intent)
                
            return {"success": True, "intent": structured_intent}
        except Exception as e:
            print(f"[BRAIN] Error: {e}")
            return {"success": False, "error": str(e)}

    def _call_ollama(self, payload):
        req = urllib.request.Request(self.ollama_url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get("response", "{}")
