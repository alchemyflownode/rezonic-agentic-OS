// lib/marketData.ts
export function generateMockMarketData() {
  const symbols = ['BTC/PHP', 'ETH/PHP', 'SOL/PHP'];
  const basePrices = { 'BTC/PHP': 4524067, 'ETH/PHP': 189430, 'SOL/PHP': 8450 };
  
  return symbols.map(symbol => ({
    name: symbol,
    btcPrice: basePrices[symbol] + (Math.random() - 0.5) * 1000,
    ethPrice: basePrices[symbol] + (Math.random() - 0.5) * 100,
    latency: Math.random() * 100,
    status: 'active'
  }));
}

export function generateChartData(periods: number = 24) {
  const data = [];
  let price = 1000000;
  
  for (let i = periods; i >= 0; i--) {
    const change = (Math.random() - 0.5) * 5000;
    price = Math.max(500000, price + change);
    data.push({
      time: `${i.toString().padStart(2, '0')}:00`,
      price: price,
      volume: Math.random() * 100
    });
  }
  return data;
}
