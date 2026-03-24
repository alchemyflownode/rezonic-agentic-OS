# security/key_manager.py
"""Secure API key management for exchange integration"""

import os
import json
import base64
import logging
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger("phoenix.security")

class KeyManager:
    """Secure storage and management of API keys"""
    
    def __init__(self, master_password: str = None):
        self.key_file = Path.home() / ".rez_hive_key"
        self.keys_file = Path("data/encrypted_keys.json")
        self.master_password = master_password or os.getenv("REZ_MASTER_KEY")
        self.cipher = None
        self._init_cipher()
    
    def _init_cipher(self):
        """Initialize encryption cipher"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            if not self.master_password:
                raise ValueError("Master password required for first-time setup")
            
            # Derive key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'rez_hive_salt_2024',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.master_password.encode()))
            
            # Save key with restricted permissions
            with open(self.key_file, 'wb') as f:
                f.write(key)
            os.chmod(self.key_file, 0o600)
            logger.info("New encryption key created")
        
        self.cipher = Fernet(key)
    
    def encrypt_api_key(self, exchange: str, api_key: str, api_secret: str) -> dict:
        """Encrypt and store API keys for an exchange"""
        try:
            # Encrypt the keys
            encrypted_key = self.cipher.encrypt(api_key.encode()).decode()
            encrypted_secret = self.cipher.encrypt(api_secret.encode()).decode()
            
            # Load existing keys
            keys = self._load_keys()
            
            # Store encrypted
            keys[exchange] = {
                "api_key": encrypted_key,
                "api_secret": encrypted_secret,
                "encrypted_at": __import__('time').time(),
                "version": 1
            }
            
            # Save to file
            self._save_keys(keys)
            logger.info(f"API keys for {exchange} encrypted and stored")
            return {"success": True, "exchange": exchange}
            
        except Exception as e:
            logger.error(f"Failed to encrypt keys for {exchange}: {e}")
            return {"success": False, "error": str(e)}
    
    def decrypt_api_key(self, exchange: str) -> dict:
        """Retrieve and decrypt API keys for an exchange"""
        try:
            keys = self._load_keys()
            if exchange not in keys:
                return {"success": False, "error": f"No keys found for {exchange}"}
            
            # Decrypt
            api_key = self.cipher.decrypt(keys[exchange]["api_key"].encode()).decode()
            api_secret = self.cipher.decrypt(keys[exchange]["api_secret"].encode()).decode()
            
            return {
                "success": True,
                "exchange": exchange,
                "api_key": api_key,
                "api_secret": api_secret
            }
            
        except Exception as e:
            logger.error(f"Failed to decrypt keys for {exchange}: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_api_key(self, exchange: str) -> dict:
        """Delete stored keys for an exchange"""
        try:
            keys = self._load_keys()
            if exchange in keys:
                del keys[exchange]
                self._save_keys(keys)
                logger.info(f"API keys for {exchange} deleted")
                return {"success": True, "exchange": exchange}
            return {"success": False, "error": f"No keys found for {exchange}"}
            
        except Exception as e:
            logger.error(f"Failed to delete keys for {exchange}: {e}")
            return {"success": False, "error": str(e)}
    
    def list_exchanges(self) -> list:
        """List exchanges with stored keys"""
        keys = self._load_keys()
        return list(keys.keys())
    
    def _load_keys(self) -> dict:
        """Load encrypted keys from file"""
        if not self.keys_file.exists():
            return {}
        
        try:
            with open(self.keys_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load keys: {e}")
            return {}
    
    def _save_keys(self, keys: dict) -> None:
        """Save encrypted keys to file"""
        try:
            self.keys_file.parent.mkdir(exist_ok=True)
            with open(self.keys_file, 'w') as f:
                json.dump(keys, f, indent=2)
            os.chmod(self.keys_file, 0o600)
        except Exception as e:
            logger.error(f"Failed to save keys: {e}")
            raise
    
    def rotate_keys(self, exchange: str) -> dict:
        """Rotate keys (requires new keys to be provided)"""
        logger.warning(f"Key rotation requires manual update for {exchange}")
        return {"success": False, "error": "Manual rotation required - provide new keys"}

__all__ = ['KeyManager']