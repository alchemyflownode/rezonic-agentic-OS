"""
VERA LEDGER - Cryptographic proof of every action
"""
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import hmac
import os

class VERALedger:
    """Immutable audit trail with cryptographic proofs"""
    
    def __init__(self, worker_id: str, storage_path: str = "data/vera/ledger"):
        self.worker_id = worker_id
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Generate or load worker key
        self.key_file = self.storage_path / f"{worker_id}.key"
        if self.key_file.exists():
            self.worker_key = self.key_file.read_bytes()
        else:
            self.worker_key = os.urandom(32)
            self.key_file.write_bytes(self.worker_key)
        
        self.current_ledger = self.storage_path / f"{datetime.now().strftime('%Y%m')}.jsonl"
        self.chain = []
        self.last_hash = "0" * 64
    
    def create_proof(self, action_type: str, target: str, result_hash: str, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Create a cryptographic proof of an action"""
        timestamp = time.time_ns()
        
        proof = {
            'worker_id': self.worker_id,
            'action_type': action_type,
            'target': target,
            'result_hash': result_hash,
            'metadata': metadata,
            'timestamp': timestamp,
            'previous_hash': self._get_last_hash()
        }
        
        proof_json = json.dumps(proof, sort_keys=True)
        proof_hash = hashlib.sha256(proof_json.encode()).hexdigest()
        
        signature = hmac.new(
            self.worker_key,
            proof_hash.encode(),
            hashlib.sha256
        ).hexdigest()
        
        ledger_entry = {
            'proof_hash': proof_hash,
            'signature': signature,
            'proof': proof
        }
        
        with open(self.current_ledger, 'a') as f:
            f.write(json.dumps(ledger_entry) + '\n')
        
        self.chain.append(ledger_entry)
        self.last_hash = proof_hash
        
        return {
            'proofHash': proof_hash,
            'signature': signature,
            'timestamp': str(timestamp)
        }
    
    def _get_last_hash(self) -> str:
        """Get hash of last entry for chain linking"""
        if not self.current_ledger.exists():
            return hashlib.sha256(b'genesis').hexdigest()
        
        with open(self.current_ledger, 'r') as f:
            lines = f.readlines()
            if not lines:
                return hashlib.sha256(b'genesis').hexdigest()
            last = json.loads(lines[-1])
            return last['proof_hash']
    
    def get_stats(self) -> Dict:
        return {
            'worker_id': self.worker_id,
            'proof_count': len(self.chain),
            'last_hash': self.last_hash[:16] + "..."
        }
