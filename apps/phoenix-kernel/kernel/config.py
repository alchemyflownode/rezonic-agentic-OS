# kernel/config.py
"""
Central configuration management for Phoenix Kernel.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class PhoenixConfig:
    """Unified configuration for all kernel components"""
    
    # Core
    version: str = "15.3.1"
    host: str = os.getenv("PHOENIX_HOST", "127.0.0.1")
    port: int = int(os.getenv("PHOENIX_PORT", "8002"))
    metrics_port: int = int(os.getenv("METRICS_PORT", "8003"))
    
    # CORS
    cors_origins: List[str] = field(default_factory=lambda: 
        os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8002").split(",")
    )
    
    # Security - API Keys (fallback)
    api_keys: Dict[str, str] = field(default_factory=lambda: {
        os.getenv("PHOENIX_ADMIN_KEY", "rez-hive-admin-key-2026"): "admin",
        "rez-hive-viewer-key-2026": "viewer",
    })
    
    # JWT Authentication
    jwt_secret: str = os.getenv("JWT_SECRET", "change-this-in-production-please")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    
    # Ollama
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    default_model: str = os.getenv("OLLAMA_MODEL", "phoenix-16k")
    num_ctx: int = int(os.getenv("OLLAMA_NUM_CTX", "16384"))
    num_gpu_layers: int = int(os.getenv("OLLAMA_GPU_LAYERS", "99"))
    num_parallel: int = int(os.getenv("OLLAMA_NUM_PARALLEL", "2"))
    ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    
    # Performance
    max_concurrent_requests: int = 2
    request_timeout: int = 30
    rate_limit_calls: int = int(os.getenv("RATE_LIMIT_CALLS", "100"))
    rate_limit_period: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    
    # Trading
    paper_balance: float = float(os.getenv("PAPER_BALANCE", "1000000.0"))
    default_symbol: str = os.getenv("DEFAULT_SYMBOL", "BTCUSDT")
    trade_fee: float = float(os.getenv("TRADE_FEE", "0.001"))
    
    # Constitution
    constitution_strict: bool = os.getenv("CONSTITUTION_STRICT", "true").lower() == "true"
    constitution_patterns: List[str] = field(default_factory=lambda: [
        r'rm\s+-rf\s+/', r'format\s+c:', r'del\s+/f\s+/q', r'mkfs\.[a-z]+',
        r'shutdown\s+-[rh]', r'reboot', r':\(\)\{\s*:\|:&\s*\};:',
        r'chmod\s+-R\s+777\s+/', r'>\s*/dev/sd', r'dd\s+if=.*of=/dev/',
        r'wget\s+.*\|\s*bash', r'curl\s+.*\|\s*sh',
        r'python\s+-c\s+[\'"].*os\.system'
    ])
    
    # Paths
    workspace: Path = Path(os.getenv("VSCODE_WORKSPACE", str(Path.cwd())))
    
    # Limits
    chain_maxlen: int = int(os.getenv("CHAIN_MAXLEN", "10000"))
    event_batch_size: int = int(os.getenv("EVENT_BATCH_SIZE", "50"))
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "104857600"))
    
    @classmethod
    def from_env(cls) -> "PhoenixConfig":
        """Load configuration from environment"""
        return cls()
    
    def validate(self) -> bool:
        """Validate critical configuration"""
        if self.jwt_secret == "change-this-in-production-please":
            import warnings
            warnings.warn(
                "⚠️ Using default JWT secret - not secure for production!\n"
                "Set JWT_SECRET environment variable for production.",
                RuntimeWarning
            )
        return True

# Global config instance
config = PhoenixConfig.from_env()

# Validate on import
config.validate()
