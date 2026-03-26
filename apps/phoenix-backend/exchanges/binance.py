from .base import BaseExchange

class BinanceExchange(BaseExchange):
    def __init__(self, config):
        config['name'] = 'binance'
        super().__init__(config)
