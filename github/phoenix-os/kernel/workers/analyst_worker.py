import asyncio
from typing import Dict, Any
from base_worker import Worker

class AnalystWorker(Worker):
    def __init__(self, bus=None):
        super().__init__("analyst_worker")
        self.bus = bus
        self.inbox = None

    async def initialize(self) -> None:
        if self.bus:
            self.inbox = await self.bus.subscribe("trade_signal")
        await super().initialize()

    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        return {"success": True, "message": "Listening..."}

    async def run_loop(self):
        while True:
            if not self.inbox: await asyncio.sleep(1); continue
            
            thought = await self.inbox.get()
            print(f"[ANALYST] Processing: {thought['asset']}")
            
            result = {"asset": thought['asset'], "signal": "BUY", "confidence": 0.9}
            
            if self.bus:
                await self.bus.publish("analysis_result", result)
