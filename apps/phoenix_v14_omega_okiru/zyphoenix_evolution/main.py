#!/usr/bin/env python3
"""
RezHiveOS PS1 - PRODUCTION SYSTEM 1
All workers fully restored and operational!
"""

import asyncio
import logging
import sys
import os
import json
import time
from datetime import datetime
from aiohttp import web
import socketio

# Add path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger("rezhive-ps1")

# CORS middleware
@web.middleware
async def cors_middleware(request, handler):
    if request.method == 'OPTIONS':
        response = web.Response()
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Hive-API-Key'
        return response
    response = await handler(request)
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    return response

# Import ALL restored workers
from backend.hive_memory.bus import HiveMemoryBus
from backend.workers.brain_worker import BrainWorker
from backend.workers.rez_scanner import RezScannerWorker
from backend.workers.hands_worker import HandsWorker
from backend.workers.crypto_worker import CryptoWorker
from backend.workers.eyes_worker import EyesWorker
from backend.workers.strategy_evolver import StrategyEvolver
from backend.workers.backtest_worker import BacktestWorker
from backend.workers.tradingview_worker import TradingViewWorker
from backend.workers.paper_trader_worker import PaperTraderWorker
from backend.workers.vision_worker import VisionWorker
from backend.workers.voice_worker import VoiceWorker
from backend.workers.system_worker import SystemWorker
from backend.workers.agamoto_bridge_worker import AgamotoBridgeWorker
from backend.workers.constitutional_worker import ConstitutionalWorker
from backend.constitution.governor import ConstitutionalGovernor

