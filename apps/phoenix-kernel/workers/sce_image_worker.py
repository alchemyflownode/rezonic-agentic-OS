# workers/sce_image_worker.py
import httpx
import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("PHOENIX.SCE_IMAGE")

class SCEImageWorker:
    def __init__(self):
        self.name = "sce_image_generator"
        self.comfyui_url = "http://127.0.0.1:8188"
        self.ollama_url = "http://localhost:11434"
        self.workflow_path = Path("D:/ComfyUI_windows_portable_nvidia/ComfyUI_windows_portable/ComfyUI/workflows/dashboard_flux.json")
        logger.info("🎨 SCE Image Worker initialized")
    
    async def _parse_natural_to_sce(self, natural_prompt: str) -> Dict[str, Any]:
        """Parse natural language into SCE structure using Ollama"""
        
        system_prompt = f"""You are an SCE prompt parser. Convert natural language into this SCE structure:

{json.dumps(SCE_TEMPLATE, indent=2)}

Extract from: "{natural_prompt}"

Return ONLY valid JSON, no other text."""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": "qwen2.5-coder:7b-32k",
                        "prompt": natural_prompt,
                        "system": system_prompt,
                        "stream": False
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    return json.loads(result.get("response", "{}"))
        except Exception as e:
            logger.error(f"SCE parsing failed: {e}")
        
        # Fallback: basic SCE from natural language
        return {
            "sce": "SCE-V",
            "L2_VISUAL": {
                "anchors": {"primary_subject": natural_prompt[:50], "secondary_subject": ""},
                "style": {"visual_tone": [], "color_palette": []}
            }
        }
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        natural_prompt = kwargs.get("prompt", task.replace("/generate", "").strip())
        
        if not natural_prompt:
            return {"error": "No prompt provided", "success": False}
        
        # Step 1: Parse to SCE
        sce_data = await self._parse_natural_to_sce(natural_prompt)
        
        # Step 2: Convert SCE to Flux prompt
        flux_prompt = self._sce_to_flux_prompt(sce_data)
        negative_prompt = self._sce_to_negative_prompt(sce_data)
        
        # Step 3: Load and inject into workflow
        with open(self.workflow_path, 'r') as f:
            workflow = json.load(f)
        
        workflow["6"]["inputs"]["text"] = flux_prompt
        workflow["7"]["inputs"]["text"] = negative_prompt
        
        # Add SCE metadata
        workflow["_sce_metadata"] = sce_data
        
        # Step 4: Send to ComfyUI
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.comfyui_url}/prompt", json={"prompt": workflow})
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "original": natural_prompt,
                    "sce_parsed": sce_data,
                    "flux_prompt": flux_prompt,
                    "prompt_id": data.get("prompt_id"),
                    "message": "SCE-structured generation queued"
                }
        
        return {"error": "Generation failed", "success": False}