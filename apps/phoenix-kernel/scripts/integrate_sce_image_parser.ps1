# integrate_sce_image_parser.ps1
# Safe implementation of SCE Image Parser for Phoenix + ComfyUI
# Creates backups before any modifications

param(
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Colors for output
$colors = @{
    Header = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Blue"
}

function Write-Header { Write-Host $args[0] -ForegroundColor $colors.Header }
function Write-Success { Write-Host $args[0] -ForegroundColor $colors.Success }
function Write-Warning { Write-Host $args[0] -ForegroundColor $colors.Warning }
function Write-Error { Write-Host $args[0] -ForegroundColor $colors.Error }
function Write-Info { Write-Host $args[0] -ForegroundColor $colors.Info }

# ============================================================================
# CONFIGURATION
# ============================================================================
$config = @{
    PhoenixKernelPath = "D:\Rezonic_Agentic\apps\phoenix-kernel\phoenix_65_workers.py"
    WorkersDir = "D:\Rezonic_Agentic\apps\phoenix-kernel\workers"
    ComfyUIWorkflowPath = "D:\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\ComfyUI\workflows"
    BackupDir = "D:\Rezonic_Agentic\backups\sce_integration_$timestamp"
}

# ============================================================================
# STEP 1: CREATE BACKUP DIRECTORY
# ============================================================================
Write-Header "`n" + "=" * 70
Write-Header "🧬 SCE IMAGE PARSER INTEGRATION"
Write-Header "=" * 70
Write-Info "`n📁 Creating backup directory: $($config.BackupDir)"

if (-not $DryRun) {
    New-Item -Path $config.BackupDir -ItemType Directory -Force | Out-Null
    Write-Success "   ✅ Backup directory created"
} else {
    Write-Warning "   [DRY RUN] Would create backup directory"
}

# ============================================================================
# STEP 2: BACKUP EXISTING FILES
# ============================================================================
Write-Header "`n📦 Backing up existing files..."

$filesToBackup = @(
    $config.PhoenixKernelPath,
    "$($config.WorkersDir)\comfyui_worker.py",
    "$($config.WorkersDir)\sce_image_parser.py"
)

foreach ($file in $filesToBackup) {
    if (Test-Path $file) {
        $backupFile = Join-Path $config.BackupDir (Split-Path $file -Leaf) + ".bak"
        if (-not $DryRun) {
            Copy-Item -Path $file -Destination $backupFile -Force
            Write-Success "   ✅ Backed up: $(Split-Path $file -Leaf) → $backupFile"
        } else {
            Write-Warning "   [DRY RUN] Would backup: $(Split-Path $file -Leaf)"
        }
    } else {
        Write-Warning "   ⚠️ File not found (will be created): $(Split-Path $file -Leaf)"
    }
}

# ============================================================================
# STEP 3: CREATE SCE IMAGE PARSER WORKER
# ============================================================================
Write-Header "`n🎨 Creating SCE Image Parser worker..."

$sceImageParserContent = @'
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
    
    # ========== CONVERTER: SCE → FLUX PROMPT ==========
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
        """Full pipeline: natural language → SCE → Flux prompt"""
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
'@

$sceImageParserPath = Join-Path $config.WorkersDir "sce_image_parser.py"

if (-not $DryRun) {
    $sceImageParserContent | Out-File -FilePath $sceImageParserPath -Encoding utf8
    Write-Success "   ✅ Created: $sceImageParserPath"
} else {
    Write-Warning "   [DRY RUN] Would create: $sceImageParserPath"
}

# ============================================================================
# STEP 4: UPDATE COMFYUI WORKER
# ============================================================================
Write-Header "`n🔄 Updating ComfyUI worker..."

$comfyuiWorkerPath = Join-Path $config.WorkersDir "comfyui_worker.py"

$comfyuiWorkerContent = @'
#!/usr/bin/env python3
"""
ComfyUI Worker with SCE Image Parser Integration
"""

import httpx
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any

# Import SCE Image Parser
try:
    from workers.sce_image_parser import sce_image_parser
    HAS_SCE_PARSER = True
except ImportError:
    HAS_SCE_PARSER = False
    logging.warning("SCE Image Parser not available")

logger = logging.getLogger("PHOENIX.COMFYUI")

class ComfyUIWorker:
    def __init__(self):
        self.name = "comfyui_generator"
        self.comfyui_url = "http://127.0.0.1:8188"
        self.comfyui_path = Path("D:/ComfyUI_windows_portable_nvidia/ComfyUI_windows_portable")
        self.workflow_path = self.comfyui_path / "ComfyUI" / "workflows" / "default_flux_workflow.json"
        logger.info("🎨 ComfyUI Worker initialized")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        prompt = kwargs.get("prompt", task.replace("/generate", "").strip())
        
        if not prompt:
            return {"error": "No prompt provided", "success": False}
        
        # Parse with SCE if available
        if HAS_SCE_PARSER:
            logger.info(f"📋 Parsing with SCE: {prompt[:50]}...")
            parsed = sce_image_parser.parse(prompt)
            flux_prompt = parsed["flux_prompt"]
            sce_data = parsed["sce"]
            logger.info(f"✅ SCE parsed: {parsed['drift_lock']}")
        else:
            flux_prompt = prompt
            sce_data = None
        
        logger.info(f"🎨 Generating: {flux_prompt[:100]}...")
        
        try:
            # Load workflow
            if not self.workflow_path.exists():
                return {"error": f"Workflow not found: {self.workflow_path}", "success": False}
            
            with open(self.workflow_path, 'r') as f:
                workflow = json.load(f)
            
            # Update prompt
            if "6" in workflow and "inputs" in workflow["6"]:
                workflow["6"]["inputs"]["text"] = flux_prompt
            
            # Add SCE metadata
            if sce_data:
                workflow["_sce_metadata"] = sce_data
            
            # Send to ComfyUI
            async with httpx.AsyncClient(timeout=120.0) as client:
                try:
                    await client.get(f"{self.comfyui_url}/system_stats")
                except:
                    return {"error": "ComfyUI not reachable", "success": False}
                
                response = await client.post(
                    f"{self.comfyui_url}/prompt",
                    json={"prompt": workflow}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "original_prompt": prompt,
                        "flux_prompt": flux_prompt,
                        "sce_parsed": sce_data is not None,
                        "prompt_id": data.get("prompt_id"),
                        "message": "Queued in ComfyUI"
                    }
                else:
                    return {"error": f"ComfyUI error: {response.status_code}", "success": False}
                    
        except Exception as e:
            logger.error(f"ComfyUI error: {e}")
            return {"error": str(e), "success": False}
'@

if (-not $DryRun) {
    $comfyuiWorkerContent | Out-File -FilePath $comfyuiWorkerPath -Encoding utf8
    Write-Success "   ✅ Updated: $comfyuiWorkerPath"
} else {
    Write-Warning "   [DRY RUN] Would update: $comfyuiWorkerPath"
}

# ============================================================================
# STEP 5: CREATE DEFAULT FLUX WORKFLOW
# ============================================================================
Write-Header "`n📁 Creating default Flux workflow..."

$workflowDir = $config.ComfyUIWorkflowPath
if (-not (Test-Path $workflowDir)) {
    if (-not $DryRun) {
        New-Item -Path $workflowDir -ItemType Directory -Force | Out-Null
        Write-Success "   ✅ Created workflow directory: $workflowDir"
    } else {
        Write-Warning "   [DRY RUN] Would create: $workflowDir"
    }
}

$fluxWorkflowContent = @'
{
  "6": {
    "inputs": {"text": "", "clip": ["30", 1]},
    "class_type": "CLIPTextEncode",
    "_meta": {"title": "Positive Prompt"}
  },
  "30": {
    "inputs": {"ckpt_name": "flux1-dev-fp8.safetensors"},
    "class_type": "CheckpointLoaderSimple",
    "_meta": {"title": "Load Flux"}
  },
  "27": {
    "inputs": {"width": 1024, "height": 1024, "batch_size": 1},
    "class_type": "EmptyLatentImage",
    "_meta": {"title": "Empty Latent"}
  },
  "35": {
    "inputs": {"guidance": 3.5, "conditioning": ["6", 0]},
    "class_type": "FluxGuidance",
    "_meta": {"title": "Flux Guidance"}
  },
  "33": {
    "inputs": {"text": "blurry, low quality, watermark, text", "clip": ["30", 1]},
    "class_type": "CLIPTextEncode",
    "_meta": {"title": "Negative Prompt"}
  },
  "31": {
    "inputs": {
      "seed": 42,
      "steps": 20,
      "cfg": 1,
      "sampler_name": "euler",
      "scheduler": "simple",
      "denoise": 1,
      "model": ["30", 0],
      "positive": ["35", 0],
      "negative": ["33", 0],
      "latent_image": ["27", 0]
    },
    "class_type": "KSampler",
    "_meta": {"title": "KSampler"}
  },
  "8": {
    "inputs": {"samples": ["31", 0], "vae": ["30", 2]},
    "class_type": "VAEDecode",
    "_meta": {"title": "VAE Decode"}
  },
  "9": {
    "inputs": {"filename_prefix": "phoenix_flux", "images": ["8", 0]},
    "class_type": "SaveImage",
    "_meta": {"title": "Save Image"}
  }
}
'@

$workflowFilePath = Join-Path $workflowDir "default_flux_workflow.json"

if (-not $DryRun) {
    $fluxWorkflowContent | Out-File -FilePath $workflowFilePath -Encoding utf8
    Write-Success "   ✅ Created: $workflowFilePath"
} else {
    Write-Warning "   [DRY RUN] Would create: $workflowFilePath"
}

# ============================================================================
# STEP 6: ADD SCE REFLEX COMMAND (Optional)
# ============================================================================
Write-Header "`n🔧 Adding SCE reflex command to Phoenix kernel..."

# This step requires parsing and modifying the kernel file - we'll do it safely
Write-Info "   Note: To add /sce command, manually add to ReflexCommands in kernel"

# ============================================================================
# SUMMARY
# ============================================================================
Write-Header "`n" + "=" * 70
Write-Header "✅ INTEGRATION COMPLETE!"
Write-Header "=" * 70

Write-Success @"

📋 WHAT WAS DONE:
   1. ✅ Created backup at: $($config.BackupDir)
   2. ✅ Created SCE Image Parser: $sceImageParserPath
   3. ✅ Updated ComfyUI Worker: $comfyuiWorkerPath
   4. ✅ Created Flux Workflow: $workflowFilePath

🚀 NEXT STEPS:
   1. Restart Phoenix:
      cd D:\Rezonic_Agentic\apps\phoenix-kernel
      python phoenix_65_workers.py

   2. Start ComfyUI:
      cd D:\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable
      python ComfyUI\main.py --windows-standalone-build

   3. Test in chat:
      /generate a beautiful glass bottle containing a galaxy, purple cosmic glow, cinematic lighting

📁 BACKUP LOCATION:
   $($config.BackupDir)

💡 TO RESTORE:
   Copy files from backup directory to original locations
"@

Write-Header "=" * 70