"""
Model Toggle System - Dynamic model selection for SCE workers
"""

import json
import subprocess
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import psutil

class ModelCategory(Enum):
    CODE = "code"
    REASONING = "reasoning"
    VISION = "vision"
    FAST = "fast"
    SPECIALIZED = "specialized"

@dataclass
class ModelConfig:
    name: str
    category: ModelCategory
    size_gb: float
    vram_required: float
    capabilities: List[str]
    default_worker: str
    description: str

class ModelToggle:
    """
    Dynamic model selector with VRAM awareness
    """
    
    def __init__(self):
        self.models = self._load_models()
        self.current_models = {
            'brain': 'qwen2.5-coder:14b',
            'vision': 'llama3.2-vision:11b',
            'reason': 'gemma2:9b',
            'fast': 'phi3.5:3.8b'
        }
        self.vram_total = self._get_vram_total()
        
    def _load_models(self) -> Dict[str, ModelConfig]:
        """Load model configurations"""
        return {
            # Code Models
            'qwen2.5-coder:14b': ModelConfig(
                name='qwen2.5-coder:14b',
                category=ModelCategory.CODE,
                size_gb=9.0,
                vram_required=10.0,
                capabilities=['code_gen', 'debug', 'architecture'],
                default_worker='brain',
                description='Best for BrainWorker - production code'
            ),
            'qwen2.5-coder:7b': ModelConfig(
                name='qwen2.5-coder:7b',
                category=ModelCategory.CODE,
                size_gb=4.7,
                vram_required=5.5,
                capabilities=['code_gen', 'debug'],
                default_worker='brain',
                description='Good balance for coding'
            ),
            
            # Reasoning Models
            'qwen:32b': ModelConfig(
                name='qwen:32b',
                category=ModelCategory.REASONING,
                size_gb=18.0,
                vram_required=20.0,
                capabilities=['deep_reasoning', 'analysis', 'planning'],
                default_worker='constitution',
                description='Best for ConstitutionalGovernor'
            ),
            'gemma2:9b': ModelConfig(
                name='gemma2:9b',
                category=ModelCategory.REASONING,
                size_gb=5.4,
                vram_required=6.5,
                capabilities=['reasoning', 'analysis'],
                default_worker='consensus',
                description='Excellent for ConsensusEngine'
            ),
            
            # Vision Models
            'llama3.2-vision:11b': ModelConfig(
                name='llama3.2-vision:11b',
                category=ModelCategory.VISION,
                size_gb=7.8,
                vram_required=8.5,
                capabilities=['vision', 'image_understanding'],
                default_worker='vision',
                description='Best for VisionWorker'
            ),
            'llava:7b': ModelConfig(
                name='llava:7b',
                category=ModelCategory.VISION,
                size_gb=4.7,
                vram_required=5.5,
                capabilities=['vision', 'image_qa'],
                default_worker='vision',
                description='Solid vision model'
            ),
            
            # Fast Models
            'phi3.5:3.8b': ModelConfig(
                name='phi3.5:3.8b',
                category=ModelCategory.FAST,
                size_gb=2.2,
                vram_required=3.0,
                capabilities=['fast', 'efficient'],
                default_worker='fast',
                description='Fast responses'
            ),
            'llama3.2:latest': ModelConfig(
                name='llama3.2:latest',
                category=ModelCategory.FAST,
                size_gb=2.0,
                vram_required=2.5,
                capabilities=['fast', 'chat'],
                default_worker='chat',
                description='Quick responses'
            ),
        }
    
    def _get_vram_total(self) -> float:
        """Get total available VRAM"""
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            return info.total / (1024**3)  # Convert to GB
        except:
            # Fallback to system RAM
            return psutil.virtual_memory().total / (1024**3)
    
    def get_compatible_models(self, category: Optional[ModelCategory] = None) -> List[ModelConfig]:
        """Get models that fit in VRAM"""
        compatible = []
        for model in self.models.values():
            if model.vram_required <= self.vram_total * 0.9:  # 90% threshold
                if category is None or model.category == category:
                    compatible.append(model)
        return compatible
    
    def set_model(self, worker: str, model_name: str) -> bool:
        """Set model for a specific worker"""
        if model_name not in self.models:
            return False
        
        model = self.models[model_name]
        if model.vram_required > self.vram_total * 0.9:
            return False
        
        self.current_models[worker] = model_name
        return True
    
    def get_model_for_worker(self, worker: str) -> str:
        """Get current model for worker"""
        return self.current_models.get(worker, 'llama3.2:latest')
    
    def get_stats(self) -> Dict[str, Any]:
        """Get model toggle statistics"""
        return {
            'vram_total': round(self.vram_total, 1),
            'vram_available': round(self.vram_total * 0.9, 1),
            'current_models': self.current_models,
            'compatible_count': len(self.get_compatible_models()),
            'total_models': len(self.models)
        }

# Singleton instance
model_toggle = ModelToggle()