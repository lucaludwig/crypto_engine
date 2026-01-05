# CADVI Pro - New Output Format

## What Changed

✅ **10 recommendations for EACH category:**
- 10 Binance Spot
- 10 Binance Futures
- 10 Binance Web3 Wallet

✅ **Removed dollar amounts** from position sizing (just shows %)

✅ **Contract addresses shown for Web3 tokens** (so you can search on Binance)

---

## Example Output

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

================================================================================
TOP 10 - BINANCE SPOT:

#1 RENDER (Render Network) $7.32 | Score: 78
   MCap: $3.8B | Vol: $450M
   24h: +12.4% | 7d: +24.8% | Vol: +156%
   Position: 3.2% | TP: $8.78 | SL: $6.59
   Risk: HIGH | ✓ Clean

#2 FET (Fetch.AI) $1.45 | Score: 76
   MCap: $1.2B | Vol: $285M
   24h: +18.2% | 7d: +32.1% | Vol: +203%
   Position: 2.8% | TP: $1.74 | SL: $1.31
   Risk: HIGH | ✓ Clean

#3 AR (Arweave) $16.80 | Score: 74
   MCap: $1.1B | Vol: $180M
   24h: +9.5% | 7d: +21.3% | Vol: +125%
   Position: 2.5% | TP: $20.16 | SL: $15.12
   Risk: HIGH | ✓ Clean

#4 OCEAN (Ocean Protocol) $0.52 | Score: 71
   MCap: $340M | Vol: $95M
   24h: +14.2% | 7d: +28.5% | Vol: +165%
   Position: 2.3% | TP: $0.62 | SL: $0.47
   Risk: HIGH | ✓ Clean

#5 GRT (The Graph) $0.28 | Score: 69
   MCap: $2.8B | Vol: $320M
   24h: +11.8% | 7d: +18.9% | Vol: +142%
   Position: 3.0% | TP: $0.34 | SL: $0.25
   Risk: MEDIUM | ✓ Clean

#6 AGIX (SingularityNET) $0.68 | Score: 66
   MCap: $850M | Vol: $145M
   24h: +13.1% | 7d: +22.8% | Vol: +158%
   Position: 2.4% | TP: $0.82 | SL: $0.61
   Risk: HIGH | ✓ Clean

#7 MATIC (Polygon) $0.89 | Score: 65
   MCap: $8.3B | Vol: $520M
   24h: +7.2% | 7d: +15.4% | Vol: +88%
   Position: 3.1% | TP: $1.07 | SL: $0.80
   Risk: MEDIUM | ✓ Clean

#8 AVAX (Avalanche) $38.50 | Score: 64
   MCap: $15.2B | Vol: $680M
   24h: +6.8% | 7d: +12.3% | Vol: +75%
   Position: 3.3% | TP: $46.20 | SL: $34.65
   Risk: MEDIUM | ✓ Clean

#9 ATOM (Cosmos) $12.30 | Score: 63
   MCap: $3.6B | Vol: $280M
   24h: +8.9% | 7d: +17.5% | Vol: +110%
   Position: 2.9% | TP: $14.76 | SL: $11.07
   Risk: MEDIUM | ✓ Clean

#10 ALGO (Algorand) $0.34 | Score: 62
   MCap: $2.8B | Vol: $195M
   24h: +10.2% | 7d: +19.8% | Vol: +132%
   Position: 2.7% | TP: $0.41 | SL: $0.31
   Risk: MEDIUM | ✓ Clean

================================================================================
TOP 10 - BINANCE FUTURES:

#1 RENDER (Render Network) $7.32 | Score: 78
   MCap: $3.8B | Vol: $450M
   24h: +12.4% | 7d: +24.8% | Vol: +156%
   Position: 3.2% | TP: $8.78 | SL: $6.59
   Risk: HIGH | ✓ Clean

#2 FET (Fetch.AI) $1.45 | Score: 76
   MCap: $1.2B | Vol: $285M
   24h: +18.2% | 7d: +32.1% | Vol: +203%
   Position: 2.8% | TP: $1.74 | SL: $1.31
   Risk: HIGH | ✓ Clean

#3 INJ (Injective) $22.50 | Score: 68
   MCap: $2.1B | Vol: $420M
   24h: +16.4% | 7d: +30.2% | Vol: +188%
   Position: 2.7% | TP: $27.00 | SL: $20.25
   Risk: MEDIUM | ✓ Clean

#4 PEPE (Pepe) $0.00001234 | Score: 67
   MCap: $5.2B | Vol: $1.8B
   24h: +8.5% | 7d: +15.2% | Vol: +95%
   Position: 3.5% | TP: $0.00001481 | SL: $0.00001111
   Risk: MEDIUM | ✓ Clean

[... 6 more futures recommendations ...]

================================================================================
TOP 10 - BINANCE WEB3 WALLET:

#1 KAITO (Kaito AI) $0.000234 | Score: 72
   MCap: $45M | Vol: $12M
   24h: +25.3% | 7d: +45.8% | Vol: +280%
   Position: 1.8% | TP: $0.000281 | SL: $0.000211
   Contract (Ethereum): 0x6f80310ca7f2c654691d1383149fa1a57d8ab1f8
   → Search this on Binance Web3 Wallet
   Risk: EXTREME | ✓ Clean

