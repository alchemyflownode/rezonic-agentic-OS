# core/sce_schema.py
"""
SCE Protocol Core Schema
Defines the Sovereign Creative Engine protocol structure
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional


class SCEProtocol:
    """
    Sovereign Creative Engine Protocol
    Handles blueprint creation and verification
    """
    
    VERSION = "1.0.0"
    
    @staticmethod
    def create_drift_lock(data: Any) -> str:
        """
        Create a drift lock hash from data
        
        Args:
            data: Data to hash
            
        Returns:
            16-character hash
        """
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    @staticmethod
    def create_blueprint(intent: dict, dna: dict, execution: dict, parent_lock: str = None) -> dict:
        """
        Create an SCE blueprint
        
        Args:
            intent: Intent dictionary
            dna: DNA dictionary
            execution: Execution dictionary
            parent_lock: Optional parent drift lock
            
        Returns:
            Blueprint dictionary
        """
        blueprint = {
            "protocol_version": SCEProtocol.VERSION,
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "dna": dna,
            "execution": execution
        }
        if parent_lock:
            blueprint["parent_drift_lock"] = parent_lock
        blueprint["master_drift_lock"] = SCEProtocol.create_drift_lock(blueprint)
        return blueprint
    
    @staticmethod
    def verify_blueprint(blueprint: dict) -> dict:
        """
        Verify a blueprint's integrity
        
        Args:
            blueprint: Blueprint dictionary
            
        Returns:
            Verification result
        """
        stored_lock = blueprint.get('master_drift_lock')
        calculated_lock = SCEProtocol.create_drift_lock(blueprint)
        is_valid = stored_lock == calculated_lock
        return {
            'verified': is_valid,
            'badge': '🟢 SOVEREIGN' if is_valid else '🔴 DRIFTED',
            'drift_lock': stored_lock
        }
    
    @staticmethod
    def extract_metadata(blueprint: dict) -> dict:
        """
        Extract metadata from blueprint
        
        Args:
            blueprint: Blueprint dictionary
            
        Returns:
            Metadata dictionary
        """
        return {
            'timestamp': blueprint.get('timestamp'),
            'protocol_version': blueprint.get('protocol_version'),
            'master_drift_lock': blueprint.get('master_drift_lock'),
            'parent_drift_lock': blueprint.get('parent_drift_lock'),
            'intent': blueprint.get('intent', {}).get('action', 'unknown'),
            'worker': blueprint.get('intent', {}).get('worker', 'unknown')
        }