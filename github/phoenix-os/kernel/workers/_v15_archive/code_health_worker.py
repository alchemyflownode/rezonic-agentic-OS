"""
workers/code_health_worker.py — Unified Code Health Worker
Combines RezCoder's static analysis with FileDoctor's healing
"""

from pathlib import Path
from typing import Dict, Any
import asyncio

# Import both workers
try:
    from workers.rezcoder import RezCoderWorker
    from workers.file_doctor_worker import FileDoctorWorker
except ImportError:
    pass


class CodeHealthWorker:
    """Unified worker for code health: analysis + healing"""
    
    name = "code_health"
    
    def __init__(self):
        self.rezcoder = RezCoderWorker()
        self.file_doctor = FileDoctorWorker()
        self._initialized = False
    
    async def initialize(self):
        await self.rezcoder.initialize()
        self._initialized = True
    
    async def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """Smart routing to appropriate worker"""
        task_lower = task.lower()
        
        # Route to FileDoctor for corruption detection
        if any(keyword in task_lower for keyword in ['scan', 'repair', 'integrity']):
            return await self.file_doctor.process(task, **kwargs)
        
        # Route to RezCoder for code analysis
        if any(keyword in task_lower for keyword in ['review', 'fix', 'report']):
            return await self.rezcoder.execute(task, **kwargs)
        
        # Default: Full health check
        return await self.full_health_check(task, **kwargs)
    
    async def full_health_check(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Run both RezCoder and FileDoctor checks"""
        
        # Step 1: Check file integrity
        integrity = await self.file_doctor.process(f"/filedoctor scan {file_path}")
        
        # Step 2: Check code quality
        quality = await self.rezcoder.execute("review", file_path=file_path)
        
        # Step 3: Combine results
        return {
            "success": True,
            "worker": self.name,
            "file": file_path,
            "integrity": {
                "healthy": "âŒ" not in integrity.get("content", ""),
                "details": integrity.get("content", "")[:500],
            },
            "quality": {
                "health_score": quality.get("health_score", 0),
                "issues": quality.get("total_issues", 0),
                "errors": quality.get("error_count", 0),
            },
            "recommendation": self._get_recommendation(integrity, quality),
        }
    
    def _get_recommendation(self, integrity, quality) -> str:
        """Generate actionable recommendation"""
        if integrity.get("content", "").find("âŒ") != -1:
            return "File may be corrupted. Run: /filedoctor repair"
        elif quality.get("health_score", 0) < 70:
            return "Code quality needs improvement. Run: /rez-fix"
        elif quality.get("health_score", 0) > 85:
            return "Code health is excellent!"
        return "Consider minor improvements"