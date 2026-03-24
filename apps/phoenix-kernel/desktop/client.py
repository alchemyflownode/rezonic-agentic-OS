import httpx
import json
import logging

logger = logging.getLogger("PHOENIX.CLIENT")

class KernelClient:
    def __init__(self, base_url="http://127.0.0.1:8002", api_key="rez-hive-admin-key-2026"):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=120.0)
        self.headers = {"Content-Type": "application/json", "X-Hive-API-Key": api_key}

    async def check_health(self):
        try:
            r = await self.client.get(f"{self.base_url}/health", headers=self.headers)
            return r.status_code == 200
        except:
            return False

    async def send_task(self, task):
        async with self.client.stream("POST", f"{self.base_url}/kernel/stream", json={"task": task}, headers=self.headers) as resp:
            if resp.status_code != 200:
                return {"success": False, "error": f"HTTP {resp.status_code}"}
            full = []
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data.get("type") == "result":
                        full.append(data["content"])
                    elif data.get("type") == "error":
                        return {"success": False, "error": data["content"]}
            return {"success": True, "response": "".join(full)}

    async def close(self):
        await self.client.aclose()
