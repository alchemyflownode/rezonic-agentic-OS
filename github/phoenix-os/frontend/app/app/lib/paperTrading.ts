export interface Trade {
  id: string;
  symbol: string;
  type: 'BUY' | 'SELL';
  amount: number;
  price: number;
  timestamp: number;
  status: 'pending' | 'completed' | 'cancelled';
  orderType: 'market' | 'limit';
  limitPrice?: number;
}

export interface Position {
  symbol: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
}

export interface Portfolio {
  balance: number;
  positions: Position[];
  totalValue: number;
  totalPnL: number;
  totalPnLPercent: number;
}

class PaperTradingService {
  private portfolio: Portfolio = {
    balance: 1000000,
    positions: [],
    totalValue: 1000000,
    totalPnL: 0,
    totalPnLPercent: 0
  };

  private trades: Trade[] = [];
  private botActive: boolean = false;
  private botInterval: NodeJS.Timeout | null = null;
  private mode: 'manual' | 'ai' | 'hybrid' = 'manual';

  private getCurrentPrice(symbol: string): number {
    const prices: Record<string, number> = {
      'BTC/PHP': 4524067 + (Math.random() - 0.5) * 50000,
      'ETH/PHP': 189430 + (Math.random() - 0.5) * 2000,
      'SOL/PHP': 8450 + (Math.random() - 0.5) * 100
    };
    return prices[symbol] || 0;
  }

  private updatePortfolio() {
    let totalValue = this.portfolio.balance;
    
    this.portfolio.positions = this.portfolio.positions.map(pos => {
      const currentPrice = this.getCurrentPrice(pos.symbol);
      const pnl = (currentPrice - pos.avgPrice) * pos.quantity;
      const pnlPercent = (pnl / (pos.avgPrice * pos.quantity)) * 100;
      
      totalValue += currentPrice * pos.quantity;
      
      return {
        ...pos,
        currentPrice,
        pnl,
        pnlPercent
      };
    });
    
    this.portfolio.totalValue = totalValue;
    this.portfolio.totalPnL = totalValue - 1000000;
    this.portfolio.totalPnLPercent = (this.portfolio.totalPnL / 1000000) * 100;
    
    return this.portfolio;
  }

  executeTrade(trade: Omit<Trade, 'id' | 'timestamp' | 'status'>): { success: boolean; message: string; trade?: Trade } {
    const currentPrice = this.getCurrentPrice(trade.symbol);
    const totalCost = trade.amount * currentPrice;
    
    if (trade.type === 'BUY') {
      if (this.portfolio.balance < totalCost) {
        return { success: false, message: 'Insufficient balance' };
      }
      
      const existingPosition = this.portfolio.positions.find(p => p.symbol === trade.symbol);
      
      if (existingPosition) {
        const newQuantity = existingPosition.quantity + trade.amount;
        const newAvgPrice = ((existingPosition.avgPrice * existingPosition.quantity) + (currentPrice * trade.amount)) / newQuantity;
        existingPosition.quantity = newQuantity;
        existingPosition.avgPrice = newAvgPrice;
      } else {
        this.portfolio.positions.push({
          symbol: trade.symbol,
          quantity: trade.amount,
          avgPrice: currentPrice,
          currentPrice: currentPrice,
          pnl: 0,
          pnlPercent: 0
        });
      }
      
      this.portfolio.balance -= totalCost;
      
    } else {
      const position = this.portfolio.positions.find(p => p.symbol === trade.symbol);
      
      if (!position) {
        return { success: false, message: 'No position to sell' };
      }
      
      if (position.quantity < trade.amount) {
        return { success: false, message: 'Insufficient position size' };
      }
      
      position.quantity -= trade.amount;
      this.portfolio.balance += totalCost;
      
      if (position.quantity === 0) {
        this.portfolio.positions = this.portfolio.positions.filter(p => p.symbol !== trade.symbol);
      }
    }
    
    const newTrade: Trade = {
      ...trade,
      id: Date.now().toString(),
      timestamp: Date.now(),
      status: 'completed',
      price: currentPrice
    };
    
    this.trades.unshift(newTrade);
    this.updatePortfolio();
    
    const message = trade.type + ' ' + trade.amount + ' ' + trade.symbol + ' at ₱' + currentPrice.toLocaleString();
    
    return { 
      success: true, 
      message: message,
      trade: newTrade
    };
  }

  private aiTradingLogic() {
    const symbols = ['BTC/PHP', 'ETH/PHP', 'SOL/PHP'];
    
    symbols.forEach(symbol => {
      const price = this.getCurrentPrice(symbol);
      const position = this.portfolio.positions.find(p => p.symbol === symbol);
      const isBullish = Math.random() > 0.5;
      const shouldBuy = isBullish && (!position || position.quantity < 0.1);
      const shouldSell = !isBullish && position && position.quantity > 0;
      
      if (shouldBuy && this.portfolio.balance > price * 0.01) {
        const amount = Math.min(0.01, this.portfolio.balance / price);
        this.executeTrade({
          symbol: symbol,
          type: 'BUY',
          amount: amount,
          orderType: 'market'
        });
      } else if (shouldSell && position) {
        const amount = Math.min(position.quantity, 0.01);
        this.executeTrade({
          symbol: symbol,
          type: 'SELL',
          amount: amount,
          orderType: 'market'
        });
      }
    });
  }

  startBot() {
    if (this.botInterval) return;
    this.botActive = true;
    this.botInterval = setInterval(() => {
      if (this.mode === 'ai' || this.mode === 'hybrid') {
        this.aiTradingLogic();
      }
    }, 10000);
  }

  stopBot() {
    if (this.botInterval) {
      clearInterval(this.botInterval);
      this.botInterval = null;
    }
    this.botActive = false;
  }

  setMode(mode: 'manual' | 'ai' | 'hybrid') {
    this.mode = mode;
    if (mode === 'ai' || mode === 'hybrid') {
      this.startBot();
    } else {
      this.stopBot();
    }
  }

  getPortfolio() {
    return this.updatePortfolio();
  }

  getTrades() {
    return this.trades;
  }

  getBotStatus() {
    return {
      active: this.botActive,
      mode: this.mode
    };
  }

  resetPortfolio() {
    this.portfolio = {
      balance: 1000000,
      positions: [],
      totalValue: 1000000,
      totalPnL: 0,
      totalPnLPercent: 0
    };
    this.trades = [];
    this.updatePortfolio();
  }
}

export const paperTrading = new PaperTradingService();
