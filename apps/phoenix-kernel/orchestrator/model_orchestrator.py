"""
Model Orchestrator Service - Routes tasks to appropriate Ollama models
Based on the RezHive Sovereign AI Coworker architecture
Uses Ollama exclusively - no Gemini dependency
"""

import os
import asyncio
import json
from typing import Dict, Any, Optional, Literal
from enum import Enum
from dataclasses import dataclass, field
import httpx

class TaskType(str, Enum):
    STRATEGIC = "strategic"      # CEO role - high-level reasoning
    CODE = "code"                 # Coder role - code generation
    VISION = "vision"             # Visionary role - image analysis (via llava)
    ANALYSIS = "analysis"         # Analyst role - data insights
    EXECUTION = "execution"       # Executor role - system interaction

@dataclass
class Task:
    type: TaskType
    prompt: str
    context: Optional[str] = None
    image: Optional[str] = None  # Base64 encoded image for vision tasks
    model_override: Optional[str] = None

class ModelOrchestrator:
    """
    Sovereign AI Coworker Orchestrator
    Routes tasks to appropriate Ollama models based on task type
    """
    
    # Ollama model configurations
    MODELS = {
        # Strategic/CEO models (larger models for complex reasoning)
        "ceo": "llama3.2:latest",      # 3B/70B - good for reasoning
        "ceo_alternative": "mistral:latest",
        
        # Code models
        "code": "codellama:latest",     # CodeLlama for code generation
        "code_alternative": "llama3.2:latest",
        
        # Vision models (requires llava or bakllava)
        "vision": "llava:latest",        # LLaVA for vision tasks
        "vision_alternative": "bakllava:latest",
        
        # Worker models (fast, efficient)
        "worker": "llama3.2:latest",     # 3B model for quick tasks
        "worker_alternative": "phi3:latest",
        
        # Analysis models
        "analysis": "llama3.2:latest",
        
        # Execution models
        "execution": "llama3.2:latest",
    }
    
    # System instructions for different roles
    SYSTEM_INSTRUCTIONS = {
        TaskType.STRATEGIC: """You are the CEO of the REZ HIVE Sovereign AI Coworker ensemble.
Focus on high-level architecture, strategy, and complex reasoning.
Provide thoughtful, strategic responses with clear reasoning.
Be authoritative, precise, and transparent in your analysis.""",
        
        TaskType.CODE: """You are the Coder of the REZ HIVE Sovereign AI Coworker ensemble.
Focus on precise, efficient, and secure code generation.
Output code with proper formatting, comments, and explanations.
Use best practices and consider edge cases.""",
        
        TaskType.VISION: """You are the Visionary of the REZ HIVE Sovereign AI Coworker ensemble.
Focus on detailed visual analysis and UI/UX understanding.
Analyze images thoroughly and provide actionable insights.
Describe what you see with precision and clarity.""",
        
        TaskType.ANALYSIS: """You are the Analyst of the REZ HIVE Sovereign AI Coworker ensemble.
Focus on pattern recognition and data insights.
Provide data-driven analysis with clear conclusions.
Identify trends, anomalies, and opportunities.""",
        
        TaskType.EXECUTION: """You are the Executor of the REZ HIVE Sovereign AI Coworker ensemble.
Focus on tool use and system interaction.
Provide actionable, executable instructions.
Be precise and consider system constraints."""
    }
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.client = httpx.AsyncClient(timeout=120.0)  # Longer timeout for models
        self._available_models = None
        print(f"✅ Model Orchestrator initialized (Ollama: {ollama_url})")
    
    async def initialize(self):
        """Check available models on startup"""
        try:
            response = await self.client.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                self._available_models = [m["name"] for m in models]
                print(f"📦 Available Ollama models: {len(self._available_models)}")
                
                # Log which models are available for each role
                for role, model in self.MODELS.items():
                    if model in self._available_models:
                        print(f"  ✅ {role}: {model} available")
                    else:
                        alt = self.MODELS.get(f"{role}_alternative")
                        if alt and alt in self._available_models:
                            print(f"  ⚠️ {role}: using {alt} (fallback)")
                        else:
                            print(f"  ❌ {role}: {model} not available")
        except Exception as e:
            print(f"⚠️ Could not connect to Ollama: {e}")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def route_task(self, task: Task) -> Dict[str, Any]:
        """
        Route a task to the appropriate model based on type
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            if task.type == TaskType.VISION and task.image:
                result = await self._execute_vision_task(task)
            else:
                result = await self._execute_text_task(task)
            
            duration = asyncio.get_event_loop().time() - start_time
            
            return {
                "status": "success",
                "result": result,
                "task_type": task.type.value,
                "duration": duration,
                "model_used": self._get_model_for_task(task)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "task_type": task.type.value
            }
    
    def _get_model_for_task(self, task: Task) -> str:
        """Determine which model to use for a task"""
        if task.model_override:
            return task.model_override
        
        # Map task type to model key
        model_key = {
            TaskType.STRATEGIC: "ceo",
            TaskType.ANALYSIS: "analysis",
            TaskType.CODE: "code",
            TaskType.VISION: "vision",
            TaskType.EXECUTION: "execution"
        }.get(task.type, "worker")
        
        model = self.MODELS.get(model_key, self.MODELS["worker"])
        
        # Check if model is available, fallback if needed
        if self._available_models and model not in self._available_models:
            fallback_key = f"{model_key}_alternative"
            fallback = self.MODELS.get(fallback_key)
            if fallback and fallback in self._available_models:
                return fallback
            # Try default worker model
            if self.MODELS["worker"] in self._available_models:
                return self.MODELS["worker"]
        
        return model
    
    def _get_system_instruction(self, task_type: TaskType) -> str:
        """Get system instruction for task type"""
        return self.SYSTEM_INSTRUCTIONS.get(task_type, "")
    
    def _build_prompt(self, task: Task) -> str:
        """Build the full prompt with context"""
        if task.context:
            return f"""Context:
{task.context}

