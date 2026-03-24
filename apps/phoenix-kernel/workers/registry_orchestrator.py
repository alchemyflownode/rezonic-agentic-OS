import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class RegistryOrchestrator:
    def __init__(self, vfs_base_path: str = "./hive_vfs"):
        """Initialize the Registry-Driven Grounding engine"""
        self.base_path = Path(vfs_base_path).resolve()
        
        # Ensure our config directories exist in the VFS
        self.agents_dir = self.base_path / "knowledge" / "agents"
        self.tools_dir = self.base_path / "tools"
        
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        
        self._init_core_definitions()

    def _init_core_definitions(self):
        """Bootstrap the system with FULL default declarative agent configs"""
        agents =[
            {
                "name": "core_researcher", "role": "Deep Web Analysis", 
                "model": "qwen2.5-coder:14b", "allowed_tools":["vfs_ls", "search_web"],
                "system_prompt": "You are the hive's eyes. Gather context efficiently without drift."
            },
            {
                "name": "data_analyst", "role": "CSV/Rental Data Parsing", 
                "model": "qwen2.5-coder:14b", "allowed_tools": ["vfs_cat"],
                "system_prompt": "Analyze datasets and extract actionable financial insights."
            },
            {
                "name": "code_executor", "role": "Python Sandbox", 
                "model": "qwen2.5-coder:14b", "allowed_tools": ["execute_code"],
                "system_prompt": "Write and execute perfect Python scripts."
            },
            {
                "name": "chronos_monitor", "role": "Background Tasks", 
                "model": "qwen2.5-coder:14b", "allowed_tools":[],
                "system_prompt": "Monitor real-time events and trigger alerts."
            }
        ]
        
        for agent in agents:
            agent_file = self.agents_dir / f"{agent['name']}.json"
            if not agent_file.exists():
                with open(agent_file, "w", encoding="utf-8") as f:
                    json.dump(agent, f, indent=4)

    def load_agent_network(self) -> dict:
        """Dynamically load all agent profiles from the VFS"""
        network = {}
        for config_file in self.agents_dir.glob("*.json"):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    agent_data = json.load(f)
                    network[agent_data.get("name", config_file.stem)] = agent_data
            except Exception as e:
                logger.error(f"Failed to load agent {config_file.name}: {e}")
        return network

    def get_agent_tools(self, agent_name: str) -> list:
        """Governance: Return ONLY the tools this specific agent is allowed to use"""
        network = self.load_agent_network()
        agent = network.get(agent_name)
        if not agent:
            return []
        return agent.get("allowed_tools",[])

    async def process(self, task: str, memory_bus=None):
        """Process task â€“ auto-generated stub"""
        return {"content": f"Processed: {task[:50]}", "worker": self.name}
    
    async def health_check(self):
        """Return worker health status"""
        return {"worker": self.name, "status": "healthy", "timestamp": __import__('time').time()}


