# Example Output - CADVI Pro

## Standard Mode (Default)

```bash
$ python pro_advisor.py
```

```
================================================================================
CADVI PRO - Crypto Market Advisor
⚠️  Not financial advice | High risk | DYOR | Only invest what you can lose
================================================================================

Fetching data... ✓
Analyzing (RSI, MACD, Bollinger, Wash Trading)... ✓

TOP 10 RECOMMENDATIONS:

#1 RENDER (Render Network) $7.32                        Binance: Spot, Futures
   MCap: $3.8B | Vol: $450M | Score: 78/100
   24h: +12.4% | 7d: +24.8% | Vol Chg: +156%
   Position: 3.2% ($320 on $10k) | TP: $8.78 | SL: $6.59
   Risk: HIGH | ✓ Clean | CMC: coinmarketcap.com/currencies/render-network/

#2 FET (Fetch.AI) $1.45                                  Binance: Spot, Futures
   MCap: $1.2B | Vol: $285M | Score: 76/100
   24h: +18.2% | 7d: +32.1% | Vol Chg: +203%
   Position: 2.8% ($280 on $10k) | TP: $1.74 | SL: $1.31
   Risk: HIGH | ✓ Clean | CMC: coinmarketcap.com/currencies/fetch-ai/

#3 AR (Arweave) $16.80                                   Binance: Spot, Futures
   MCap: $1.1B | Vol: $180M | Score: 74/100
   24h: +9.5% | 7d: +21.3% | Vol Chg: +125%
   Position: 2.5% ($250 on $10k) | TP: $20.16 | SL: $15.12
   Risk: HIGH | ✓ Clean | CMC: coinmarketcap.com/currencies/arweave/

#4 RNDR (Render Token) $0.000234                        Binance: Web3 Wallet
   MCap: $45M | Vol: $12M | Score: 72/100
   24h: +25.3% | 7d: +45.8% | Vol Chg: +280%
   Position: 1.8% ($180 on $10k) | TP: $0.000281 | SL: $0.000211
   Risk: EXTREME | ✓ Clean | CMC: coinmarketcap.com/currencies/render-token/

#5 OCEAN (Ocean Protocol) $0.52                         Binance: Spot
   MCap: $340M | Vol: $95M | Score: 71/100
   24h: +14.2% | 7d: +28.5% | Vol Chg: +165%
   Position: 2.3% ($230 on $10k) | TP: $0.62 | SL: $0.47
   Risk: HIGH | ✓ Clean | CMC: coinmarketcap.com/currencies/ocean-protocol/

#6 GRT (The Graph) $0.28                                Binance: Spot, Futures
   MCap: $2.8B | Vol: $320M | Score: 69/100
   24h: +11.8% | 7d: +18.9% | Vol Chg: +142%
   Position: 3.0% ($300 on $10k) | TP: $0.34 | SL: $0.25
   Risk: MEDIUM | ✓ Clean | CMC: coinmarketcap.com/currencies/the-graph/

#7 INJ (Injective) $22.50                               Binance: Spot, Futures
   MCap: $2.1B | Vol: $420M | Score: 68/100
   24h: +16.4% | 7d: +30.2% | Vol Chg: +188%
   Position: 2.7% ($270 on $10k) | TP: $27.00 | SL: $20.25
   Risk: MEDIUM | ✓ Clean | CMC: coinmarketcap.com/currencies/injective/

#8 PEPE (Pepe) $0.00001234                              Binance: Spot, Futures
   MCap: $5.2B | Vol: $1.8B | Score: 67/100
   24h: +8.5% | 7d: +15.2% | Vol Chg: +95%
   Position: 3.5% ($350 on $10k) | TP: $0.00001481 | SL: $0.00001111
   Risk: MEDIUM | ✓ Clean | CMC: coinmarketcap.com/currencies/pepe/

#9 AGIX (SingularityNET) $0.68                          Binance: Spot
   MCap: $850M | Vol: $145M | Score: 66/100
   24h: +13.1% | 7d: +22.8% | Vol Chg: +158%
   Position: 2.4% ($240 on $10k) | TP: $0.82 | SL: $0.61
   Risk: HIGH | ✓ Clean | CMC: coinmarketcap.com/currencies/singularitynet/

#10 WLD (Worldcoin) $2.34                               Not on Binance
   MCap: $950M | Vol: $180M | Score: 65/100
   24h: +19.8% | 7d: +38.4% | Vol Chg: +220%
   Position: 2.2% ($220 on $10k) | TP: $2.81 | SL: $2.11
   Risk: HIGH | ✓ Clean | CMC: coinmarketcap.com/currencies/worldcoin/

Analyzed: 987 coins | Filtered: 143 suspicious | 14:32:05
⚠️  High risk! Not financial advice!
```