Task: {task.prompt}

Respond with your analysis and solution."""
        return task.prompt
    
    async def _execute_text_task(self, task: Task) -> str:
        """Execute a text-based task via Ollama"""
        prompt = self._build_prompt(task)
        system_instruction = self._get_system_instruction(task.type)
        model_name = self._get_model_for_task(task)
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "system": system_instruction,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 2048
            }
        }
        
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama error: {response.status_code}")
            
            data = response.json()
            return data.get("response", "")
            
        except httpx.TimeoutException:
            raise Exception(f"Timeout: {model_name} took too long to respond")
        except Exception as e:
            raise Exception(f"Ollama execution failed: {e}")
    
    async def _execute_vision_task(self, task: Task) -> str:
        """Execute a vision task via Ollama with LLaVA or BakLLaVA"""
        if not task.image:
            return "No image provided for vision task"
        
        model_name = self._get_model_for_task(task)
        
        # LLaVA expects image in base64 format with special formatting
        # Remove data:image/jpeg;base64, prefix if present
        image_data = task.image
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]
        
        payload = {
            "model": model_name,
            "prompt": task.prompt,
            "images": [image_data],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama vision error: {response.status_code}")
            
            data = response.json()
            return data.get("response", "")
            
        except Exception as e:
            # Fallback to text-only if vision model fails
            return f"[Vision model unavailable: {e}]\n\nProcessing text analysis of your request:\n{task.prompt}"
    
    async def get_available_models(self) -> list:
        """Get list of available models from Ollama"""
        if self._available_models is None:
            await self.initialize()
        return self._available_models or []
    
    async def check_health(self) -> Dict[str, Any]:
        """Check if Ollama is healthy"""
        try:
            response = await self.client.get(f"{self.ollama_url}/api/tags", timeout=5.0)
            models = response.json().get("models", []) if response.status_code == 200 else []
            
            return {
                "connected": response.status_code == 200,
                "models_available": len(models),
                "models": [m["name"] for m in models],
                "orchestrator_ready": True
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "orchestrator_ready": False
            }


# Singleton instance for global use
_model_orchestrator = None

async def get_model_orchestrator() -> ModelOrchestrator:
    """Get or create the global model orchestrator instance"""
    global _model_orchestrator
    if _model_orchestrator is None:
        _model_orchestrator = ModelOrchestrator()
        await _model_orchestrator.initialize()
    return _model_orchestrator