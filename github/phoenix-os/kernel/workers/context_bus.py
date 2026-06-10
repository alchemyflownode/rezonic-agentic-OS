import asyncio
from typing import Dict, List, Any
from base_worker import Worker

class ContextBus(Worker):
    def __init__(self):
        super().__init__("context_bus")
        self.description = "Central nervous system"
        self._channels: Dict[str, List[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, channel: str) -> asyncio.Queue:
        async with self._lock:
            if channel not in self._channels:
                self._channels[channel] = []
            inbox = asyncio.Queue()
            self._channels[channel].append(inbox)
            return inbox

    async def publish(self, channel: str, message: Dict[str, Any]) -> int:
        if channel not in self._channels:
            return 0
        for inbox in self._channels[channel]:
            await inbox.put(message)
        return len(self._channels[channel])

    async def execute(self, task: str, **kwargs: Any) -> Dict[str, Any]:
        return {"success": True, "active_channels": list(self._channels.keys())}