---

## Quick Mode

```bash
$ python pro_advisor.py --quick
```

```
================================================================================
QUICK TRADE SETUP:

#1 RENDER  Entry: $  7.320000 | TP: $  8.784000 | SL: $  6.588000 | Size:  3.2% | Spot, Futures
#2 FET     Entry: $  1.450000 | TP: $  1.740000 | SL: $  1.305000 | Size:  2.8% | Spot, Futures
#3 AR      Entry: $ 16.800000 | TP: $ 20.160000 | SL: $ 15.120000 | Size:  2.5% | Spot, Futures
#4 RNDR    Entry: $  0.000234 | TP: $  0.000281 | SL: $  0.000211 | Size:  1.8% | Web3 Wallet
#5 OCEAN   Entry: $  0.520000 | TP: $  0.624000 | SL: $  0.468000 | Size:  2.3% | Spot
#6 GRT     Entry: $  0.280000 | TP: $  0.336000 | SL: $  0.252000 | Size:  3.0% | Spot, Futures
#7 INJ     Entry: $ 22.500000 | TP: $ 27.000000 | SL: $ 20.250000 | Size:  2.7% | Spot, Futures
#8 PEPE    Entry: $  0.000012 | TP: $  0.000015 | SL: $  0.000011 | Size:  3.5% | Spot, Futures
#9 AGIX    Entry: $  0.680000 | TP: $  0.816000 | SL: $  0.612000 | Size:  2.4% | Spot
#10 WLD    Entry: $  2.340000 | TP: $  2.808000 | SL: $  2.106000 | Size:  2.2% | Not on Binance

================================================================================
```

---

## Verbose Mode (Shows Technical Indicators)

```bash
$ python pro_advisor.py --verbose
```

```
TOP 10 RECOMMENDATIONS:

#1 RENDER (Render Network) $7.32                        Binance: Spot, Futures
   MCap: $3.8B | Vol: $450M | Score: 78/100
   24h: +12.4% | 7d: +24.8% | Vol Chg: +156%
   Tech: RSI 65 | MACD 72 | BB 68 | BTC Corr 75
   Position: 3.2% ($320 on $10k) | TP: $8.78 | SL: $6.59
   Risk: HIGH | ✓ Clean | CMC: coinmarketcap.com/currencies/render-network/

[... and so on ...]
```

---

## Platform Indicators Explained

### **Binance: Spot**
- Available for direct trading on Binance Exchange
- Easy to buy/sell with USDT pairs
- Can set OCO orders (Take Profit + Stop Loss combined)

### **Binance: Futures**
- Available for futures/leverage trading on Binance
- ⚠️ CAUTION: Leverage trading is extremely risky
- Most liquid assets have futures

### **Binance: Spot, Futures**
- Available on both spot and futures
- Usually top coins with high liquidity
- Best for various trading strategies

### **Binance: Web3 Wallet**
- Token requires Binance Web3 Wallet (DEX trading)
- NOT available on Binance Exchange directly
- More complex to trade (needs wallet setup, gas fees)
- Higher risk, less liquidity

### **Not on Binance**
- Not available on Binance at all
- Check CoinMarketCap for other exchanges (Coinbase, KuCoin, etc.)
- May require other platforms or DEX

---

## Tips for Using Output

1. **Check Platform First**: Coins on "Spot, Futures" are easiest to trade
2. **Position Size**: Use the recommended % on your portfolio (shown for $10k)
3. **TP/SL**: Copy these exact values to your exchange orders
4. **Risk Level**: "EXTREME" = smallest positions, "HIGH" = small, "MEDIUM" = moderate
5. **Filtered Count**: Higher filtered count = more suspicious activity in market
6. **Score**: >75 = strong signal, 65-75 = moderate, <65 = weaker

---

## Real-World Example Trade

Let's say you have a **$5,000 portfolio** and #1 recommendation is:

```
#1 RENDER (Render Network) $7.32                        Binance: Spot, Futures
   Position: 3.2% ($320 on $10k) | TP: $8.78 | SL: $6.59
```

**Your Trade:**
1. Platform: Binance Spot (easy!)
2. Position size: 3.2% of $5,000 = **$160**
3. Buy: $160 worth of RENDER at ~$7.32
4. Set Take Profit: $8.78 (+20%)
5. Set Stop Loss: $6.59 (-10%)
6. Use OCO order type on Binance

**Potential Outcomes:**
- ✅ Hits TP: +$32 profit (+20%)
- ❌ Hits SL: -$16 loss (-10%)
- Risk/Reward: 2:1 ratio

---

This is what you'll see when you run the tool!
