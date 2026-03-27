# workers/app_builder_worker.py
"""App Builder Worker - Generate deployable app blueprints from intent"""

import hashlib
import json
import re
from typing import Dict, Any
from base_worker import Worker


class AppBuilderWorker(Worker):
    """Generate app blueprints from user intent"""
    
    def __init__(self):
        super().__init__("app_builder")
        self.default_stack = {
            "frontend": "Next.js 14 + Tailwind CSS + Framer Motion",
            "backend": "FastAPI + Supabase",
            "ai": "Phoenix Kernel + Ollama",
            "state": "Zustand",
            "database": "PostgreSQL (Supabase)",
            "auth": "Supabase Auth"
        }
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Generate blueprint from project intent"""
        intent = kwargs.get("intent", task)
        
        # Parse intent
        project_type = self._detect_project_type(intent)
        tech_stack = self._recommend_stack(project_type)
        architecture = self._generate_architecture(project_type, intent)
        risks = self._identify_risks(project_type, intent)
        
        blueprint = {
            "title": f"App: {intent[:50]}",
            "type": project_type,
            "stack": tech_stack,
            "architecture": architecture,
            "risks": risks,
            "files": self._generate_file_structure(project_type),
            "commands": self._generate_commands(project_type),
            "drift_lock": self._generate_drift_lock(intent)
        }
        
        return {
            "success": True,
            "blueprint": blueprint,
            "worker": self.name,
            "drift_lock": blueprint["drift_lock"]
        }
    
    def _detect_project_type(self, intent: str) -> str:
        """Detect project type from intent"""
        intent_lower = intent.lower()
        if "gallery" in intent_lower or "art" in intent_lower:
            return "gallery"
        elif "dashboard" in intent_lower or "analytics" in intent_lower:
            return "dashboard"
        elif "ecommerce" in intent_lower or "shop" in intent_lower:
            return "ecommerce"
        elif "chat" in intent_lower or "messaging" in intent_lower:
            return "chat"
        elif "game" in intent_lower:
            return "game"
        else:
            return "generic"
    
    def _recommend_stack(self, project_type: str) -> Dict:
        """Recommend tech stack based on project type"""
        stack = self.default_stack.copy()
        
        if project_type == "gallery":
            stack["frontend"] = "Next.js + Tailwind + Framer Motion + Sharp"
            stack["additional"] = "Cloudinary for image optimization"
        elif project_type == "dashboard":
            stack["frontend"] = "Next.js + Tailwind + Recharts + Framer Motion"
            stack["state"] = "Zustand + TanStack Query"
        elif project_type == "ecommerce":
            stack["frontend"] = "Next.js + Tailwind + Stripe"
            stack["backend"] = "FastAPI + Supabase + Stripe Webhooks"
        elif project_type == "chat":
            stack["frontend"] = "Next.js + Tailwind + Socket.io-client"
            stack["backend"] = "FastAPI + WebSockets + Phoenix Kernel"
        
        return stack
    
    def _generate_architecture(self, project_type: str, intent: str) -> Dict:
        """Generate architecture diagram data"""
        return {
            "layers": ["UI", "State Management", "API Layer", "Workers", "Memory"],
            "data_flow": "User → UI → API → Workers → Response",
            "workers": ["code_execution", "sandbox", "brain", "memory"],
            "components": [
                "app/page.tsx",
                "components/",
                "hooks/",
                "lib/",
                "workers/"
            ]
        }
    
    def _identify_risks(self, project_type: str, intent: str) -> list:
        """Identify potential risks"""
        risks = [
            "Performance: Optimize asset loading for high-res media",
            "Security: Ensure sandbox isolation for code execution",
            "Timeline: 40-hour development window may be tight",
            "User Experience: Need intuitive interface for non-technical users"
        ]
        
        if "image" in intent.lower() or "gallery" in intent.lower():
            risks.insert(0, "Images: Use Next.js Image optimization and lazy loading")
        if "real-time" in intent.lower():
            risks.append("Real-time: Implement WebSocket with reconnection logic")
        
        return risks
    
    def _generate_file_structure(self, project_type: str) -> list:
        """Generate recommended file structure"""
        base = [
            "src/app/layout.tsx",
            "src/app/page.tsx",
            "src/components/ui/",
            "src/hooks/",
            "src/lib/",
            "src/types/"
        ]
        
        if project_type == "gallery":
            base.extend([
                "src/app/upload/page.tsx",
                "src/app/gallery/[id]/page.tsx",
                "src/components/gallery/painting-card.tsx",
                "src/components/ui/frame-simulator.tsx"
            ])
        elif project_type == "dashboard":
            base.extend([
                "src/components/dashboard/metrics-card.tsx",
                "src/components/dashboard/chart.tsx",
                "src/hooks/use-data.ts"
            ])
        
        return base
    
    def _generate_commands(self, project_type: str) -> list:
        """Generate setup commands"""
        return [
            "npx create-next-app@latest my-app --typescript --tailwind",
            "cd my-app",
            "npm install framer-motion zustand @tanstack/react-query",
            "npm run dev"
        ]
    
    def _generate_drift_lock(self, data: str) -> str:
        """Generate drift lock hash"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]