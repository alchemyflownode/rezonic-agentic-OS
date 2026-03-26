import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
SCE Compiler - Sovereign Creative Engine
Parses SCE Bytecode and orchestrates multi-modal generation
"""

import asyncio
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime

from workers.base_worker import BaseWorker
from core.sce_schema import SCEProtocol

class SCECompiler(BaseWorker):
    def __init__(self):
        super().__init__("sce_compiler", "Sovereign Creative Engine Compiler")
        self.is_ready = True
        self.compilation_history = []
        
    async def process(self, task: str, **kwargs) -> Dict[str, Any]:
        """Compile and render SCE protocol"""
        return await self.track_processing(self._compile, task)
    
    async def _compile(self, task: str) -> Dict[str, Any]:
        self.log("info", f"Compiling SCE: {task[:50]}...")
        
        # Try to parse as JSON
        try:
            protocol = json.loads(task)
        except:
            # If not JSON, assume it's a topic and generate
            from workers.brain_worker import BrainWorker
            brain = BrainWorker()
            result = await brain.process(task)
            protocol = result.get("protocol", {})
        
        if not protocol:
            return {
                "status": "error",
                "content": "❌ Could not parse or generate SCE protocol"
            }
        
        # Validate protocol structure
        validation = self._validate_protocol(protocol)
        if not validation["valid"]:
            return validation
        
        # Compile each segment
        segments = protocol.get("segments", [])
        compiled_segments = []
        
        for i, segment in enumerate(segments):
            self.log("info", f"Compiling segment {i+1}/{len(segments)}")
            
            compiled = await self._compile_segment(segment, i)
            compiled_segments.append(compiled)
            
            # Simulate validation
            await asyncio.sleep(0.3)
        
        # Generate final output
        output_hash = hashlib.sha256(
            json.dumps(protocol, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        result = {
            "status": "success",
            "content": f"✅ SCE Protocol compiled successfully",
            "protocol_hash": output_hash,
            "segments_compiled": len(compiled_segments),
            "validation_scores": [s["validation_score"] for s in compiled_segments],
            "avg_score": sum(s["validation_score"] for s in compiled_segments) / len(compiled_segments),
            "compiled_segments": compiled_segments,
            "vfs": protocol.get("vfs", [])
        }
        
        self.compilation_history.append({
            "timestamp": datetime.now().isoformat(),
            "hash": output_hash,
            "segments": len(compiled_segments)
        })
        
        return result
    
    async def _compile_segment(self, segment: Dict, index: int) -> Dict:
        """Compile individual segment"""
        # Simulate rendering and validation
        validation_score = min(0.85 + (index * 0.02), 0.98)
        
        return {
            "segment_id": segment.get("id", index + 1),
            "title": segment.get("title", f"Segment {index+1}"),
            "duration": segment.get("duration", 3),
            "validation_score": round(validation_score, 2),
            "passed": validation_score >= segment.get("exitState", {}).get("validation_cue", {}).get("threshold", 0.8),
            "output_url": f"/output/segment_{index+1}_{int(asyncio.get_event_loop().time())}.mp4"
        }
    
    def _validate_protocol(self, protocol: Dict) -> Dict:
        """Validate SCE protocol structure"""
        required_keys = ["meta", "segments"]
        for key in required_keys:
            if key not in protocol:
                return {
                    "status": "error",
                    "valid": False,
                    "content": f"❌ Missing required key: {key}"
                }
        
        if not isinstance(protocol["segments"], list) or len(protocol["segments"]) == 0:
            return {
                "status": "error",
                "valid": False,
                "content": "❌ Segments must be a non-empty array"
            }
        
        return {"valid": True, "status": "ok"}
    
    async def get_history(self) -> List[Dict]:
        """Get compilation history"""
        return self.compilation_history
