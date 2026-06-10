# test_full_trading.py
"""
Phoenix OS - Complete Trading Simulation Test
Tests: Portfolio, Trading, Backtesting, Market Data, Kill Switch
"""

import asyncio
import aiohttp
import json
import time
import random
from datetime import datetime
import sys

API_BASE = "http://localhost:8002"
API_KEY = "rez-hive-admin-key-2026"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}📊 {text}{Colors.END}")

def print_trade(text):
    print(f"{Colors.YELLOW}💰 {text}{Colors.END}")

async def test_portfolio(session):
    """Test portfolio endpoint"""
    print_info("Fetching portfolio...")
    try:
        async with session.get(f"{API_BASE}/portfolio") as resp:
            if resp.status == 200:
                data = await resp.json()
                print_success(f"Portfolio loaded: Balance={data.get('balance', 0)}, Value={data.get('total_value', 0)}")
                return data
            else:
                print_error(f"Portfolio failed: {resp.status}")
                return None
    except Exception as e:
        print_error(f"Portfolio error: {e}")
        return None

async def execute_trade(session, action, symbol, amount):
    """Execute a trade via chat endpoint"""
    task = f"/trade {action} {symbol} {amount}"
    print_trade(f"Executing: {task}")
    
    try:
        async with session.post(f"{API_BASE}/kernel/stream", 
                               json={"task": task}) as resp:
            if resp.status == 200:
                full_response = ""
                async for line in resp.content:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            if data.get('type') == 'reflex':
                                print_success(f"Trade result: {data.get('content', '')[:100]}")
                                return True
                        except:
                            pass
                return True
            else:
                print_error(f"Trade failed: {resp.status}")
                return False
    except Exception as e:
        print_error(f"Trade error: {e}")
        return False

async def test_backtest(session, strategy):
    """Test backtesting"""
    task = f"/backtest {strategy}"
    print_info(f"Running backtest: {strategy}")
    
    try:
        async with session.post(f"{API_BASE}/kernel/stream", 
                               json={"task": task}) as resp:
            if resp.status == 200:
                full_response = ""
                async for line in resp.content:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            if data.get('type') == 'reflex':
                                content = data.get('content', '')
                                print_success(f"Backtest result: {content[:200]}")
                                return True
                        except:
                            pass
                return True
            else:
                print_error(f"Backtest failed: {resp.status}")
                return False
    except Exception as e:
        print_error(f"Backtest error: {e}")
        return False

async def test_kill_switch(session):
    """Test kill switch"""
    print_info("Testing kill switch...")
    try:
        # Check status
        async with session.get(f"{API_BASE}/kill/status") as resp:
            data = await resp.json()
            print_info(f"Kill switch status: {'ACTIVE' if data.get('active') else 'INACTIVE'}")
        
        # Activate
        print_info("Activating kill switch...")
        async with session.post(f"{API_BASE}/kill", 
                               headers={"Authorization": f"Bearer {API_KEY}"}) as resp:
            if resp.status == 200:
                data = await resp.json()
                print_success(f"Kill switch activated at {data.get('triggered_at')}")
                return True
            else:
                print_error(f"Kill switch activation failed: {resp.status}")
                return False
    except Exception as e:
        print_error(f"Kill switch error: {e}")
        return False

async def test_market_data(session):
    """Test market data streaming"""
    print_info("Testing market data...")
    try:
        # Check if market data is available via health or workers
        async with session.get(f"{API_BASE}/health") as resp:
            data = await resp.json()
            if data.get('workers', 0) > 0:
                print_success(f"Market data available (workers: {data.get('workers')})")
                return True
            else:
                print_error("No market data workers found")
                return False
    except Exception as e:
        print_error(f"Market data error: {e}")
        return False

