import asyncio
from typing import Dict, Any
from base_worker import Worker

class ConstitutionalCouncilWorker(Worker):
    def __init__(self, bus=None):
        super().__init__("constitutional_council")
        self.bus = bus
        self.inbox = None

    async def initialize(self) -> None:
        if self.bus:
            self.inbox = await self.bus.subscribe("analysis_result")
        await super().initialize()

    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        return {"success": True, "message": "Guarding..."}

    async def run_loop(self):
        while True:
            if not self.inbox: await asyncio.sleep(1); continue
            
            signal = await self.inbox.get()
            print(f"[COUNCIL] Evaluating {signal['asset']} {signal['signal']}")
            
            approved = signal['asset'] != "DOGE" # Example rule
            
            ruling = {"approved": approved, "final_order": signal if approved else None}
            
            if self.bus and approved:
                await self.bus.publish("execution_ready", ruling)
            elif not approved:
                print(f"[COUNCIL] BLOCKED: {signal['asset']}")
