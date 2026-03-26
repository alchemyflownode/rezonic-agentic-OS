# backend/kernel/autonomous_loop.py
"""
The Mind of RezHive - Continuous Cognition Loop
"""
import asyncio
import logging
import time
import random
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("rez-hive-mind")

class AutonomousMind:
    """
    The continuous cognition engine that gives RezHive life.
    Runs 24/7, thinking, acting, and learning.
    """
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.running = False
        self.cycle_count = 0
        self.last_thought = None
        self.goals = []
        self.metrics = {
            'cycles': 0,
            'actions_taken': 0,
            'errors': 0,
            'last_cycle_time': 0
        }
        
    async def start(self):
        """Start the autonomous mind"""
        logger.info("🧠 AUTONOMOUS MIND INITIALIZED")
        logger.info("═" * 60)
        self.running = True
        
        # Initial system scan
        await self._system_scan()
        
        # Main cognition loop
        while self.running:
            try:
                cycle_start = time.time()
                self.cycle_count += 1
                
                # PHASE 1: OBSERVE - Gather system state
                state = await self._observe()
                
                # PHASE 2: THINK - Process with Brain
                thought = await self._think(state)
                self.last_thought = thought
                
                # PHASE 3: ACT - Execute decisions
                if thought and thought.get('action'):
                    await self._act(thought['action'])
                
                # PHASE 4: LEARN - Store in memory
                await self._learn(state, thought)
                
                # Update metrics
                cycle_time = time.time() - cycle_start
                self.metrics['cycles'] = self.cycle_count
                self.metrics['last_cycle_time'] = cycle_time
                
                # Log heartbeat every 10 cycles
                if self.cycle_count % 10 == 0:
                    logger.info(f"🧠 Mind heartbeat: {self.cycle_count} cycles | {cycle_time:.2f}s")
                
                # Rest between cycles (prevents CPU hogging)
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Mind error: {e}")
                self.metrics['errors'] += 1
                await asyncio.sleep(5)
    
    async def _observe(self) -> Dict[str, Any]:
        """Observe system state from all sources"""
        state = {
            'timestamp': time.time(),
            'workers': len(self.kernel.workers),
            'memory_size': 0,
            'system_load': 0,
            'market_data': None,
            'needs_attention': []
        }
        
        # Check memory bus
        bus = self.kernel.components.get('hive_bus')
        if bus and hasattr(bus, 'memories'):
            state['memory_size'] = len(bus.memories)
        
        # Check for pending tasks
        for name, worker in self.kernel.workers.items():
            if hasattr(worker, 'needs_attention'):
                if await worker.needs_attention():
                    state['needs_attention'].append(name)
        
        return state
    
    async def _think(self, state: Dict) -> Optional[Dict]:
        """Process state through BrainWorker to decide action"""
        brain = self.kernel.workers.get('brain')
        if not brain:
            return None
        
        # Construct cognition prompt
        prompt = f"""
        [AUTONOMOUS COGNITION CYCLE {self.cycle_count}]
        Time: {datetime.now().isoformat()}
        
        System State:
        - Active Workers: {state['workers']}
        - Memory Objects: {state['memory_size']}
        - Needs Attention: {', '.join(state['needs_attention']) if state['needs_attention'] else 'None'}
        
        Current Goals:
        {self._format_goals()}
        
        Your task:
        1. Analyze if any worker needs attention
        2. Consider if market conditions require action
        3. Check if memory needs optimization
        4. Decide if new strategies should be evolved
        
        Respond with JSON:
        {{
            "action": "ACTION_NAME",
            "target": "worker_name",
            "reasoning": "why this action",
            "parameters": {{}}
        }}
        
        Available Actions:
        - SCAN: Run scanner worker
        - CHECK_MARKET: Update crypto prices
        - EVOLVE: Run strategy evolution
        - OPTIMIZE_MEMORY: Clean old memories
        - IDLE: No action needed
        """
        
        try:
            result = await brain.process(prompt)
            
            # Parse response (handle both string and dict returns)
            if isinstance(result, dict):
                content = result.get('content', '{}')
            else:
                content = str(result)
            
            # Try to extract JSON
            import json
            import re
            
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            return {'action': 'IDLE', 'reasoning': 'No structured response'}
            
        except Exception as e:
            logger.error(f"Thinking error: {e}")
            return {'action': 'IDLE', 'reasoning': f'Error: {e}'}
    
    async def _act(self, action: Dict):
        """Execute the decided action"""
        action_name = action.get('action', 'IDLE')
        target = action.get('target')
        params = action.get('parameters', {})
        
        if action_name == 'IDLE' or not target:
            return
        
        logger.info(f"⚡ Mind acting: {action_name} on {target}")
        
        worker = self.kernel.workers.get(target)
        if not worker:
            logger.warning(f"Target worker {target} not found")
            return
        
        try:
            if action_name == 'SCAN':
                if hasattr(worker, 'process'):
                    await worker.process('/scan workspace')
                    
            elif action_name == 'CHECK_MARKET':
                if hasattr(worker, 'process'):
                    await worker.process('/price BTC/USDT')
                    
            elif action_name == 'EVOLVE':
                if hasattr(worker, 'process'):
                    await worker.process('/evolve 1')
            
            self.metrics['actions_taken'] += 1
            
            # Store action in memory
            bus = self.kernel.components.get('hive_bus')
            if bus:
                bus.store(
                    f"mind_action_{int(time.time())}",
                    {
                        'action': action_name,
                        'target': target,
                        'params': params,
                        'timestamp': time.time()
                    },
                    tags=['mind', 'action', action_name.lower()]
                )
                
        except Exception as e:
            logger.error(f"Action failed: {e}")
    
    async def _learn(self, state: Dict, thought: Optional[Dict]):
        """Store the cycle in memory for future reference"""
        bus = self.kernel.components.get('hive_bus')
        if not bus:
            return
        
        cycle_record = {
            'cycle': self.cycle_count,
            'timestamp': time.time(),
            'state': state,
            'thought': thought,
            'metrics': self.metrics.copy()
        }
        
        bus.store(
            f"mind_cycle_{self.cycle_count}",
            cycle_record,
            tags=['mind', 'cycle', 'autonomous']
        )
    
    def _format_goals(self) -> str:
        """Format current goals for the prompt"""
        if not self.goals:
            return "No active goals"
        
        return '\n'.join([f"- {g}" for g in self.goals[-3:]])
    
    async def stop(self):
        """Gracefully stop the mind"""
        logger.info("🧠 Autonomous mind shutting down...")
        self.running = False

# ==========================================
# Add to main_ps1.py initialization
# ==========================================
"""
In RezHivePS1.initialize(), add:

# Phase 3: Autonomous Mind
logger.info("\n🧠 PHASE 3: Awakening Autonomous Mind")
from backend.kernel.autonomous_loop import AutonomousMind
self.mind = AutonomousMind(self)
asyncio.create_task(self.mind.start())
logger.info("  ✅ Mind initialized and running")
"""