#!/usr/bin/env python3
"""Train Learning Engine on Historical Data

This script fetches historical data from Binance and runs a simulation
to pre-train the Learning Engine. This solves the "Cold Start" problem
and provides the bot with immediate pattern recognition capabilities.
"""
import time
from datetime import datetime, timedelta
import random
from colorama import Fore, Style, init
from api.binance_client import load_binance_client
from api.learning_engine import TradingLearningEngine
from api.enhanced_analyzer import EnhancedCryptoAnalyzer

init(autoreset=True)

def train_on_history(days: int = 30, limit_per_coin: int = 50):
    """Fetch historical data and train engine"""
    
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}TIME TRAVEL TRAINING (Historical Simulation){Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    
    # Initialize
    try:
        binance_client = load_binance_client(dry_run=True)
        learning_engine = TradingLearningEngine()
        
        print(f"Connecting to Binance to fetch history ({days} days)...")
        
        # Get top volume coins to train on (diverse dataset)
        tickers = binance_client.client.get_ticker()
        # Filter for USDT pairs with good volume
        candidates = [
            t['symbol'] for t in tickers 
            if t['symbol'].endswith('USDT') 
            and float(t['quoteVolume']) > 10_000_000
            and 'UP' not in t['symbol'] and 'DOWN' not in t['symbol'] # Exclude leverage tokens
        ]
        
        # Pick random sample of 20 coins
        selected_symbols = random.sample(candidates, min(20, len(candidates)))
        print(f"Selected {len(selected_symbols)} coins for training: {', '.join(selected_symbols[:5])}...")
        
        total_simulated_trades = 0
        total_wins = 0
        
        for symbol in selected_symbols:
            print(f"\nProcessing {symbol}...", end=" ", flush=True)
            
            # Fetch Klines (4h candles)
            # interval=4h gives us clear trends/swings
            klines = binance_client.client.get_klines(
                symbol=symbol,
                interval='4h',
                limit=limit_per_coin
            )
            
            # Simulate trades based on simple logic to feed the engine
            # We want to feed it "What happened after X pattern?"
            
            for i in range(len(klines) - 5): # Need future data to know outcome
                current_candle = klines[i]
                future_candle = klines[i+3] # Look 12 hours ahead
                
                # Parse data
                open_price = float(current_candle[1])
                close_price = float(current_candle[4])
                volume = float(current_candle[5])
                high_price = float(current_candle[2])
                low_price = float(current_candle[3])
                
                future_close = float(future_candle[4])
                
                # Calculate metrics similar to EnhancedCryptoAnalyzer
                change_24h = ((close_price - open_price) / open_price) * 100 # Approx candle change
                
                # Mock Coin Data Structure (approximate)
                coin_data = {
                    'symbol': symbol,
                    'price': close_price,
                    'market_cap': 100_000_000, # Dummy
                    'volume_24h': volume * close_price,
                    'change_24h': change_24h,
                    'volume_change_24h': random.uniform(-20, 50), # Simulated
                    'enhanced_score': random.randint(50, 90), # Simulated score
                    'wash_trading_confidence': random.randint(0, 30)
                }
                
                # Simulate a Trade
                pnl = ((future_close - close_price) / close_price) * 100
                is_winner = pnl > 0.5 # Consider >0.5% a win for training
                
                if abs(pnl) > 0.5: # Only learn from significant moves
                    total_simulated_trades += 1
                    if is_winner: total_wins += 1
                    
                    learning_engine.analyze_trade_outcome(
                        symbol=symbol,
                        buy_price=close_price,
                        sell_price=future_close,
                        coin_data=coin_data,
                        exit_type='SIMULATED'
                    )
            
            print(f"{Fore.GREEN}✓{Style.RESET_ALL}", end="")

        print(f"\n\n{Fore.GREEN}{Style.BRIGHT}TRAINING COMPLETE!{Style.RESET_ALL}")
        print(f"Simulated Trades: {total_simulated_trades}")
        print(f"Simulated Win Rate: {total_wins/total_simulated_trades*100:.1f}%")
        print(f"Learnings saved to 'learnings.json'")
        
        # Show immediate insights
        print("\n" + learning_engine.generate_learning_report())
        
    except Exception as e:
        print(f"\n{Fore.RED}Training failed: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    train_on_history()
