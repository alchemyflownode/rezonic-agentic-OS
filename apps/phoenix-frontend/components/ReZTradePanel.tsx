// D:\Rezonic_Agentic\apps\phoenix-frontend\components\ReZTradePanel.tsx
/**
 * ReZ Trader Main Trading Panel
 * Combines your existing components into one sovereign trading interface
 */

import React, { useState, useEffect } from 'react';
import { usePhoenixStore } from '../store/phoenixStore';
import { TradingViewChart } from './TradingViewChart';
import { PortfolioView } from './PortfolioView';
import { IntegrityPulse } from './IntegrityPulse';
import { ConstitutionPanel } from './ConstitutionPanel';

export const ReZTradePanel: React.FC = () => {
  const [symbol, setSymbol] = useState('EUR_USD');
  const [amount, setAmount] = useState(1000);
  const [stopLoss, setStopLoss] = useState('');
  const [takeProfit, setTakeProfit] = useState('');
  const [validationResult, setValidationResult] = useState<any>(null);
  
  const { 
    executeTrade, 
    portfolio, 
    killSwitch, 
    fetchPortfolio,
    socket 
  } = usePhoenixStore();
  
  // Subscribe to pulse updates
  useEffect(() => {
    if (!socket) return;
    
    socket.on('pulse_update', (data) => {
      console.log('Pulse update:', data);
    });
    
    return () => {
      socket.off('pulse_update');
    };
  }, [socket]);
  
  const handleTrade = async () => {
    if (killSwitch.active) {
      alert('🔴 Kill switch active - trades blocked');
      return;
    }
    
    const trade = {
      symbol,
      amount,
      price: 0, // Will be filled by market
      stop_loss: stopLoss ? parseFloat(stopLoss) : null,
      take_profit: takeProfit ? parseFloat(takeProfit) : null
    };
    
    // Execute trade
    const result = await executeTrade('buy', symbol, amount);
    
    if (result) {
      alert('✅ Trade executed constitutionally');
      await fetchPortfolio();
    } else {
      alert('❌ Trade blocked by constitution');
    }
  };
  
  return (
    <div className="rez-trade-panel" style={{
      display: 'grid',
      gridTemplateColumns: '1fr 400px',
      height: '100vh',
      gap: '20px',
      padding: '20px',
      background: '#0a0a0a',
      color: '#00ff00'
    }}>
      {/* Left: Chart Area */}
      <div style={{
        background: '#1a1a1a',
        borderRadius: '8px',
        padding: '20px',
        border: '1px solid #00ff00'
      }}>
        <h2 style={{ marginBottom: '20px' }}>📊 {symbol}</h2>
        <TradingViewChart symbol={symbol} />
      </div>
      
      {/* Right: Trading Controls */}
      <div style={{
        background: '#1a1a1a',
        borderRadius: '8px',
        padding: '20px',
        border: '1px solid #00ff00',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px'
      }}>
        {/* Pulse Score */}
        <IntegrityPulse />
        
        {/* Trade Form */}
        <div style={{
          background: '#0a0a0a',
          padding: '15px',
          borderRadius: '8px'
        }}>
          <h3>⚡ Execute Trade</h3>
          
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>Symbol</label>
            <input
              value={symbol}
              onChange={e => setSymbol(e.target.value.toUpperCase())}
              style={{
                width: '100%',
                padding: '8px',
                background: '#1a1a1a',
                border: '1px solid #00ff00',
                color: '#00ff00',
                borderRadius: '4px'
              }}
            />
          </div>
          
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>Amount (units)</label>
            <input
              type="number"
              value={amount}
              onChange={e => setAmount(parseFloat(e.target.value))}
              style={{
                width: '100%',
                padding: '8px',
                background: '#1a1a1a',
                border: '1px solid #00ff00',
                color: '#00ff00',
                borderRadius: '4px'
              }}
            />
          </div>
          
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>Stop Loss (optional)</label>
            <input
              type="number"
              value={stopLoss}
              onChange={e => setStopLoss(e.target.value)}
              placeholder="Auto-calculated from rules"
              style={{
                width: '100%',
                padding: '8px',
                background: '#1a1a1a',
                border: '1px solid #00ff00',
                color: '#00ff00',
                borderRadius: '4px'
              }}
            />
          </div>
          
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>Take Profit (optional)</label>
            <input
              type="number"
              value={takeProfit}
              onChange={e => setTakeProfit(e.target.value)}
              style={{
                width: '100%',
                padding: '8px',
                background: '#1a1a1a',
                border: '1px solid #00ff00',
                color: '#00ff00',
                borderRadius: '4px'
              }}
            />
          </div>
          
          <button
            onClick={handleTrade}
            disabled={killSwitch.active}
            style={{
              width: '100%',
              padding: '12px',
              background: killSwitch.active ? '#333' : '#00ff00',
              color: killSwitch.active ? '#666' : '#0a0a0a',
              border: 'none',
              borderRadius: '4px',
              cursor: killSwitch.active ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
              fontSize: '16px'
            }}
          >
            {killSwitch.active ? '🔴 KILL SWITCH ACTIVE' : '🚀 EXECUTE TRADE'}
          </button>
        </div>
        
        {/* Portfolio View */}
        <PortfolioView />
        
        {/* Constitution Rules */}
        <ConstitutionPanel compact />
      </div>
    </div>
  );
};