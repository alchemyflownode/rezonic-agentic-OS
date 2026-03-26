"""
Smart Model Router - AI-powered model selection with loading states
"""

import asyncio
import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import random
import psutil

class TaskType(Enum):
    CODE = "code"
    REASONING = "reasoning"
    VISION = "vision"
    CHAT = "chat"
    ANALYSIS = "analysis"
    CONSTITUTIONAL = "constitutional"
    STRATEGY = "strategy"
    UNKNOWN = "unknown"

@dataclass
class ModelCapability:
    """Model capabilities and performance metrics"""
    name: str
    task_types: List[TaskType]
    size_gb: float
    speed_score: float  # 1-10, higher is faster
    quality_score: float  # 1-10, higher is better
    vram_required: float
    load_time_ms: float
    success_rate: float = 1.0
    avg_response_time_ms: float = 0
    usage_count: int = 0
    
@dataclass
class LoadingState:
    """Loading animation state"""
    stage: str
    message: str
    progress: float
    estimated_time_ms: int
    model_name: str

class SmartRouter:
    """
    AI-powered router that intelligently selects models based on task analysis
    """
    
    def __init__(self):
        self.models = self._initialize_models()
        self.routing_history: List[Dict] = []
        self.current_load_state: Optional[LoadingState] = None
        self.loading_callbacks = []
        
        # Performance tracking
        self.model_stats = {name: {
            'uses': 0,
            'total_time': 0,
            'successes': 0,
            'failures': 0
        } for name in self.models}
        
    def _initialize_models(self) -> Dict[str, ModelCapability]:
        """Initialize model capabilities"""
        return {
            # CODE MODELS
            'qwen2.5-coder:14b': ModelCapability(
                name='qwen2.5-coder:14b',
                task_types=[TaskType.CODE, TaskType.ANALYSIS],
                size_gb=9.0,
                speed_score=6,
                quality_score=9,
                vram_required=10.0,
                load_time_ms=2500
            ),
            'qwen2.5-coder:7b': ModelCapability(
                name='qwen2.5-coder:7b',
                task_types=[TaskType.CODE],
                size_gb=4.7,
                speed_score=8,
                quality_score=7,
                vram_required=5.5,
                load_time_ms=1500
            ),
            'deepseek-coder:latest': ModelCapability(
                name='deepseek-coder:latest',
                task_types=[TaskType.CODE],
                size_gb=0.776,
                speed_score=9,
                quality_score=6,
                vram_required=1.0,
                load_time_ms=500
            ),
            
            # REASONING MODELS
            'qwen:32b': ModelCapability(
                name='qwen:32b',
                task_types=[TaskType.REASONING, TaskType.ANALYSIS, TaskType.STRATEGY],
                size_gb=18.0,
                speed_score=4,
                quality_score=10,
                vram_required=20.0,
                load_time_ms=4000
            ),
            'gemma2:9b': ModelCapability(
                name='gemma2:9b',
                task_types=[TaskType.REASONING, TaskType.ANALYSIS],
                size_gb=5.4,
                speed_score=7,
                quality_score=8,
                vram_required=6.5,
                load_time_ms=2000
            ),
            'phi3.5:3.8b': ModelCapability(
                name='phi3.5:3.8b',
                task_types=[TaskType.REASONING, TaskType.CHAT],
                size_gb=2.2,
                speed_score=9,
                quality_score=7,
                vram_required=3.0,
                load_time_ms=800
            ),
            
            # VISION MODELS
            'llama3.2-vision:11b': ModelCapability(
                name='llama3.2-vision:11b',
                task_types=[TaskType.VISION],
                size_gb=7.8,
                speed_score=5,
                quality_score=9,
                vram_required=8.5,
                load_time_ms=3000
            ),
            'llava:7b': ModelCapability(
                name='llava:7b',
                task_types=[TaskType.VISION],
                size_gb=4.7,
                speed_score=6,
                quality_score=7,
                vram_required=5.5,
                load_time_ms=2000
            ),
            
            # CONSTITUTIONAL MODELS
            'sovereign-constitutional:latest': ModelCapability(
                name='sovereign-constitutional:latest',
                task_types=[TaskType.CONSTITUTIONAL, TaskType.ANALYSIS],
                size_gb=3.8,
                speed_score=7,
                quality_score=9,
                vram_required=4.5,
                load_time_ms=1500
            ),
            
            # FAST MODELS
            'llama3.2:latest': ModelCapability(
                name='llama3.2:latest',
                task_types=[TaskType.CHAT, TaskType.UNKNOWN],
                size_gb=2.0,
                speed_score=9,
                quality_score=6,
                vram_required=2.5,
                load_time_ms=500
            ),
            'smollm2:360m': ModelCapability(
                name='smollm2:360m',
                task_types=[TaskType.CHAT],
                size_gb=0.725,
                speed_score=10,
                quality_score=4,
                vram_required=1.0,
                load_time_ms=200
            ),
        }
    
    def analyze_task(self, task: str) -> Dict[str, Any]:
        """Analyze task to determine requirements"""
        task_lower = task.lower()
        
        # Detect task type
        task_type = TaskType.UNKNOWN
        if any(word in task_lower for word in ['code', 'function', 'class', 'script', 'program', 'write', 'implement']):
            task_type = TaskType.CODE
        elif any(word in task_lower for word in ['explain', 'why', 'reason', 'think', 'analyze', 'evaluate']):
            task_type = TaskType.REASONING
        elif any(word in task_lower for word in ['image', 'picture', 'see', 'vision', 'screen', 'view']):
            task_type = TaskType.VISION
        elif any(word in task_lower for word in ['constitution', 'law', 'rule', 'govern', 'policy']):
            task_type = TaskType.CONSTITUTIONAL
        elif any(word in task_lower for word in ['strategy', 'plan', 'evolve', 'optimize']):
            task_type = TaskType.STRATEGY
        
        # Calculate complexity
        complexity = min(10, len(task.split()) / 10 + 2)
        
        # Detect requirements
        requirements = {
            'needs_code': task_type == TaskType.CODE,
            'needs_reasoning': task_type in [TaskType.REASONING, TaskType.ANALYSIS],
            'needs_vision': task_type == TaskType.VISION,
            'needs_constitutional': task_type == TaskType.CONSTITUTIONAL,
            'complexity': complexity,
            'estimated_tokens': len(task.split()) * 2,
            'task_type': task_type.value
        }
        
        return requirements
    
    def select_best_model(self, requirements: Dict[str, Any]) -> Tuple[str, LoadingState]:
        """Select the best model based on requirements"""
        
        # Score each model
        scores = []
        for name, model in self.models.items():
            score = 0
            
            # Match task type
            task_type = TaskType(requirements['task_type'])
            if task_type in model.task_types:
                score += 30
            elif task_type == TaskType.UNKNOWN and TaskType.UNKNOWN in model.task_types:
                score += 20
            
            # Complexity matching
            if requirements['complexity'] > 7:
                score += model.quality_score * 2
            else:
                score += model.speed_score * 2
            
            # Specialized requirements
            if requirements.get('needs_code') and 'code' in [t.value for t in model.task_types]:
                score += 20
            if requirements.get('needs_vision') and 'vision' in [t.value for t in model.task_types]:
                score += 20
            if requirements.get('needs_constitutional') and 'constitutional' in [t.value for t in model.task_types]:
                score += 20
            
            # Performance history
            stats = self.model_stats[name]
            if stats['uses'] > 0:
                success_rate = stats['successes'] / stats['uses']
                score += success_rate * 10
                avg_time = stats['total_time'] / stats['uses'] if stats['uses'] > 0 else 0
                if avg_time < 2000:
                    score += 5
            
            scores.append((name, score))
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        best_model = scores[0][0]
        
        # Create loading state
        model = self.models[best_model]
        loading_state = LoadingState(
            stage="loading_model",
            message=f"Loading {best_model}...",
            progress=0,
            estimated_time_ms=model.load_time_ms,
            model_name=best_model
        )
        
        return best_model, loading_state
    
    async def load_model_with_animation(self, model_name: str, callback=None):
        """Simulate model loading with animation"""
        model = self.models[model_name]
        steps = [
            (0, "Initializing model..."),
            (20, f"Loading {model_name} into VRAM..."),
            (40, f"Allocating {model.size_gb}GB memory..."),
            (60, "Warming up inference engine..."),
            (80, "Almost ready..."),
            (100, "Model loaded!")
        ]
        
        total_time = model.load_time_ms / 1000  # Convert to seconds
        step_time = total_time / len(steps)
        
        for progress, message in steps:
            self.current_load_state = LoadingState(
                stage="loading",
                message=message,
                progress=progress,
                estimated_time_ms=int((total_time - (step_time * steps.index((progress, message)))) * 1000),
                model_name=model_name
            )
            
            if callback:
                await callback(self.current_load_state)
            
            await asyncio.sleep(step_time)
    
    async def route_task(self, task: str, callback=None) -> Dict[str, Any]:
        """Route task to best model with loading animation"""
        start_time = time.time()
        
        # Step 1: Analyze task
        self.current_load_state = LoadingState(
            stage="analyzing",
            message="Analyzing task requirements...",
            progress=10,
            estimated_time_ms=500,
            model_name="analyzer"
        )
        if callback:
            await callback(self.current_load_state)
        await asyncio.sleep(0.3)
        
        requirements = self.analyze_task(task)
        
        # Step 2: Select model
        self.current_load_state = LoadingState(
            stage="selecting",
            message=f"Selecting best model for {requirements['task_type']}...",
            progress=30,
            estimated_time_ms=300,
            model_name="selector"
        )
        if callback:
            await callback(self.current_load_state)
        await asyncio.sleep(0.2)
        
        selected_model, loading_state = self.select_best_model(requirements)
        
        # Step 3: Load model with animation
        await self.load_model_with_animation(selected_model, callback)
        
        # Step 4: Execute (simulated)
        self.current_load_state = LoadingState(
            stage="executing",
            message=f"Processing with {selected_model}...",
            progress=90,
            estimated_time_ms=1000,
            model_name=selected_model
        )
        if callback:
            await callback(self.current_load_state)
        
        # Simulate processing
        await asyncio.sleep(0.5)
        
        # Record stats
        elapsed = (time.time() - start_time) * 1000
        self.model_stats[selected_model]['uses'] += 1
        self.model_stats[selected_model]['total_time'] += elapsed
        self.model_stats[selected_model]['successes'] += 1
        
        # Return routing info
        return {
            'task': task,
            'analysis': requirements,
            'selected_model': selected_model,
            'load_time_ms': elapsed,
            'model_stats': self.model_stats[selected_model],
            'drift_lock': hashlib.sha256(f"{task}:{selected_model}:{time.time()}".encode()).hexdigest()[:16]
        }

# Singleton instance
smart_router = SmartRouter()