"""Paper Trader Worker - WITH STREAMING"""
import logging

logger = logging.getLogger(__name__)

class PaperTraderWorker:
    def __init__(self, hive_bus=None):
        self.hive_bus = hive_bus
        self.balance = 10000.0
        logger.info("  💹 PaperTraderWorker initialized")
    
    async def health_check(self):
        return {"healthy": True, "worker": "paper_trader", "balance": self.balance}
    
    async def process(self, task):
        return {"content": f"Balance: ${self.balance:.2f}"}
    
    async def process_stream(self, task):
        """Streaming version for paper trader"""
        yield f"📊 Paper Trader processing: {task}\n"
        yield f"Current balance: ${self.balance:.2f}\n"
        yield f"Open positions: 0\n"
        yield f"Today's P&L: $0.00\n"