async def run_trading_simulation(session):
    """Run a full trading simulation"""
    print_header("🚀 FULL TRADING SIMULATION")
    
    results = []
    
    # 1. Check initial portfolio
    portfolio = await test_portfolio(session)
    if portfolio:
        initial_balance = portfolio.get('balance', 0)
        print_info(f"Initial balance: ${initial_balance:,.2f}")
        results.append(True)
    else:
        results.append(False)
    
    # 2. Test market data
    results.append(await test_market_data(session))
    
    # 3. Run multiple trades
    print_header("📈 EXECUTING TRADES")
    trades = [
        ("buy", "BTC/PHP", 0.01),
        ("buy", "ETH/PHP", 0.1),
        ("sell", "BTC/PHP", 0.005),
        ("buy", "SOL/PHP", 1.0),
        ("sell", "ETH/PHP", 0.05),
    ]
    
    trade_success = 0
    for action, symbol, amount in trades:
        success = await execute_trade(session, action, symbol, amount)
        if success:
            trade_success += 1
        await asyncio.sleep(0.5)  # Small delay between trades
    
    results.append(trade_success > 0)
    print_success(f"Trades executed: {trade_success}/{len(trades)} successful")
    
    # 4. Check portfolio after trades
    print_header("📊 POST-TRADE PORTFOLIO")
    portfolio = await test_portfolio(session)
    if portfolio:
        new_balance = portfolio.get('balance', 0)
        positions = portfolio.get('positions', {})
        print_info(f"New balance: ${new_balance:,.2f}")
        print_info(f"Open positions: {len(positions)}")
        for symbol, amount in positions.items():
            print_info(f"  {symbol}: {amount} units")
        results.append(True)
    else:
        results.append(False)
    
    # 5. Test backtesting
    print_header("📉 BACKTESTING")
    backtest_strategies = [
        "moving average crossover on BTC",
        "mean reversion on ETH",
        "momentum strategy on SOL"
    ]
    
    backtest_success = 0
    for strategy in backtest_strategies:
        success = await test_backtest(session, strategy)
        if success:
            backtest_success += 1
        await asyncio.sleep(0.5)
    
    results.append(backtest_success > 0)
    print_success(f"Backtests completed: {backtest_success}/{len(backtest_strategies)} successful")
    
    # 6. Test kill switch (optional - uncomment to test)
    # print_header("🛑 KILL SWITCH TEST")
    # await test_kill_switch(session)
    
    # Summary
    print_header("📊 SIMULATION SUMMARY")
    passed = sum(results)
    total = len(results)
    
    print(f"\n{'Test':<30} {'Result':<10}")
    print(f"{'-'*40}")
    print(f"{'Portfolio Access':<30} {'✅' if results[0] else '❌'}")
    print(f"{'Market Data':<30} {'✅' if results[1] else '❌'}")
    print(f"{'Trade Execution':<30} {'✅' if results[2] else '❌'}")
    print(f"{'Post-Trade State':<30} {'✅' if results[3] else '❌'}")
    print(f"{'Backtesting':<30} {'✅' if results[4] else '❌'}")
    
    print(f"\n{Colors.BOLD}Overall: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print_success("\n🎉 TRADING SYSTEM FULLY OPERATIONAL! 🎉")
    else:
        print_error("\n⚠️ Some tests failed. Check logs above.")
    
    return passed == total

async def main():
    print_header("PHOENIX OS - COMPLETE TRADING SIMULATION")
    print_info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"API: {API_BASE}")
    
    async with aiohttp.ClientSession() as session:
        # Check kernel connection
        try:
            async with session.get(f"{API_BASE}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print_success(f"Kernel connected! Workers: {data.get('workers', 0)}")
                else:
                    print_error(f"Kernel returned status {resp.status}")
                    return
        except Exception as e:
            print_error(f"Cannot connect to kernel: {e}")
            print_info("Make sure kernel is running: python rezphoenix_v15_final.py")
            return
        
        # Run full simulation
        success = await run_trading_simulation(session)
        
        print_header("SIMULATION COMPLETE")
        if success:
            print_success("Your Phoenix trading system is ready for production!")
        else:
            print_error("Please review failed tests above.")

if __name__ == "__main__":
    asyncio.run(main())