# register_workers.py
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WORKER_REGISTRATION")

def register_all_workers():
    """Register all workers with the system"""
    
    workers_dir = Path("workers")
    sys.path.insert(0, str(workers_dir))
    
    # Import all worker modules
    worker_modules = {}
    
    # List of all worker files
    worker_files = [
        "agamato_bridge_worker",
        "apex_worker",
        "app_builder_worker",
        "audio_worker",
        "backtest_engine",
        "backtest_worker",
        "brain_worker",
        "canvas_worker",
        "chronos_worker",
        "constitutional_council_fixed",
        "constitutional_evaluator",
        "constitutional_governor",
        "constitutional_router",
        "constitutional_worker",
        "context_bus",
        "core",
        "cortex_worker",
        "crypto_worker",
        "dream_worker",
        "entropy_worker",
        "evolution_worker",
        "execution_worker",
        "eyes_worker",
        "filesystem_context",
        "file_doctor_worker",
        "forex_worker",
        "hands_worker",
        "harvester_worker",
        "hybrid_orchestrator",
        "jurisdiction_scanner",
        "memory_worker",
        "mock_trader",
        "ollama_constitutional_enhanced",
        "paper_trader_worker",
        "pc_hive_memory",
        "ps1_router",
        "registry",
        "registry_orchestrator",
        "rezstack_worker",
        "rez_scanner",
        "risk_worker",
        "sandbox_worker",
        "sce_compiler",
        "simple_test_worker",
        "strategy_evolver",
        "system_worker",
        "techdebt_scanner",
        "test_worker",
        "tradingview_worker",
        "validator_worker",
        "vision_worker",
        "voice_worker"
    ]
    
    for module_name in worker_files:
        try:
            module = __import__(module_name)
            worker_modules[module_name] = module
            logger.info(f"✅ Registered: {module_name}")
        except Exception as e:
            logger.error(f"❌ Failed to register {module_name}: {e}")
    
    logger.info(f"📊 Total registered: {len(worker_modules)}")
    return worker_modules

if __name__ == "__main__":
    register_all_workers()
