#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from desktop.client import KernelClient
from desktop.presence import DesktopPresence
from desktop.watcher import PhoenixFileHandler
import logging
logging.basicConfig(level=logging.INFO)

async def main():
    client = KernelClient()  # uses localhost:8002 and rez-hive-admin-key-2026
    if not await client.check_health():
        print("❌ Kernel not running. Start it first: python zyphoenix5.py")
        return
    loop = asyncio.get_running_loop()
    presence = DesktopPresence(client, loop)
    presence.run()
    watcher = PhoenixFileHandler(client)
    observer = watcher.start()
    print("✅ Phoenix Desktop Coworker running. Press Ctrl+C to stop.")
    await asyncio.Event().wait()  # run forever
asyncio.run(main())