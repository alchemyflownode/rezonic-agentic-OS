#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCE Image Parser - Constitutional Image Generation for ComfyUI
Converts natural language to SCE-structured prompts for Flux
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger("PHOENIX.SCE_IMAGE")

class SCEImageParser:
    """P1-P3 Constitutional Image Parser - Converts natural language to SCE structure"""
    
    def __init__(self):

    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute worker task"""
        return {"success": True, "message": f"Worker {self.name} executed {task}"}
        self.version = "1.0.0"
        self.domain = "IMAGE_GENERATION"
        
        # Style keyword mappings
        self.style_keywords = {
            "visual_tone": {
                "beautiful": ["beautiful", "stunning", "gorgeous", "elegant"],
                "dreamlike": ["dreamlike", "ethereal", "surreal", "magical"],
                "cinematic": ["cinematic", "dramatic", "epic", "film"],
                "cyberpunk": ["cyberpunk", "neon", "futuristic", "dystopian"],
                "anime": ["anime", "manga", "sakuga", "japanese animation"],
                "realistic": ["realistic", "photorealistic", "hyperrealistic"]
            },
            "color_palette": {
                "purple": ["purple", "violet", "lavender", "amethyst"],
                "galaxy": ["galaxy", "cosmic", "nebula", "space"],
                "gold": ["gold", "golden", "amber", "honey"],
                "cyan": ["cyan", "teal", "aqua", "turquoise"],
                "neon_pink": ["neon pink", "magenta", "hot pink"],
                "electric_blue": ["electric blue", "cobalt", "sapphire"]
            },
            "material_focus": {
                "glass": ["glass", "crystal", "transparent", "refractive"],
                "metal": ["metal", "chrome", "steel", "titanium"],
                "light": ["light", "refraction", "glow", "luminescence"],
                "fabric": ["fabric", "cloth", "silk", "velvet"],
                "water": ["water", "liquid", "fluid", "flowing"]
            }
        }
        
        # Composition patterns
        self.composition_patterns = {
            "portrait": ["portrait", "face", "headshot", "bust"],
            "landscape": ["landscape", "scenery", "vista", "panorama"],
            "macro": ["macro", "close-up", "detail", "extreme close"],
            "wide": ["wide", "establishing", "aerial", "bird's eye"]
        }
        
        # Framing patterns
        self.framing_patterns = {
            "centered": ["centered", "center frame", "symmetrical"],
            "rule_of_thirds": ["rule of thirds", "off-center"],
            "low_angle": ["low angle", "worm's eye", "looking up"],
            "high_angle": ["high angle", "bird's eye", "overhead"]
        }
    
    # ========== P1: INTENT CAPTURE ==========
    def p1_capture_intent(self, prompt: str) -> Dict[str, str]:
        """Extract primary and secondary subjects"""
        patterns = {
            'primary': r'(?:a|an|the)\s+([\w\s]+?)(?:\s+(?:with|containing|inside|in|and)\s+|$)',
            'secondary': r'(?:with|containing|inside|in|and)\s+([\w\s]+?)(?:\s+(?:with|and|,)|$)'
        }
        
        primary_match = re.search(patterns['primary'], prompt, re.IGNORECASE)
        secondary_match = re.search(patterns['secondary'], prompt, re.IGNORECASE)
        
        return {
            "primary_subject": primary_match.group(1).strip() if primary_match else prompt.split()[:3],
            "secondary_subject": secondary_match.group(1).strip() if secondary_match else "",
            "intent": prompt[:100]
        }
    
    # ========== P2: DNA PROCESSING ==========
    def p2_extract_dna(self, prompt: str) -> Dict[str, Any]:
        """Extract style, colors, materials from prompt"""
        result = {
            "visual_tone": [],
            "color_palette": [],
            "material_focus": [],
            "composition": {"scene_type": "", "framing": "", "depth": ""}
        }
        
        prompt_lower = prompt.lower()
        
        # Detect visual tone
        for tone, keywords in self.style_keywords["visual_tone"].items():
            if any(kw in prompt_lower for kw in keywords):
                result["visual_tone"].append(tone)
        if not result["visual_tone"]:
            result["visual_tone"] = ["beautiful", "cinematic"]
        
        # Detect colors
        for color, keywords in self.style_keywords["color_palette"].items():
            if any(kw in prompt_lower for kw in keywords):
                result["color_palette"].append(color)
        if not result["color_palette"]:
            result["color_palette"] = ["purple", "galaxy"]
        
        # Detect materials
        for material, keywords in self.style_keywords["material_focus"].items():
            if any(kw in prompt_lower for kw in keywords):
                result["material_focus"].append(material)
        if not result["material_focus"]:
            result["material_focus"] = ["glass", "light"]
        
        # Detect composition
        for comp_type, keywords in self.composition_patterns.items():
            if any(kw in prompt_lower for kw in keywords):
                result["composition"]["scene_type"] = f"{comp_type} scene"
                break
        if not result["composition"]["scene_type"]:
            result["composition"]["scene_type"] = "surreal scene"
        
        # Detect framing
        for framing, keywords in self.framing_patterns.items():
            if any(kw in prompt_lower for kw in keywords):
                result["composition"]["framing"] = framing
                break
        if not result["composition"]["framing"]:
            result["composition"]["framing"] = "centered object"
        
        # Detect depth
        if any(kw in prompt_lower for kw in ["macro", "close-up", "detail"]):
            result["composition"]["depth"] = "macro foreground, shallow depth"
        elif any(kw in prompt_lower for kw in ["wide", "landscape", "panorama"]):
            result["composition"]["depth"] = "infinite depth, vast scale"
        else:
            result["composition"]["depth"] = "balanced depth"
        
        return result
    
    # ========== P3: EXECUTION BYTECODE ==========
    def p3_generate_bytecode(self, prompt: str) -> Dict[str, Any]:
        """Generate full SCE JSON structure"""
        intent = self.p1_capture_intent(prompt)
        dna = self.p2_extract_dna(prompt)
        
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
            },
            "composition": dna["composition"],
            "quality_flags": {
                "detail": "high",
                "lighting": "cinematic",
                "render_bias": "artstation-grade"
            },
            "negative": [
                "low resolution",
                "blurry",
                "text",
                "watermark",
                "distorted",
                "ugly",
                "deformed"
            ]
        }
    
    # ========== CONVERTER: SCE â†’ FLUX PROMPT ==========
    def sce_to_flux_prompt(self, sce: Dict[str, Any]) -> str:
        """Convert SCE structure to Flux prompt with weighting"""
        parts = []
        
        # Anchors with weighting
        primary = sce["anchors"]["primary_subject"]
        secondary = sce["anchors"]["secondary_subject"]
        parts.append(f"({primary}:1.2)")
        if secondary:
            parts.append(f"with ({secondary}:1.1)")
        
        # Style
        if sce["style"]["visual_tone"]:
            parts.append(", ".join(sce["style"]["visual_tone"]))
        
        # Colors
        if sce["style"]["color_palette"]:
            parts.append(f"with {' and '.join(sce['style']['color_palette'])} colors")
        
        # Materials
        if sce["style"]["material_focus"]:
            parts.append(f"featuring {' and '.join(sce['style']['material_focus'])}")
        
        # Composition
        parts.append(sce["composition"]["scene_type"])
        parts.append(sce["composition"]["depth"])
        
        # Quality
        parts.append(sce["quality_flags"]["lighting"])
        parts.append("masterpiece, best quality, highly detailed, 8k, photorealistic")
        
        return ", ".join(parts)
    
    # ========== MAIN ENTRY ==========
    def parse(self, natural_prompt: str) -> Dict[str, Any]:
        """Full pipeline: natural language â†’ SCE â†’ Flux prompt"""
        sce = self.p3_generate_bytecode(natural_prompt)
        flux_prompt = self.sce_to_flux_prompt(sce)
        
        return {
            "success": True,
            "original_prompt": natural_prompt,
            "sce": sce,
            "flux_prompt": flux_prompt,
            "drift_lock": sce.get("drift_lock", "")
        }

# Create instance
sce_image_parser = SCEImageParser()