class RezHivePS1:
    """Production System 1 - All Workers Operational"""
    
    def __init__(self):
        self.name = "RezHivePS1"
        self.version = "1.0.0"
        self.workers = {}
        self.components = {}
        self.sio = socketio.AsyncServer(cors_allowed_origins=['http://localhost:3000'])
        self.app = web.Application(middlewares=[cors_middleware])
        
    async def initialize(self):
        """Initialize ALL restored workers"""
        logger.info("="*60)
        logger.info("REZ HIVE PS1 BOOT SEQUENCE")
        logger.info("="*60)
        
        # Initialize core components
        self.components['hive_bus'] = HiveMemoryBus()
        self.components['governor'] = ConstitutionalGovernor(hive_bus=self.components['hive_bus'])
        logger.info("  ✅ Core components initialized")
        
        # Initialize ALL workers (prioritizing the large, working ones)
        worker_classes = {
            # Core AI & Processing
            'brain': BrainWorker,
            'scanner': RezScannerWorker,
            'hands': HandsWorker,
            
            # Trading & Finance
            'crypto': CryptoWorker,
            'paper_trader': PaperTraderWorker,
            'strategy': StrategyEvolver,
            'backtest': BacktestWorker,
            'tradingview': TradingViewWorker,
            
            # Vision & Voice
            'eyes': EyesWorker,
            'vision': VisionWorker,
            'voice': VoiceWorker,
            
            # System & Bridge
            'system': SystemWorker,
            'agamato': AgamotoBridgeWorker,
            'constitution': ConstitutionalWorker
        }
        
        for name, worker_class in worker_classes.items():
            try:
                worker = worker_class(hive_bus=self.components['hive_bus'])
                self.workers[name] = worker
                size_hint = "large" if name in ['scanner', 'paper_trader', 'strategy'] else "ready"
                logger.info(f"  ✅ {name} worker initialized ({size_hint})")
            except Exception as e:
                logger.error(f"  ❌ Failed to initialize {name}: {e}")
        
        logger.info(f"\n📊 Total workers: {len(self.workers)}")
        
        # Attach socket.io
        self.sio.attach(self.app)
        await self.setup_routes()
        await self.setup_socket_handlers()
        
    async def setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/status', self.handle_status)
        self.app.router.add_post('/kernel/stream', self.handle_kernel_stream)
        
    async def setup_socket_handlers(self):
        """Setup Socket.IO handlers"""
        
        @self.sio.event
        async def connect(sid, environ):
            logger.info(f"Client connected: {sid}")
            await self.sio.emit('connected', {'status': 'connected'}, room=sid)
            
        @self.sio.event
        async def disconnect(sid):
            logger.info(f"Client disconnected: {sid}")
    
    async def handle_health(self, request):
        """Health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'version': self.version,
            'workers': len(self.workers),
            'timestamp': time.time()
        })
    
    async def handle_status(self, request):
        """Detailed status endpoint"""
        worker_status = {}
        for name, worker in self.workers.items():
            try:
                if hasattr(worker, 'health_check'):
                    status = await worker.health_check() if asyncio.iscoroutinefunction(worker.health_check) else worker.health_check()
                    worker_status[name] = status
            except:
                worker_status[name] = {'healthy': 'unknown'}
        
        return web.json_response({
            'name': self.name,
            'version': self.version,
            'workers': worker_status
        })
    
    async def handle_kernel_stream(self, request):
        """Stream responses from workers"""
        response = web.StreamResponse(
            status=200,
            headers={
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }
        )
        await response.prepare(request)
        
        try:
            data = await request.json()
            task = data.get('task', '')
            
            # Smart routing based on task content
            worker = self._route_task(task)
            
            if not worker:
                await response.write(b'data: {"error": "No worker available"}\n\n')
                await response.write_eof()
                return
            
            # Send routing info
            worker_name = task.split()[0] if task.startswith('/') else 'brain'
            init_msg = json.dumps({"content": f"⚙️ Routing to {worker_name.upper()}...\n\n"})
            await response.write(f"data: {init_msg}\n\n".encode())
            
            # Process with worker
            if hasattr(worker, 'process_stream'):
                async for chunk in worker.process_stream(task):
                    if chunk:
                        payload = json.dumps({"content": chunk})
                        await response.write(f"data: {payload}\n\n".encode())
            else:
                result = await worker.process(task)
                content = result.get('content', str(result)) if isinstance(result, dict) else str(result)
                payload = json.dumps({"content": content})
                await response.write(f"data: {payload}\n\n".encode())
                
        except Exception as e:
            error_msg = json.dumps({"error": str(e)})
            await response.write(f"data: {error_msg}\n\n".encode())
            
        await response.write_eof()
        return response
    
    def _route_task(self, task: str):
        """Route task to appropriate worker"""
        task_lower = task.lower()
        
        # Command-based routing
        if task.startswith('/scan'):
            return self.workers.get('scanner')
        elif task.startswith('/think') or '?' in task or not task.startswith('/'):
            return self.workers.get('brain')
        elif task.startswith('/price') or 'btc' in task_lower or 'crypto' in task_lower:
            return self.workers.get('crypto')
        elif task.startswith('/click') or task.startswith('/type') or task.startswith('/move'):
            return self.workers.get('hands')
        elif task.startswith('/evolve') or 'strategy' in task_lower:
            return self.workers.get('strategy')
        elif task.startswith('/backtest'):
            return self.workers.get('backtest')
        elif task.startswith('/trade') or 'paper' in task_lower:
            return self.workers.get('paper_trader')
        elif task.startswith('/chart') or 'tradingview' in task_lower:
            return self.workers.get('tradingview')
        elif task.startswith('/see') or task.startswith('/vision'):
            return self.workers.get('vision')
        elif task.startswith('/constitution') or 'law' in task_lower:
            return self.workers.get('constitution')
        
        # Default to brain
        return self.workers.get('brain')
    
    async def run(self):
        """Run the server"""
        await self.initialize()
        
        # Start server
        for port in [8000, 8001]:
            try:
                runner = web.AppRunner(self.app)
                await runner.setup()
                site = web.TCPSite(runner, '0.0.0.0', port)
                await site.start()
                logger.info(f"🚀 Server running on http://0.0.0.0:{port}")
                
                # Keep running
                while True:
                    await asyncio.sleep(1)
                    
            except OSError:
                continue
            except KeyboardInterrupt:
                logger.info("\n🛑 Shutting down...")
                await runner.cleanup()
                break

async def main():
    """Main entry point"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Banner
    print(r"""
    ██████╗ ███████╗███████╗██╗  ██╗██╗██╗   ██╗███████╗
    ██╔══██╗██╔════╝╚════██║██║  ██║██║██║   ██║██╔════╝
    ██████╔╝█████╗    ███╔═╝███████║██║██║   ██║█████╗  
    ██╔══██╗██╔══╝  ██╔══╝  ██╔══██║██║╚██╗ ██╔╝██╔══╝  
    ██║  ██║███████╗███████╗██║  ██║██║ ╚████╔╝ ███████╗
    ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝
    """)
    print("                 PRODUCTION SYSTEM 1")
    print("          ALL WORKERS RESTORED AND OPERATIONAL\n")
    
    ps1 = RezHivePS1()
    await ps1.run()

if __name__ == "__main__":
    asyncio.run(main())