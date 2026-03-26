import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# backend/workers/file_doctor_worker.py
"""
FILE DOCTOR WORKER - Heals corrupted files
"""

import hashlib
import os
try:
    import magic
    MAGIC_OK = True
except ImportError:
    MAGIC_OK = False
    class MagicStub:
        def from_file(self, p): return 'application/octet-stream'
    magic = MagicStub()
from typing import Dict, Any

class FileDoctorWorker:
    def __init__(self):
        self.name = "FileDoctorWorker"
        self.repairable_types = [
            'image/jpeg', 'image/png', 'image/gif',
            'application/pdf',
            'text/plain', 'text/markdown',
            'application/zip', 'application/x-rar-compressed'
        ]
    
    async def process(self, task: str, memory_bus=None) -> Dict[str, Any]:
        if "scan" in task.lower():
            return await self._scan_file(task)
        elif "repair" in task.lower():
            return await self._repair_file(task)
        elif "integrity" in task.lower():
            return await self._check_integrity(task)
        else:
            return {
                "content": "ðŸ©º **File Doctor Commands**:\nâ€¢ /filedoctor scan <file> - Check file health\nâ€¢ /filedoctor repair <file> - Attempt repair\nâ€¢ /filedoctor integrity <folder> - Verify all files",
                "worker": self.name
            }
    
    async def _scan_file(self, task: str) -> Dict[str, Any]:
        # Extract path
        path = task.replace("/filedoctor scan", "").strip().strip('"\'')
        
        if not os.path.exists(path):
            return {"content": f"âŒ File not found: {path}", "worker": self.name}
        
        # Check file
        file_size = os.path.getsize(path)
        mime = magic.from_file(path, mime=True)
        
        # Calculate checksum
        with open(path, 'rb') as f:
            file_hash = hashlib.sha256(f.read(8192)).hexdigest()[:16]
        
        # Check if repairable
        repairable = mime in self.repairable_types
        
        # Publish event
        await event_bus.publish(Event(
            type=EventType.FILE_SCANNED,
            source="file_doctor",
            payload={"path": path, "mime": mime, "repairable": repairable}
        ))
        
        return {
            "content": f"ðŸ©º **File Scan Complete**\n\nâ€¢ Path: {path}\nâ€¢ Size: {file_size:,} bytes\nâ€¢ Type: {mime}\nâ€¢ Checksum: {file_hash}\nâ€¢ Repairable: {'âœ…' if repairable else 'âŒ'}",
            "worker": self.name
        }

    async def process(self, task: str, memory_bus=None):
        """Process task – auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}

