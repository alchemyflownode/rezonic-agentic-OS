# AUTO-FIXED IMPORT PATH
import sys
from pathlib import Path
_workers_dir = Path(__file__).parent.resolve()
if str(_workers_dir) not in sys.path:
    sys.path.insert(0, str(_workers_dir))
# END AUTO-FIX
﻿# test_image_gen.py
import httpx
import asyncio
import json

async def test():
    print("=" * 50)
    print("🧪 TESTING IMAGE GENERATION")
    print("=" * 50)
    
    # Test 1: Generate image
    print("\n📡 Test 1: Generating image...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/kernel/stream",
            json={"task": "/generate a beautiful glass bottle with a galaxy inside"}
        )
        
        # Read streaming response
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    if data.get("type") == "reflex":
                        print(f"   Response: {data.get('content')[:100]}...")
                except:
                    pass
    
    # Wait a bit for generation
    print("\n⏳ Waiting 10 seconds for generation...")
    await asyncio.sleep(10)
    
    # Test 2: Get latest image
    print("\n📸 Test 2: Getting latest image...")
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8002/image/latest")
        if response.status_code == 200:
            print(f"   ✅ Image found! Size: {len(response.content)} bytes")
        else:
            print(f"   ❌ No image: {response.status_code}")
    
    # Test 3: List images
    print("\n📋 Test 3: Listing images...")
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8002/image/list")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {data.get('count', 0)} images")
            for img in data.get("images", [])[:3]:
                print(f"     - {img['filename']} ({img['size']} bytes)")
        else:
            print(f"   ❌ Failed: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(test())
