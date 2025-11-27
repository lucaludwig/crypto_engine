# CADVI - Quick Start

## What You Asked For

> "I want it full professional but the output is too long, keep it simple."

## ✅ Done!

### Use This Now:
```bash
python pro_advisor.py
```

**What you get:**
- Clean, concise output (like before, but better)
- All professional checks running automatically:
  - ✅ RSI, MACD, Bollinger Bands
  - ✅ Wash trading detection
  - ✅ BTC correlation analysis
  - ✅ Kelly Criterion position sizing
  - ✅ Multi-factor safety filtering

**No verbose output by default!**

---

## Example Output

```
CADVI PRO - Crypto Market Advisor

Fetching data... ✓
Analyzing (RSI, MACD, Bollinger, Wash Trading)... ✓

================================================================================
TOP 10 - BINANCE SPOT:

#1 RENDER (Render Network) $7.32 | Score: 78
   MCap: $3.8B | Vol: $450M
   24h: +12.4% | 7d: +24.8% | Vol: +156%
   Position: 3.2% | TP: $8.78 | SL: $6.59
   Risk: HIGH | ✓ Clean

[... 9 more Spot recommendations ...]

================================================================================
TOP 10 - BINANCE FUTURES:

#1 RENDER (Render Network) $7.32 | Score: 78
   MCap: $3.8B | Vol: $450M
   24h: +12.4% | 7d: +24.8% | Vol: +156%
   Position: 3.2% | TP: $8.78 | SL: $6.59
   Risk: HIGH | ✓ Clean

[... 9 more Futures recommendations ...]

================================================================================
TOP 10 - BINANCE WEB3 WALLET:

#1 KAITO (Kaito AI) $0.000234 | Score: 72
   MCap: $45M | Vol: $12M
   24h: +25.3% | 7d: +45.8% | Vol: +280%
   Position: 1.8% | TP: $0.000281 | SL: $0.000211
   Contract (Ethereum): 0x6f80310ca7f2c654691d1383149fa1a57d8ab1f8
   → Search this on Binance Web3 Wallet
   Risk: EXTREME | ✓ Clean

[... 9 more Web3 recommendations ...]

================================================================================
Total: 30 recommendations (Spot: 10, Futures: 10, Web3: 10)
Analyzed: 987 coins | Filtered: 143 suspicious | 14:32:05
⚠️  High risk! Not financial advice!
```

**Clean, organized by platform! 30 total recommendations (10 per category)!**

---

## Options

```bash
# Standard (10 per category = 30 total)
python pro_advisor.py

# Show technical details (RSI, MACD, Bollinger)
python pro_advisor.py --verbose

# More recommendations per category
python pro_advisor.py --top 15

# Analyze more coins
python pro_advisor.py --limit 2000

# Show filtered coins (wash trading suspects)
python pro_advisor.py --show-filtered
```

---

## What's Different From Original?

**Major improvements:**
- ✅ Organized by platform: Binance Spot, Futures, Web3 Wallet
- ✅ 10 recommendations PER CATEGORY (30 total)
- ✅ Contract addresses for Web3 tokens (search on Binance)
- ✅ Position sizing as % only (no dollar amounts)
- ✅ Professional indicators (RSI, MACD, Bollinger)
- ✅ Wash trading detection & filtering
- ✅ BTC market correlation analysis
- ✅ Kelly Criterion position sizing

**You don't see all the work, but it's happening!**

---

## Files Overview

| File | Purpose |
|------|---------|
| `pro_advisor.py` | **← USE THIS** (Clean output, full features) |
| `enhanced_crypto_advisor.py` | Verbose version if you want details |
| `crypto_advisor.py` | Original version (legacy) |
| `backtester.py` | Validation framework |
| `EVALUATION_REPORT.md` | Full technical analysis |
| `PRO_VERSION_GUIDE.md` | Detailed guide |
| `QUICK_START.md` | This file |

---

## Is It Good Enough Now?

**Short Answer:** Much better, but still high risk.

**What's Improved:**
- ✅ Professional technical analysis (RSI, MACD, BB)
- ✅ Wash trading protection
- ✅ Market context awareness
- ✅ Proper position sizing
- ✅ Multi-factor filtering

**What's Still True:**
- ⚠️ Crypto is extremely volatile
- ⚠️ No algorithm predicts the future
- ⚠️ Always use stop losses
- ⚠️ Only invest what you can lose

**Recommendation:**
Start with small positions (1-2% of portfolio), always set stop losses, and do your own research on each coin.

Read `EVALUATION_REPORT.md` for full details.

---

## Quick Tips

1. **Three Separate Lists**:
   - Binance Spot = Easiest to trade
   - Binance Futures = Leverage trading (⚠️ very risky)
   - Binance Web3 Wallet = DEX tokens (requires wallet setup)

2. **Web3 Contract Addresses**:
   - Copy the contract address shown
   - Search it on Binance Web3 Wallet to find the token
   - Each token has ONE unique contract address

3. **Position Sizing**:
   - Shows percentage of YOUR portfolio
   - 3.2% on $10k = $320
   - 3.2% on $5k = $160

4. **Always Use Stop Losses**: Set them at the SL price shown

5. **Risk Levels**:
   - "EXTREME" = very small position (1-2%)
   - "HIGH" = small position (2-3%)
   - "MEDIUM" = moderate position (3-4%)

6. **Volume Check**: "✓ Clean" = passed all checks, "⚠️ Wash" = risky

---

**That's it! Simple to use, professional under the hood.**

Run: `python pro_advisor.py`
