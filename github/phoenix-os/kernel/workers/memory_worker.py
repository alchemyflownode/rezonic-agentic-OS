import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from base_worker import Worker

class MemoryWorker(Worker):
    def __init__(self, bus=None):
        super().__init__("memory_worker")
        self.bus = bus
        self.inbox = None
        self.history_file = Path("data/memory/hive_log.jsonl")

    async def initialize(self) -> None:
        if self.bus:
            self.inbox = await self.bus.subscribe("execution_ready")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        await super().initialize()

    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        return {"success": True}

    async def run_loop(self):
        while True:
            if not self.inbox: await asyncio.sleep(1); continue
            
            ruling = await self.inbox.get()
            actual_order = ruling.get("final_order", {})
            
            if not actual_order:
                continue
                
            actual_order["timestamp"] = datetime.now().isoformat()
            
            print(f"[MEMORY] Storing: {actual_order['asset']}")
            with open(self.history_file, "a") as f:
                f.write(json.dumps(actual_order) + "\n")
