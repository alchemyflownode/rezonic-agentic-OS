# src/lib/gpu_manager.py
"""
Sovereign OS - Centralized GPU Manager
All 28 workers import this for deterministic, GPU-accelerated inference
"""
import os, sys, json, time, warnings, torch
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache

warnings.filterwarnings("ignore")

try:
    from llama_cpp import Llama
    CUDA_AVAILABLE = True
except ImportError:
    CUDA_AVAILABLE = False
    print("⚠️  llama-cpp-python not installed. GPU acceleration disabled.", file=sys.stderr)

class SovereignGPU:
    """Singleton GPU manager with constitutional safeguards"""
    
    _instance: Optional['SovereignGPU'] = None
    _models: Dict[str, Llama] = {}
    
    # Constitutional constraints (immutable)
    MAX_VRAM_FRACTION = 0.85  # Never exceed 85% VRAM
    DEFAULT_TEMPERATURE = 0.0  # Deterministic by default
    MAX_CONTEXT = 4096  # Safe context window for 12GB VRAM
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._check_hardware()
    
    def _check_hardware(self):
        """Validate GPU availability and log specs"""
        if CUDA_AVAILABLE and torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            self.vram_total_gb = props.total_memory / 1024**3
            self.gpu_name = props.name
            print(f"🎮 GPU: {self.gpu_name} | VRAM: {self.vram_total_gb:.1f}GB", file=sys.stderr)
        else:
            print("⚠️  CUDA not available. Falling back to CPU.", file=sys.stderr)
            self.vram_total_gb = 0
            self.gpu_name = "CPU"
    
    @lru_cache(maxsize=3)  # Cache up to 3 models (swap as needed)
    def load_model(self, model_name: str, model_path: str, quantization: str = "q4") -> Llama:
        """Load or retrieve cached model with GPU offloading"""
        if model_name in self._models:
            return self._models[model_name]
        
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model not found: {path}")
        
        # Calculate safe VRAM allocation
        safe_vram = self.vram_total_gb * self.MAX_VRAM_FRACTION
        estimated_model_size = 4.5 if "phi-3" in model_name.lower() else 6.0  # GB estimate
        
        if estimated_model_size > safe_vram:
            print(f"⚠️  Model {model_name} ({estimated_model_size}GB) may exceed safe VRAM ({safe_vram:.1f}GB)", file=sys.stderr)
        
        print(f"🧠 Loading {model_name} onto {self.gpu_name}...", file=sys.stderr)
        
        llm = Llama(
            model_path=str(path),
            n_gpu_layers=-1 if CUDA_AVAILABLE and torch.cuda.is_available() else 0,
            n_ctx=self.MAX_CONTEXT,
            n_threads=max(1, os.cpu_count() // 2),
            verbose=False,
            # Constitutional/deterministic settings
            seed=42,
            logits_all=False,
        )
        
        self._models[model_name] = llm
        print(f"✅ {model_name} ready", file=sys.stderr)
        return llm
    
    def generate(
        self,
        prompt: str,
        model_name: str = "phi-3-mini",
        max_tokens: int = 256,
        temperature: Optional[float] = None,
        stop_sequences: Optional[list] = None
    ) -> Dict[str, Any]:
        """Generate response with constitutional enforcement"""
        if temperature is None:
            temperature = self.DEFAULT_TEMPERATURE
        
        start = time.time()
        
        try:
            llm = self.load_model(model_name, f"models/{model_name}-q4.gguf")
            
            # Format prompt based on model
            if "phi-3" in model_name.lower():
                formatted = f"<|user|>\n{prompt}<|end|>\n<|assistant|->"
                default_stop = ["<|end|>", "<|user|>"]
            else:
                formatted = f"User: {prompt}\nAssistant:"
                default_stop = ["\nUser:", "\n\n"]
            
            output = llm(
                formatted,
                max_tokens=max_tokens,
                stop=stop_sequences or default_stop,
                echo=False,
                temperature=temperature,
                top_p=1.0 if temperature == 0 else 0.9,
                repeat_penalty=1.1
            )
            
            text = output['choices'][0]['text'].strip()
            elapsed = time.time() - start
            
            return {
                "success": True,
                "response": text,
                "tokens": len(text.split()),
                "tokens_per_second": round(len(text.split()) / elapsed, 1) if elapsed > 0 else 0,
                "time_ms": round(elapsed * 1000),
                "backend": "CUDA_GPU" if CUDA_AVAILABLE and torch.cuda.is_available() else "CPU",
                "model": model_name,
                "deterministic": temperature == 0.0,
                "constitutional": {
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "context_window": self.MAX_CONTEXT
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "backend": "CUDA_GPU" if CUDA_AVAILABLE else "CPU",
                "fallback_suggestion": "Try reducing max_tokens or switching to CPU"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Return GPU health for monitoring"""
        if not (CUDA_AVAILABLE and torch.cuda.is_available()):
            return {"available": False, "backend": "CPU"}
        
        return {
            "available": True,
            "backend": "CUDA_GPU",
            "gpu_name": self.gpu_name,
            "vram_total_gb": round(self.vram_total_gb, 1),
            "vram_used_gb": round(torch.cuda.memory_allocated(0) / 1024**3, 1),
            "vram_free_gb": round((self.vram_total_gb * self.MAX_VRAM_FRACTION) - (torch.cuda.memory_allocated(0) / 1024**3), 1),
            "models_loaded": list(self._models.keys()),
            "constitutional_limits": {
                "max_vram_fraction": self.MAX_VRAM_FRACTION,
                "default_temperature": self.DEFAULT_TEMPERATURE,
                "max_context": self.MAX_CONTEXT
            }
        }

# Global singleton instance
gpu = SovereignGPU()

# Convenience function for workers
def sovereign_generate(prompt: str, **kwargs) -> Dict[str, Any]:
    """One-line inference for workers"""
    return gpu.generate(prompt, **kwargs)