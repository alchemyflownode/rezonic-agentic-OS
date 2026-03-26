@app.get("/api/signal")
async def get_signal(pair: str = "BTC/USDT"):
    """Get trading signal for a pair - use ?pair=BTC/USDT"""
    # Simulate price movement
    if pair in prices:
        change = random.uniform(-0.02, 0.02)
        prices[pair] = prices[pair] * (1 + change)
    else:
        prices[pair] = 50000
    
    current_price = prices.get(pair, 50000)
    php_price = current_price * 58
    
    # Generate random but realistic signals
    rsi = random.uniform(20, 80)
    signal = 'HOLD'
    confidence = 0.5
    
    if rsi < 30:
        signal = 'BUY'
        confidence = 0.85
    elif rsi > 70:
        signal = 'SELL'
        confidence = 0.85
    
    return {
        'worker_id': 'mock_trader',
        'pair': pair,
        'signal': signal,
        'confidence': round(confidence, 2),
        'price_usd': round(current_price, 2),
        'price_php': round(php_price, 2),
        'indicators': {
            'rsi': round(rsi, 2),
            'trend': 'BULLISH' if rsi < 50 else 'BEARISH'
        },
        'timestamp': int(time.time() * 1000)
    }