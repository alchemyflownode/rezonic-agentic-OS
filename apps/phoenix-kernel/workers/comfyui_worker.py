# workers/comfyui_worker.py - FIXED JSON FORMAT
import httpx
import json
import logging
import re
import random
from typing import Dict, Any

logger = logging.getLogger("PHOENIX.COMFYUI")

class ComfyUIWorker:
    def __init__(self):
        self.name = "comfyui_generator"
        self.comfyui_url = "http://127.0.0.1:8188"
        logger.info("🎨 ComfyUI Worker initialized")

    # ========== P1: INTENT CAPTURE ==========
    def _p1_capture_intent(self, prompt: str) -> Dict[str, str]:
        patterns = {
            'primary': r'(?:a|an|the)\s+([\w\s]+?)(?:\s+(?:with|containing|inside|in|and)\s+|$)',
            'secondary': r'(?:with|containing|inside|in|and)\s+([\w\s]+?)(?:\s+(?:with|and|,)|$)'
        }
        primary_match = re.search(patterns['primary'], prompt, re.IGNORECASE)
        secondary_match = re.search(patterns['secondary'], prompt, re.IGNORECASE)
        
        return {
            "primary_subject": primary_match.group(1).strip() if primary_match else prompt[:50],
            "secondary_subject": secondary_match.group(1).strip() if secondary_match else "",
            "intent": prompt[:100]
        }

    # ========== P2: DNA PROCESSING ==========
    def _p2_extract_dna(self, prompt: str) -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        
        style_map = {
            "beautiful": ["beautiful", "stunning", "gorgeous"],
            "cinematic": ["cinematic", "dramatic", "epic"],
            "dreamlike": ["dreamlike", "ethereal", "surreal"],
            "cyberpunk": ["cyberpunk", "neon", "futuristic"]
        }
        
        color_map = {
            "purple": ["purple", "violet", "lavender"],
            "galaxy": ["galaxy", "cosmic", "nebula"],
            "gold": ["gold", "golden", "amber"],
            "cyan": ["cyan", "teal", "aqua"]
        }
        
        material_map = {
            "glass": ["glass", "crystal", "transparent"],
            "metal": ["metal", "chrome", "steel"],
            "light": ["light", "glow", "refraction"]
        }
        
        visual_tone = []
        for tone, keywords in style_map.items():
            if any(kw in prompt_lower for kw in keywords):
                visual_tone.append(tone)
        if not visual_tone:
            visual_tone = ["beautiful", "cinematic"]
        
        color_palette = []
        for color, keywords in color_map.items():
            if any(kw in prompt_lower for kw in keywords):
                color_palette.append(color)
        if not color_palette:
            color_palette = ["purple", "galaxy"]
        
        material_focus = []
        for material, keywords in material_map.items():
            if any(kw in prompt_lower for kw in keywords):
                material_focus.append(material)
        if not material_focus:
            material_focus = ["glass", "light"]
        
        return {
            "visual_tone": visual_tone,
            "color_palette": color_palette,
            "material_focus": material_focus
        }

    # ========== P3: SCE JSON GENERATION ==========
    def _p3_generate_sce(self, prompt: str) -> Dict[str, Any]:
        intent = self._p1_capture_intent(prompt)
        dna = self._p2_extract_dna(prompt)
        
        return {
            "sce": "SCE-V",
            "version": "1.0.0",
            "domain": "IMAGE_GENERATION",
            "mode": "COMPRESSED",
            "intent": intent["intent"],
            "anchors": {
                "primary_subject": intent["primary_subject"],
                "secondary_subject": intent["secondary_subject"]
            },
            "style": {
                "visual_tone": dna["visual_tone"],
                "color_palette": dna["color_palette"],
                "material_focus": dna["material_focus"]
            }
        }

    # ========== SCE → FLUX PROMPT ==========
    def _sce_to_flux_prompt(self, sce: Dict[str, Any]) -> str:
        parts = []
        
        primary = sce["anchors"]["primary_subject"]
        secondary = sce["anchors"]["secondary_subject"]
        parts.append(f"({primary}:1.2)")
        if secondary:
            parts.append(f"with ({secondary}:1.1)")
        
        if sce["style"]["visual_tone"]:
            parts.append(", ".join(sce["style"]["visual_tone"]))
        
        if sce["style"]["color_palette"]:
            parts.append(f"with {' and '.join(sce['style']['color_palette'])} colors")
        
        if sce["style"]["material_focus"]:
            parts.append(f"featuring {' and '.join(sce['style']['material_focus'])}")
        
        parts.append("masterpiece, best quality, highly detailed, 8k")
        
        return ", ".join(parts)

    # ========== BUILD COMFYUI WORKFLOW (RETURNS DICT, NOT JSON STRING) ==========
    def _build_workflow(self, flux_prompt: str) -> Dict[str, Any]:
        """Build workflow as Python dict - will be JSON serialized by httpx"""
        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "flux1-dev-fp8.safetensors"}
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": flux_prompt, "clip": ["1", 1]}
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "blurry, low quality, watermark, text", "clip": ["1", 1]}
            },
            "4": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 768, "height": 1024, "batch_size": 1}
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": random.randint(1, 999999999),
                    "steps": 20,
                    "cfg": 7.5,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0]
                }
            },
            "6": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["5", 0], "vae": ["1", 2]}
            },
            "7": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "phoenix_flux", "images": ["6", 0]}
            }
        }

    # ========== MAIN EXECUTION ==========
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        natural_prompt = kwargs.get("prompt", task.replace("/generate", "").strip())
        
        if not natural_prompt:
            return {"error": "No prompt provided", "success": False}
        
        logger.info(f"📝 Processing: {natural_prompt[:100]}...")
        
        # Step 1: SCE Parsing
        sce_data = self._p3_generate_sce(natural_prompt)
        logger.info(f"✅ SCE Parsed: {sce_data['intent'][:50]}...")
        
        # Step 2: Convert to Flux Prompt
        flux_prompt = self._sce_to_flux_prompt(sce_data)
        logger.info(f"🎨 Flux Prompt: {flux_prompt[:100]}...")
        
        # Step 3: Build workflow
        workflow = self._build_workflow(flux_prompt)
        
        # Step 4: Send to ComfyUI - httpx will automatically convert dict to JSON
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Check ComfyUI
                try:
                    health = await client.get(f"{self.comfyui_url}/system_stats", timeout=5.0)
                    logger.info(f"✅ ComfyUI connected")
                except Exception as e:
                    return {"error": f"ComfyUI not reachable: {e}", "success": False}
                
                # Queue prompt - httpx serializes the dict to JSON automatically
                response = await client.post(
                    f"{self.comfyui_url}/prompt",
                    json=workflow  # This sends proper JSON with double quotes
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Prompt queued! ID: {data.get('prompt_id')}")
                    return {
                        "success": True,
                        "original": natural_prompt,
                        "flux_prompt": flux_prompt,
                        "prompt_id": data.get("prompt_id"),
                        "message": f"Queued in ComfyUI - ID: {data.get('prompt_id')}"
                    }
                else:
                    logger.error(f"ComfyUI error: {response.status_code} - {response.text}")
                    return {"error": f"ComfyUI error: {response.status_code}", "success": False}
                    
        except Exception as e:
            logger.error(f"ComfyUI error: {e}")
            return {"error": str(e), "success": False}