"""
SCE Bytecode Schema
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import hashlib
import json
import time

@dataclass
class SCEBytecode:
    """SCE Bytecode container"""
    bytecode: bytes
    version: str = "1.0.0"
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            bytecode=json.dumps(data).encode(),
            version=data.get('version', '1.0.0')
        )
        
    def compute_hash(self) -> str:
        return hashlib.sha256(self.bytecode).hexdigest()
