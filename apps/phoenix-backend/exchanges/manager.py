import yaml
import os
import logging
from .binance import BinanceExchange

logger = logging.getLogger(__name__)

class ExchangeManager:
    def __init__(self, config_path="config/exchanges.yaml"):
        self.exchanges = {}
        self.load_config(config_path)
        
    def load_config(self, path):
        if not os.path.exists(path):
            logger.warning(f"Config not found: {path}")
            return
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
            
        ex_config = config.get('exchanges', {})
        self.mode = config.get('mode', 'testnet')
        
        for name, cfg in ex_config.items():
            if not cfg.get('enabled'): continue
            cfg['testnet'] = (self.mode == 'testnet')
            if name == 'binance':
                self.exchanges[name] = BinanceExchange(cfg)
            # Add other exchanges dynamically here
        logger.info(f"✅ Loaded {len(self.exchanges)} exchange configs.")
        
    async def connect_all(self):
        for name, ex in self.exchanges.items():
            await ex.connect()
