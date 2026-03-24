# graceful_shutdown.py
"""Graceful shutdown handler for Phoenix Kernel"""

import signal
import asyncio
import sys
import logging
import time
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("phoenix.graceful")

class GracefulShutdown:
    """Handle graceful shutdown of the kernel"""
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.shutdown_requested = False
        self.shutdown_start_time = None
        self._tasks = []
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Graceful shutdown handler initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        if not self.shutdown_requested:
            self.shutdown_requested = True
            self.shutdown_start_time = time.time()
            logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self._shutdown())
        else:
            logger.warning("Force shutdown...")
            sys.exit(1)
    
    async def _shutdown(self):
        """Execute graceful shutdown sequence"""
        try:
            # Step 1: Stop accepting new requests
            logger.info("Step 1: Stopping new requests...")
            if hasattr(self.kernel, 'accepting_requests'):
                self.kernel.accepting_requests = False
            
            # Step 2: Complete pending tasks
            logger.info("Step 2: Completing pending tasks...")
            pending = self._get_pending_tasks()
            if pending:
                logger.info(f"  Waiting for {len(pending)} pending tasks...")
                await asyncio.wait_for(asyncio.gather(*pending, return_exceptions=True), timeout=10)
            
            # Step 3: Save state
            logger.info("Step 3: Saving system state...")
            await self._save_state()
            
            # Step 4: Close connections
            logger.info("Step 4: Closing connections...")
            await self._close_connections()
            
            # Step 5: Final cleanup
            logger.info("Step 5: Final cleanup...")
            await self._cleanup()
            
            duration = time.time() - self.shutdown_start_time
            logger.info(f"✅ Graceful shutdown complete in {duration:.2f}s")
            sys.exit(0)
            
        except asyncio.TimeoutError:
            logger.error("Shutdown timeout - forcing exit")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
            sys.exit(1)
    
    def _get_pending_tasks(self):
        """Get list of pending tasks"""
        tasks = []
        
        # Check kernel for pending tasks
        if hasattr(self.kernel, 'pending_tasks'):
            tasks.extend(self.kernel.pending_tasks)
        
        return tasks
    
    async def _save_state(self):
        """Save current system state"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "drift_chain_length": len(getattr(self.kernel, 'drift_chain', [])),
            "workers": len(getattr(self.kernel, 'workers', {})),
            "memory": len(getattr(self.kernel, 'memories', {})) if hasattr(self.kernel, 'memories') else 0
        }
        
        # Save to file
        try:
            import json
            state_file = Path("data/shutdown_state.json")
            state_file.parent.mkdir(exist_ok=True)
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.info(f"  State saved to {state_file}")
        except Exception as e:
            logger.error(f"  Failed to save state: {e}")
    
    async def _close_connections(self):
        """Close all active connections"""
        # Close HTTP client
        if hasattr(self.kernel, 'http_client') and self.kernel.http_client:
            await self.kernel.http_client.aclose()
            logger.info("  HTTP client closed")
    
    async def _cleanup(self):
        """Final cleanup tasks"""
        # Clear any temporary files
        try:
            import shutil
            temp_dir = Path("data/temp")
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                logger.info("  Temporary files cleaned")
        except Exception as e:
            logger.error(f"  Cleanup error: {e}")
    
    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress"""
        return self.shutdown_requested

__all__ = ['GracefulShutdown']