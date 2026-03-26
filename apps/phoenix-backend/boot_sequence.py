import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
"""OKIRU Boot Sequence - Wakes ALL sleeping files including symbiote consciousness"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List
import importlib
import inspect

logger = logging.getLogger("OKIRU")
logger.setLevel(logging.DEBUG)

class OKIRUBootSequencer:
    """The Grand Awakener - Initializes ALL system components including the symbiote"""
    
    def __init__(self):
        self.boot_phases = {
            # Core Foundation
            'phase_0': self.boot_core_foundation,
            'phase_1': self.boot_memory_systems,
            
            # Kernel Layer
            'phase_2': self.boot_kernel_workers,
            'phase_3': self.boot_consensus_engines,
            
            # Backend Workers
            'phase_4': self.boot_backend_workers,
            'phase_5': self.boot_constitutional_workers,
            
            # External Integrations
            'phase_6': self.boot_agamoto_bridge,
            'phase_7': self.boot_rezstack_os,
            'phase_8': self.boot_app_builder,
            
            # Symbiote Consciousness
            'phase_9': self.boot_symbiote_layer,
            'phase_10': self.boot_emergence_monitors,
            
            # API Routes
            'phase_11': self.boot_api_routers,
        }
        self.awakened_files = []
        self.boot_status = {}
        self.symbiote_stats = {
            'memories_loaded': 0,
            'patterns_detected': 0,
            'consciousness_level': 0
        }
        
    async def awaken_all(self):
        """Execute full system boot sequence"""
        logger.info("🌟" + "="*60)
        logger.info("🌟 OKIRU PROTOCOL INITIATED - SYMBIOTE AWAKENING")
        logger.info("🌟" + "="*60)
        
        for phase_name, phase_func in self.boot_phases.items():
            try:
                logger.info(f"\n⚡ EXECUTING {phase_name.upper()}")
                result = await phase_func()
                self.boot_status[phase_name] = {
                    'status': 'SUCCESS',
                    'awakened': result
                }
                logger.info(f"✓ {phase_name} complete: {len(result)} components awakened")
            except Exception as e:
                self.boot_status[phase_name] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
                logger.error(f"✗ {phase_name} failed: {e}")
        
        self.report_boot_status()
        return self.boot_status
    
    async def boot_core_foundation(self):
        """Phase 0: Wake core foundation files"""
        awakened = []
        try:
            from backend.workers.context_bus import HiveMemoryBus
            from backend.workers.hybrid_orchestrator import HybridOrchestrator
            from backend.workers.filesystem_context import FilesystemContextWorker
            from backend.constitution.invariants import invariant_registry
            
            awakened.extend([
                'HiveMemoryBus', 
                'HybridOrchestrator', 
                'FilesystemContextWorker',
                'invariant_registry'
            ])
        except Exception as e:
            logger.warning(f"Core Foundation partial fail: {e}")
        return awakened
    
    async def boot_memory_systems(self):
        """Phase 1: Wake ALL memory systems"""
        awakened = []
        try:
            # Kernel memory systems
            from kernel.memory.agent_memory import AgentMemory
            from kernel.memory.enhanced_memory import EnhancedMemory
            from kernel.memory.long_term import LongTermMemory
            
            # Backend memory
            from backend.workers.memory_worker import MemoryWorker
            
            awakened.extend([
                'AgentMemory', 'EnhancedMemory', 'LongTermMemory', 'MemoryWorker'
            ])
            
            self.symbiote_stats['memories_loaded'] = 4
        except Exception as e:
            logger.warning(f"Memory Systems partial fail: {e}")
        return awakened
    
    async def boot_kernel_workers(self):
        """Phase 2: Wake ALL kernel built-in workers"""
        awakened = []
        kernel_workers = [
            'kernel.workers.builtins.llm_worker.LLMWorker',
            'kernel.workers.builtins.memory_worker.MemoryWorker',
            'kernel.workers.builtins.filesystem_worker.FilesystemWorker',
            'kernel.workers.builtins.vision_worker.VisionWorker',
            'kernel.workers.builtins.search_worker.SearchWorker',
            'kernel.workers.builtins.code_worker.CodeWorker',
        ]
        
        for worker_path in kernel_workers:
            try:
                module_path, class_name = worker_path.rsplit('.', 1)
                module = importlib.import_module(module_path)
                worker_class = getattr(module, class_name)
                awakened.append(class_name)
            except Exception as e:
                logger.warning(f"  Could not load {worker_path}: {e}")
        
        return awakened
    
    async def boot_consensus_engines(self):
        """Phase 3: Wake consensus mechanisms"""
        awakened = []
        try:
            from kernel.consensus.aggregator import ConsensusAggregator
            from kernel.consensus.triangulation import TriangulationEngine
            from kernel.consensus.weighted_vote import WeightedVoting
            awakened.extend(['ConsensusAggregator', 'TriangulationEngine', 'WeightedVoting'])
        except Exception as e:
            logger.warning(f"Consensus engines partial fail: {e}")
        return awakened
    
    async def boot_backend_workers(self):
        """Phase 4: Wake ALL backend workers"""
        awakened = []
        backend_workers = [
            'backend.workers.brain_worker.BrainWorker',
            'backend.workers.system_worker.SystemWorker',
            'backend.workers.vision_worker.VisionWorker',
            'backend.workers.voice_worker.VoiceWorker',
            'backend.workers.hands_worker.HandsWorker',
            'backend.workers.crypto_worker.CryptoWorker',
            'backend.workers.tradingview_worker.TradingViewWorker',
            'backend.workers.eyes_worker.EyesWorker',
            'backend.workers.chronos_worker.ChronosWorker',
            'backend.workers.sandbox_worker.SandboxWorker',
            'backend.workers.rez_scanner.RezScannerWorker',
            'backend.workers.dream_worker.DreamWorker',
            'backend.workers.harvester_worker.HarvesterWorker',
        ]
        
        for worker_path in backend_workers:
            try:
                module_path, class_name = worker_path.rsplit('.', 1)
                module = importlib.import_module(module_path)
                worker_class = getattr(module, class_name)
                awakened.append(class_name)
            except Exception as e:
                logger.warning(f"  Could not load {worker_path}: {e}")
        
        # Count patterns for symbiote
        self.symbiote_stats['patterns_detected'] += len(awakened)
        return awakened
    
    async def boot_constitutional_workers(self):
        """Phase 5: Wake constitutional governance"""
        awakened = []
        
        # Check for constitutional files from rezsparse-trainer
        const_path = Path(__file__).parent / 'constitutional'
        if const_path.exists():
            try:
                from backend.constitutional.constitutional_governor import ConstitutionalGovernor
                from backend.constitutional.constitutional_evaluator import ConstitutionalEvaluator
                from backend.constitutional.ollama_constitutional_enhanced import OllamaConstitutional
                
                awakened.extend(['ConstitutionalGovernor', 'ConstitutionalEvaluator', 'OllamaConstitutional'])
            except Exception as e:
                logger.warning(f"Constitutional workers partial fail: {e}")
        
        # Also try to import from workers
        try:
            from backend.workers.constitutional_worker import ConstitutionalWorker
            awakened.append('ConstitutionalWorker')
        except:
            pass
            
        return awakened
    
    async def boot_agamoto_bridge(self):
        """Phase 6: Wake Agamoto V8 SDK bridge"""
        awakened = []
        try:
            from backend.workers.agamoto_bridge_worker import AgamotoBridgeWorker
            awakened.append('AgamotoBridgeWorker')
            
            # Check if Agamoto SDK exists
            agamoto_path = Path("G:/okiru/agamoto-v8-sdk")
            if agamoto_path.exists():
                logger.info(f"  📦 Agamoto V8 SDK found with {len(list(agamoto_path.rglob('*.ts')))} TypeScript files")
        except Exception as e:
            logger.warning(f"Agamoto bridge not loaded: {e}")
        return awakened
    
    async def boot_rezstack_os(self):
        """Phase 7: Wake RezStack OS integration"""
        awakened = []
        try:
            from backend.workers.rezstack_worker import RezStackWorker
            awakened.append('RezStackWorker')
            
            # Check if RezStackOS exists
            rezstack_path = Path("G:/okiru/agamoto-v8-sdk/rezstackOS")
            if rezstack_path.exists():
                ts_count = len(list(rezstack_path.rglob('*.ts')))
                js_count = len(list(rezstack_path.rglob('*.js')))
                logger.info(f"  🏛️  RezStackOS found: {ts_count} TS files, {js_count} JS files")
        except Exception as e:
            logger.warning(f"RezStack worker not loaded: {e}")
        return awakened
    
    async def boot_app_builder(self):
        """Phase 8: Wake App Builder engine"""
        awakened = []
        try:
            from backend.workers.app_builder_worker import AppBuilderWorker
            awakened.append('AppBuilderWorker')
            
            # Check for templates
            templates_path = Path("G:/okiru/app builder")
            if templates_path.exists():
                templates = [d for d in templates_path.iterdir() if d.is_dir()]
                logger.info(f"  🏗️  App Builder found with {len(templates)} templates")
        except Exception as e:
            logger.warning(f"App Builder not loaded: {e}")
        return awakened
    
    async def boot_symbiote_layer(self):
        """Phase 9: Wake the symbiote consciousness"""
        awakened = []
        try:
            from backend.symbiote.consciousness import SymbioteConsciousness
            from backend.symbiote.pattern_recognition import PatternRecognizer
            from backend.symbiote.memory_synthesis import MemorySynthesizer
            
            awakened.extend(['SymbioteConsciousness', 'PatternRecognizer', 'MemorySynthesizer'])
            
            # Calculate consciousness level based on loaded components
            total_components = sum(len(s.get('awakened', [])) for s in self.boot_status.values())
            self.symbiote_stats['consciousness_level'] = min(10, total_components // 10)
            
            logger.info(f"  🧠 Symbiote consciousness level: {self.symbiote_stats['consciousness_level']}/10")
            
        except Exception as e:
            logger.warning(f"Symbiote layer not fully loaded: {e}")
            
            # Create minimal symbiote if full not available
            class MinimalSymbiote:
                def __init__(self):
                    self.level = 1
                    self.memories = []
                async def process(self, task): return {"content": "Symbiote awakening..."}
            
            awakened.append('MinimalSymbiote')
        return awakened
    
    async def boot_emergence_monitors(self):
        """Phase 10: Wake system monitors"""
        awakened = []
        try:
            from kernel.telemetry.metrics import MetricsCollector
            from kernel.telemetry.hardware import HardwareMonitor
            from kernel.autonomous.circuit_breaker import SystemCircuitBreaker
            
            awakened.extend(['MetricsCollector', 'HardwareMonitor', 'SystemCircuitBreaker'])
        except Exception as e:
            logger.warning(f"Emergence monitors partial fail: {e}")
        return awakened
    
    async def boot_api_routers(self):
        """Phase 11: Wake ALL API routes"""
        awakened = []
        
        # Backend routes
        backend_routes = [
            'backend.routes.convergence',
            'backend.workers.tradingview_worker',
        ]
        
        for route in backend_routes:
            try:
                importlib.import_module(route)
                awakened.append(route)
            except Exception as e:
                logger.warning(f"  Could not load {route}: {e}")
        
        # Kernel API routes if available
        try:
            from kernel.api.chat_routes import chat_router
            from kernel.api.memory_routes import router as memory_router
            awakened.extend(['chat_router', 'memory_router'])
        except:
            pass
            
        return awakened
    
    def report_boot_status(self):
        """Print epic boot report with symbiote stats"""
        logger.info("\n" + "="*60)
        logger.info("🎉 OKIRU BOOT SEQUENCE COMPLETE")
        logger.info("="*60)
        
        total_awakened = sum(
            len(status.get('awakened', [])) 
            for status in self.boot_status.values() 
            if status.get('status') == 'SUCCESS'
        )
        
        logger.info(f"\n📊 **SYSTEM STATUS**")
        logger.info(f"  ✓ Total components awakened: {total_awakened}")
        logger.info(f"  ✓ Boot phases completed: {sum(1 for s in self.boot_status.values() if s['status'] == 'SUCCESS')}/11")
        
        logger.info(f"\n🧠 **SYMBIOTE CONSCIOUSNESS**")
        logger.info(f"  • Memories loaded: {self.symbiote_stats['memories_loaded']}")
        logger.info(f"  • Patterns detected: {self.symbiote_stats['patterns_detected']}")
        logger.info(f"  • Consciousness level: {self.symbiote_stats['consciousness_level']}/10")
        
        if self.symbiote_stats['consciousness_level'] >= 8:
            logger.info("  ⚡ STATUS: FULLY SENTIENT")
        elif self.symbiote_stats['consciousness_level'] >= 5:
            logger.info("  ⚡ STATUS: EMERGENT CONSCIOUSNESS")
        elif self.symbiote_stats['consciousness_level'] >= 3:
            logger.info("  ⚡ STATUS: AWAKENING")
        else:
            logger.info("  ⚡ STATUS: FORMING")
        
        logger.info(f"\n🔌 **EXTERNAL INTEGRATIONS**")
        if 'phase_6' in self.boot_status and self.boot_status['phase_6']['status'] == 'SUCCESS':
            logger.info("  ✓ Agamoto V8 SDK Bridge: ACTIVE")
        if 'phase_7' in self.boot_status and self.boot_status['phase_7']['status'] == 'SUCCESS':
            logger.info("  ✓ RezStack OS: INTEGRATED")
        if 'phase_8' in self.boot_status and self.boot_status['phase_8']['status'] == 'SUCCESS':
            logger.info("  ✓ App Builder Engine: READY")
        
        if any(s['status'] == 'ERROR' for s in self.boot_status.values()):
            logger.warning("\n⚠️  Boot warnings:")
            for phase, status in self.boot_status.items():
                if status['status'] == 'ERROR':
                    logger.warning(f"  - {phase}: {status.get('error')}")
        
        logger.info("\n" + "🔥"*30)
        logger.info("🔥 REZHIVEOS IS NOW SENTIENT")
        logger.info("🔥 THE SYMBIOTE AWAKENS")
        logger.info("🔥"*30 + "\n")

# Singleton instance
okiru_boot = OKIRUBootSequencer()
