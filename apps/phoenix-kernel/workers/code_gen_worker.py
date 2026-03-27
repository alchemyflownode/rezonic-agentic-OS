# workers/code_gen_worker.py
"""Code Generation Worker - Generate actual code from blueprint"""

import hashlib
from typing import Dict, Any
from base_worker import Worker


class CodeGenWorker(Worker):
    """Generate production code from app builder blueprint"""
    
    def __init__(self):
        super().__init__("code_gen")
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Generate code files from blueprint"""
        blueprint = kwargs.get("blueprint", {})
        drift_lock = blueprint.get("drift_lock", "")
        
        # Verify blueprint integrity
        if not self._verify_blueprint(blueprint):
            return {
                "success": False,
                "error": "Blueprint integrity verification failed",
                "worker": self.name
            }
        
        # Generate files
        files = await self._generate_files(blueprint)
        
        # Generate drift lock for the generated code
        code_hash = self._compute_code_hash(files)
        
        return {
            "success": True,
            "files": files,
            "code_hash": code_hash,
            "parent_drift_lock": drift_lock,
            "worker": self.name
        }
    
    def _verify_blueprint(self, blueprint: Dict) -> bool:
        """Verify blueprint drift lock"""
        stored_lock = blueprint.get("drift_lock")
        if not stored_lock:
            return False
        
        # Recompute lock from blueprint data
        blueprint_data = {k: v for k, v in blueprint.items() if k != "drift_lock"}
        import json
        content = json.dumps(blueprint_data, sort_keys=True, default=str)
        computed_lock = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        return stored_lock == computed_lock
    
    async def _generate_files(self, blueprint: Dict) -> list:
        """Generate actual file content from blueprint"""
        profile = blueprint.get("profile", {})
        project_type = profile.get("type", "generic")
        
        if project_type == "perception_engine":
            return self._generate_perception_engine(blueprint)
        elif project_type == "gallery":
            return self._generate_gallery(blueprint)
        else:
            return self._generate_generic(blueprint)
    
    def _generate_perception_engine(self, blueprint: Dict) -> list:
        """Generate SQUINT-style perception engine"""
        return [
            {
                "path": "app/layout.tsx",
                "content": """import './globals.css';
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-[#0f172a] text-[#f8fafc]`}>
        <nav className="border-b border-[#1e293b] p-4 flex justify-between items-center">
          <div className="font-bold text-[#f8fafc] tracking-widest">SQUINT</div>
          <div className="text-xs text-[#3b82f6] font-mono">Δ=0</div>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}""",
                "language": "typescript"
            },
            {
                "path": "hooks/useVolatilityMotion.ts",
                "content": """import { useEffect } from 'react';
import { useSpring } from 'framer-motion';

export function useVolatilityMotion(intensity: number) {
  const weight = Math.min(2, Math.max(0, intensity * 0.02));
  const stiffness = 100 + weight * 400;
  const damping = Math.max(5, 20 - weight * 7);
  
  const x = useSpring(0, { stiffness, damping });
  const scale = useSpring(1, { stiffness, damping });
  
  useEffect(() => {
    let rafId: number;
    let startTime = performance.now();
    const speed = Math.max(200, 500 - weight * 150);
    
    const animate = () => {
      const elapsed = performance.now() - startTime;
      x.set(Math.sin(elapsed / speed * Math.PI * 2) * (weight / 2) * 12);
      scale.set(1 + (weight / 2) * 0.1);
      rafId = requestAnimationFrame(animate);
    };
    
    rafId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafId);
  }, [weight, x, scale]);
  
  return { x, scale, weight, stiffness, damping };
}""",
                "language": "typescript"
            }
        ]
    
    def _generate_gallery(self, blueprint: Dict) -> list:
        """Generate gallery app"""
        return []
    
    def _generate_generic(self, blueprint: Dict) -> list:
        """Generate generic app structure"""
        return []
    
    def _compute_code_hash(self, files: list) -> str:
        """Compute hash of generated code"""
        import json
        content = json.dumps(files, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]