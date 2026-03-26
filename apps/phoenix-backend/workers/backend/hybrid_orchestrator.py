from cognitive_imports.workers.compute_orchestrator import ComputeOrchestrator

class HybridOrchestrator(ComputeOrchestrator):
    def __init__(self, hive_bus=None):
        super().__init__()
        self.hive_bus = hive_bus# backend/workers/hybrid_orchestrator.py
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HybridOrchestrator:
    """
    TB-CSPN (Task-Based Communication Sequential Process Network) style orchestrator
    Routes tasks to either deterministic tools or semantic LLM based on intent
    """
    
    def __init__(self):
        # Deterministic command patterns (fast path)
        self.deterministic_patterns = {
            r"^(?:list|ls|dir|show files).*": {"tool": "vfs_ls", "args_extractor": self._extract_path},
            r"^(?:cd|go to|enter|navigate to)\s+(.+)$": {"tool": "vfs_cd", "args_extractor": self._extract_path_from_command},
            r"^(?:cat|read|show|view)\s+file\s+(.+)$": {"tool": "vfs_cat", "args_extractor": self._extract_path_from_command},
            r"^(?:show|list|what) agents?$": {"tool": "hive_list_agents", "args_extractor": lambda x: {}},
            r"^(?:search|find)\s+web\s+for\s+(.+)$": {"tool": "web_search", "args_extractor": self._extract_query},
            r"^(?:search|find)\s+file\s+(.+)$": {"tool": "search_pc", "args_extractor": self._extract_query},
            
            # ⚡ The OKIRU Sandbox Trigger
            r"^(?:/run|execute code|run latest code|test script).*": {
                "tool": "sandbox_run",
                "args_extractor": lambda x: {}
            }
        }
        logger.info("✅ HybridOrchestrator initialized with OKIRU triggers")
    
    def _extract_path(self, text: str) -> Dict[str, str]:
        path = "."
        for pattern in [r'in\s+([^\s]+)', r'path\s+([^\s]+)', r'dir\s+([^\s]+)']:
            match = re.search(pattern, text.lower())
            if match:
                path = match.group(1)
                break
        return {"path": path}
    
    def _extract_path_from_command(self, text: str) -> Dict[str, str]:
        parts = text.split(maxsplit=1)
        return {"path": parts[1]} if len(parts) > 1 else {"path": "."}
    
    def _extract_query(self, text: str) -> Dict[str, str]:
        parts = text.split(maxsplit=1)
        return {"query": parts[1]} if len(parts) > 1 else {"query": text}
    
    def evaluate_intent(self, prompt: str) -> Dict[str, Any]:
        prompt_lower = prompt.lower().strip()
        for pattern, config in self.deterministic_patterns.items():
            if re.match(pattern, prompt_lower):
                return {
                    "routing_type": "deterministic",
                    "target_mcp_tool": config["tool"],
                    "arguments": config["args_extractor"](prompt_lower)
                }
        return {"routing_type": "semantic", "target_mcp_tool": None, "arguments": {}}