#2 BUBBLE (Bubble Map) $0.00156 | Score: 70
   MCap: $38M | Vol: $8.5M
   24h: +32.1% | 7d: +58.3% | Vol: +325%
   Position: 1.5% | TP: $0.00187 | SL: $0.00140
   Contract (BNB Smart Chain): 0x3d4b4bcae23683c26a1e3a7f83dc19c5c23c61f2
   → Search this on Binance Web3 Wallet
   Risk: EXTREME | ✓ Clean

#3 GRIFFAIN (Griffain) $0.00456 | Score: 69
   MCap: $52M | Vol: $15M
   24h: +28.5% | 7d: +52.1% | Vol: +298%
   Position: 1.9% | TP: $0.00547 | SL: $0.00410
   Contract (Ethereum): 0x8f7d64ea817b7e9f7e6d5f4ff3a9f9f5b9c8d3e2
   → Search this on Binance Web3 Wallet
   Risk: EXTREME | ✓ Clean

#4 VISTA (Vista) $0.00892 | Score: 67
   MCap: $61M | Vol: $18M
   24h: +22.8% | 7d: +41.5% | Vol: +265%
   Position: 2.0% | TP: $0.01070 | SL: $0.00803
   Contract (Polygon): 0x5a3e6f7c8d9e1b2f4a8c7d6e5f4a3b2c1d0e9f8a
   → Search this on Binance Web3 Wallet
   Risk: EXTREME | ✓ Clean

[... 6 more Web3 recommendations ...]

================================================================================
Total: 30 recommendations (Spot: 10, Futures: 10, Web3: 10)
Analyzed: 987 coins | Filtered: 143 suspicious | 14:32:05
⚠️  High risk! Not financial advice!
```

---

## Key Features

### 1. Separate Categories
Each category (Spot, Futures, Web3) gets its own section with 10 recommendations.

### 2. Position Sizing
- Shows percentage only (no dollar amount)
- Example: `Position: 3.2%` means invest 3.2% of your portfolio

### 3. Web3 Contract Addresses
For Web3 tokens, you get:
```
Contract (Ethereum): 0x6f80310ca7f2c654691d1383149fa1a57d8ab1f8
→ Search this on Binance Web3 Wallet
```

**How to use:**
1. Open Binance Web3 Wallet
2. Go to "Discover" or "Search"
3. Paste the contract address
4. Find the token and trade

### 4. Clean Output
- No verbose details by default
- Add `--verbose` to see RSI, MACD, Bollinger, BTC correlation scores
- Add `--show-filtered` to see coins filtered by wash trading

---

## Command Options

```bash
# Standard (10 per category)
python pro_advisor.py

# Show more per category
python pro_advisor.py --top 15

# Show technical indicators
python pro_advisor.py --verbose

# Show filtered coins
python pro_advisor.py --show-filtered

# Analyze more coins
python pro_advisor.py --limit 2000
```

---

## Understanding the Categories

### Binance Spot
- **What:** Trade directly on Binance exchange
- **How:** Easy - just buy/sell like normal
- **Liquidity:** Usually high
- **Best for:** Most users

### Binance Futures
- **What:** Leverage trading (⚠️ VERY risky)
- **How:** Available on Binance Futures
- **Liquidity:** Usually highest
- **Best for:** Experienced traders only

### Binance Web3 Wallet
- **What:** DEX tokens, use Binance Web3 Wallet
- **How:** More complex - need wallet, gas fees
- **Liquidity:** Often lower
- **Best for:** Those comfortable with DEX/wallets
- **Important:** Contract address provided for search

---

## Position Sizing Examples

If you have a **$10,000 portfolio**:

- `Position: 3.2%` = Invest $320
- `Position: 2.5%` = Invest $250
- `Position: 1.8%` = Invest $180

If you have a **$5,000 portfolio**:

- `Position: 3.2%` = Invest $160
- `Position: 2.5%` = Invest $125
- `Position: 1.8%` = Invest $90

**Always use the percentage relative to YOUR portfolio size.**

---

## Trading Web3 Tokens

### Step-by-Step:

1. **Find the token**
   ```
   Contract (Ethereum): 0x6f80310ca7f2c654691d1383149fa1a57d8ab1f8
   ```

2. **Open Binance Web3 Wallet** (in Binance app or website)

3. **Search** using the contract address

4. **Connect wallet** and ensure you have:
   - Enough of the base currency (ETH, BNB, etc.)
   - Gas fees for transactions

5. **Trade** via the DEX connected to Binance Wallet

**Note:** Web3 tokens are HIGHER RISK - smaller position sizes recommended!

---

## Tips

1. **Diversify across categories** - Don't put everything in one section
2. **Start with Spot** - Easiest and safest
3. **Be careful with Futures** - Leverage can wipe you out quickly
4. **Web3 requires research** - Make sure you understand the project first
5. **Contract addresses are unique** - Each token has ONE correct address
6. **Double-check addresses** - Wrong address = lost funds!

---

**That's the new format! 30 total recommendations (10 per category) with clear separation and Web3 contract addresses included.**
