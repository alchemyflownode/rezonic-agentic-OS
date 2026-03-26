# AUTO-FIXED IMPORT PATH
import sys
from pathlib import Path
_workers_dir = Path(__file__).parent.resolve()
if str(_workers_dir) not in sys.path:
    sys.path.insert(0, str(_workers_dir))
# END AUTO-FIX
# test_comfyui_connection.py
import httpx
import asyncio
import json
from pathlib import Path

async def test():
    comfyui_url = "http://127.0.0.1:8188"
    workflow_path = Path("D:/ComfyUI_windows_portable_nvidia/ComfyUI_windows_portable/ComfyUI/workflows/cyberpunk_cat_workflow.json")
    
    # Check if ComfyUI is running
    async with httpx.AsyncClient() as client:
        try:
            health = await client.get(f"{comfyui_url}/system_stats")
            print(f"✅ ComfyUI running: {health.status_code}")
        except:
            print("❌ ComfyUI not running!")
            return
        
        # Load workflow
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)
        
        # Queue prompt
        response = await client.post(f"{comfyui_url}/prompt", json={"prompt": workflow})
        print(f"Queue response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Queued! Prompt ID: {data.get('prompt_id')}")
        else:
            print(f"❌ Error: {response.text}")

asyncio.run(test())