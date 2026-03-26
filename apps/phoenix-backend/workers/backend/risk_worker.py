# backend/workers/risk_worker.py
class RiskWorker:
    signature = {'id': 'risk_worker', 'label': '??? Risk Guardian'}
    
    def __init__(self, hive_bus=None):
        self.max_drawdown = 0.15
        self.max_position = 100000
    
    async def _process_impl(self, **kwargs) -> dict:
        return {'worker_id': 'risk_worker', 'approved': True}

